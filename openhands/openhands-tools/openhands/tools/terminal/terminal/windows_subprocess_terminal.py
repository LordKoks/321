"""Windows-compatible terminal backend implementation."""

import os
import re
import shutil
import subprocess
import threading
import time
from collections import deque
from typing import IO

from openhands.sdk.logger import get_logger
from openhands.sdk.utils import sanitized_env
from openhands.tools.terminal.constants import (
    CMD_OUTPUT_PS1_BEGIN,
    CMD_OUTPUT_PS1_END,
    HISTORY_LIMIT,
)
from openhands.tools.terminal.metadata import CmdOutputMetadata
from openhands.tools.terminal.terminal.interface import TerminalInterface


logger = get_logger(__name__)

ENTER = "\n"


class WindowsSubprocessTerminal(TerminalInterface):
    """Windows-compatible terminal backend using subprocess pipes."""

    PS1: str
    process: subprocess.Popen | None
    output_buffer: deque[str]
    output_lock: threading.Lock
    stdout_thread: threading.Thread | None
    stderr_thread: threading.Thread | None
    _current_command_running: bool

    def __init__(
        self,
        work_dir: str,
        username: str | None = None,
        shell_path: str | None = None,
    ):
        super().__init__(work_dir, username)
        self.PS1 = CmdOutputMetadata.to_ps1_prompt()
        self.process = None
        self.output_buffer = deque(maxlen=HISTORY_LIMIT + 50)
        self.output_lock = threading.Lock()
        self.stdout_thread = None
        self.stderr_thread = None
        self._current_command_running = False
        self.shell_path = shell_path

    def initialize(self) -> None:
        """Initialize the terminal session."""
        if self._initialized:
            return

        # Resolve shell path
        resolved_shell_path = self.shell_path
        if not resolved_shell_path:
            # Try to find bash (git bash)
            resolved_shell_path = shutil.which("bash")
            if not resolved_shell_path:
                # Try common git bash locations
                possible_paths = [
                    r"C:\Program Files\Git\bin\bash.exe",
                    r"C:\Program Files\Git\usr\bin\bash.exe",
                    r"C:\Program Files (x86)\Git\bin\bash.exe",
                ]
                for p in possible_paths:
                    if os.path.exists(p):
                        resolved_shell_path = p
                        break
        
        if not resolved_shell_path:
            # Fallback to powershell if bash is absolutely not found
            resolved_shell_path = shutil.which("powershell")
            if not resolved_shell_path:
                 raise RuntimeError("Could not find bash or powershell in PATH.")

        self.shell_path = resolved_shell_path
        logger.info(f"Using shell: {resolved_shell_path}")

        # Environment
        env = sanitized_env()
        env["PS1"] = self.PS1
        env["TERM"] = "xterm-256color"
        env["PYTHONIOENCODING"] = "utf-8"

        # Command to start shell
        # We need -i for interactive mode to get prompts
        cmd = [resolved_shell_path]
        if "bash" in resolved_shell_path.lower():
            cmd.extend(["--noediting", "-i"])

        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.work_dir,
                env=env,
                text=True,
                bufsize=0, # Unbuffered
                encoding='utf-8',
                errors='replace'
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start shell {resolved_shell_path}: {e}")

        # Start reader threads
        self.stdout_thread = threading.Thread(
            target=self._read_stream, args=(self.process.stdout,), daemon=True
        )
        self.stdout_thread.start()

        self.stderr_thread = threading.Thread(
            target=self._read_stream, args=(self.process.stderr,), daemon=True
        )
        self.stderr_thread.start()

        self._initialized = True

        # Configure shell if it's bash
        if "bash" in resolved_shell_path.lower():
            init_cmd = (
                f'export PROMPT_COMMAND=\'export PS1="{self.PS1}"\'; export PS2=""'
            )
            self._write_input(init_cmd + ENTER)
            time.sleep(1.0)
            self.clear_screen()
        else:
            # PowerShell prompt setup
            # This is a basic attempt to make it compatible
            ps_prompt = f'function prompt {{ "{self.PS1}" }}'
            self._write_input(ps_prompt + ENTER)
            time.sleep(1.0)
            self.clear_screen()

        logger.debug("Windows terminal initialized with work dir: %s", self.work_dir)

    def close(self) -> None:
        """Clean up."""
        if self._closed:
            return

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                pass
            self.process = None

        self._closed = True

    def _write_input(self, data: str) -> None:
        if not self.process or not self.process.stdin:
            return
        try:
            self.process.stdin.write(data)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"Failed to write to terminal: {e}")

    def _read_stream(self, stream: IO[str]) -> None:
        """Read from a stream continuously."""
        try:
            while True:
                if not self.process or self.process.poll() is not None:
                    break
                
                # Read char by char
                chunk = stream.read(1)
                if not chunk:
                    break
                
                with self.output_lock:
                     self._add_text_to_buffer(chunk)
        except Exception as e:
            logger.debug(f"Error reading stream: {e}")

    def _add_text_to_buffer(self, text: str) -> None:
        """Add text to buffer, handling line splitting."""
        if not self.output_buffer:
            self.output_buffer.append("")
            
        # Append text to the last buffer item
        current = self.output_buffer.pop()
        combined = current + text
        
        # Split lines, keeping delimiters
        # We want to mimic behavior where each item in deque is a line (or partial line)
        parts = combined.split("\n")
        
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                # This is a complete line
                self.output_buffer.append(part + "\n")
            else:
                # This is the last part, might be partial
                if part or len(parts) > 1:
                    self.output_buffer.append(part)

    def send_keys(self, text: str, enter: bool = True) -> None:
        if not self._initialized:
            raise RuntimeError("Terminal is not initialized")

        # Handle special keys roughly
        if text.upper() == "C-C":
            # Can't easily send SIGINT to pipe.
            return

        payload = text
        if enter:
            payload += ENTER
        
        self._write_input(payload)
        self._current_command_running = True

    def read_screen(self) -> str:
        if not self._initialized:
            raise RuntimeError("Terminal is not initialized")
        
        time.sleep(0.01)
        with self.output_lock:
            return "".join(self.output_buffer)

    def clear_screen(self) -> None:
        with self.output_lock:
            self.output_buffer.clear()

    def interrupt(self) -> bool:
        # Not easily supported with pipes on Windows without killing the shell
        return False

    def is_running(self) -> bool:
        if not self.process:
            return False
        if self.process.poll() is not None:
            return False
        
        # Check for prompt
        try:
            content = self.read_screen()
            # If screen ends with prompt, no command is running
            return not content.rstrip().endswith(CMD_OUTPUT_PS1_END.rstrip())
        except Exception:
            return True
