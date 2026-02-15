import os
import subprocess
import sys
import webbrowser
import time
from pathlib import Path
import site

def install_dependencies(libs_dir):
    python_executable = sys.executable
    
    print(f"📦 Installing dependencies to {libs_dir}...")
    
    # Dependencies list
    dependencies = [
        "fastapi", "uvicorn", "pydantic", "tenacity", "litellm", 
        "docker", "sqlalchemy", "alembic", "websockets", "wsproto",
        "starlette", "python-multipart", "jinja2", "aiofiles", "termcolor",
        "httpx", "click", "rich", "toml", "psutil", "python-json-logger",
        "Authlib", "deprecation", "fastmcp", "filelock", "python-frontmatter",
        "lmnr", "bashlex", "binaryornot", "cachetools", "libtmux", "browser-use",
        "func-timeout", "tom-swe", "playwright"
    ]
    
    try:
        # Install to target directory
        subprocess.check_call(
            [python_executable, "-m", "pip", "install", "--target", str(libs_dir)] + dependencies
        )
        print("✅ Dependencies installed.")
        
        # Create marker file
        (libs_dir / ".installed").touch()
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to install dependencies: {e}")
        # Clean up partial install if possible?
        raise

def install_playwright(libs_dir):
    python_executable = sys.executable
    print("🎭 Installing Playwright browsers...")
    try:
        # We need to set PYTHONPATH so it finds playwright
        env = os.environ.copy()
        env["PYTHONPATH"] = str(libs_dir) + os.pathsep + env.get("PYTHONPATH", "")
        subprocess.check_call([python_executable, "-m", "playwright", "install", "chromium"], env=env)
        print("✅ Playwright browsers installed.")
    except Exception as e:
        print(f"⚠️ Failed to install Playwright browsers (might be already installed): {e}")

def main():
    print("🚀 Starting Unified AI Agent Application...")
    print(f"🐍 Using System Python: {sys.version}")
    
    # Paths
    root_dir = Path(__file__).parent.absolute()
    openhands_root = root_dir / "openhands"
    libs_dir = openhands_root / ".libs"
    
    # Check if we need to install/update dependencies
    # Check for marker file
    marker_file = libs_dir / ".installed"
    
    if not libs_dir.exists() or not marker_file.exists():
        libs_dir.mkdir(parents=True, exist_ok=True)
        try:
            install_dependencies(libs_dir)
            install_playwright(libs_dir)
        except Exception as e:
            print(f"❌ Critical error installing dependencies: {e}")
            print("Try deleting the 'openhands/.libs' directory and running again.")
            return

    # Define package paths
    package_paths = [
        root_dir / "metagpt",
        openhands_root / "openhands-agent-server",
        openhands_root / "openhands-sdk",
        openhands_root / "openhands-tools",
        openhands_root / "openhands-workspace",
        libs_dir # Add our local libs
    ]
    
    # Static files
    ui_dir = openhands_root / "scripts" / "agent_server_ui"
    static_files_path = ui_dir / "static"
    
    # Environment variables
    env = os.environ.copy()
    
    # Construct PYTHONPATH
    current_pythonpath = env.get("PYTHONPATH", "")
    new_paths = [str(p) for p in package_paths]
    if current_pythonpath:
        new_paths.append(current_pythonpath)
    
    env["PYTHONPATH"] = os.pathsep.join(new_paths)
    env["OH_STATIC_FILES_PATH"] = str(static_files_path)

    # Handle pywin32 paths
    # pywin32 installs .pth file which adds specific subdirectories to path.
    # Since we are setting PYTHONPATH manually, we need to add these explicitly.
    pywin32_paths = [
        libs_dir / "win32",
        libs_dir / "win32" / "lib",
        libs_dir / "Pythonwin",
        libs_dir / "pywin32_system32", # For DLLs if python doesn't find them
    ]
    
    # Append pywin32 paths to PYTHONPATH
    current_pythonpath_list = env["PYTHONPATH"].split(os.pathsep)
    for p in pywin32_paths:
        if p.exists():
            current_pythonpath_list.append(str(p))
            
    env["PYTHONPATH"] = os.pathsep.join(current_pythonpath_list)
    
    # Also add pywin32_system32 to PATH to find DLLs
    pywin32_sys32 = libs_dir / "pywin32_system32"
    if pywin32_sys32.exists():
        env["PATH"] = str(pywin32_sys32) + os.pathsep + env.get("PATH", "")
    
    # Command to run openhands-agent-server using SYSTEM python
    cmd = [sys.executable, "-m", "openhands.agent_server", "--host", "0.0.0.0", "--port", "8000"]
    
    print(f"📂 Serving UI from: {static_files_path}")
    print("🔧 Starting OpenHands Agent Server on http://localhost:8000")
    print("📱 Mobile App: APK is located at 'mobile-app/android/app/build/outputs/apk/debug/app-debug.apk'")
    print("🧩 VS Code Extension: 'vscode-acp/vscode-acp-1.3.0.vsix'")
    
    try:
        process = subprocess.Popen(cmd, env=env, cwd=openhands_root)
        
        # Wait for server to start
        time.sleep(5)
        
        print("\n✅ Server process started!")
        print("🌍 Web UI: http://localhost:8000")
        
        webbrowser.open("http://localhost:8000")
        
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        process.terminate()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    main()
