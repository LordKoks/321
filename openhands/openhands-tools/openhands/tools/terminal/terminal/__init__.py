import platform

from openhands.tools.terminal.terminal.factory import create_terminal_session
from openhands.tools.terminal.terminal.interface import (
    TerminalInterface,
    TerminalSessionBase,
)
from openhands.tools.terminal.terminal.terminal_session import (
    TerminalCommandStatus,
    TerminalSession,
)
from openhands.tools.terminal.terminal.tmux_terminal import TmuxTerminal

if platform.system() == "Windows":
    from openhands.tools.terminal.terminal.windows_subprocess_terminal import (
        WindowsSubprocessTerminal,
    )
    SubprocessTerminal = WindowsSubprocessTerminal # Alias for compatibility if needed
else:
    from openhands.tools.terminal.terminal.subprocess_terminal import (
        SubprocessTerminal,
    )

__all__ = [
    "TerminalInterface",
    "TerminalSessionBase",
    "TmuxTerminal",
    "SubprocessTerminal",
    "TerminalSession",
    "TerminalCommandStatus",
    "create_terminal_session",
]
