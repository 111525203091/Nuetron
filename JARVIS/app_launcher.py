"""
ULTRON Desktop Application Launcher
Launches ULTRON in a native, standalone, borderless window with zero browser chrome.
"""

import os
import sys
import time
import shutil
import threading
import subprocess
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
URL = "http://127.0.0.1:5000"
WINDOW_SIZE = "1320,840"
PROFILE_DIR = Path(os.environ.get("LOCALAPPDATA", str(BASE_DIR))) / "UltronDesktopProfile"


def is_server_running(url: str = URL, timeout: float = 1.0) -> bool:
    """Check if the ULTRON server is already active."""
    try:
        with urllib.request.urlopen(f"{url}/api/status", timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def start_server_in_background():
    """Start the ULTRON core server in a background daemon thread."""
    from core.brain import JarvisBrain
    from core.voice import VoiceEngine
    from core.dispatcher import Dispatcher
    from core.web_server import init_web, run_web

    brain = JarvisBrain()
    voice = VoiceEngine()
    dispatcher = Dispatcher(brain, voice)
    init_web(brain, dispatcher, voice)
    run_web(debug=False)


def find_browser_executable() -> str:
    """Find Microsoft Edge or Google Chrome for standalone app mode."""
    candidates = [
        # Edge candidates
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        # Chrome candidates
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return ""


def main():
    print("Initializing ULTRON Desktop Application...")

    # 1. Start server if not running
    if not is_server_running():
        server_thread = threading.Thread(target=start_server_in_background, daemon=True)
        server_thread.start()

        # Wait for server to be responsive
        max_wait = 15
        started = False
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if is_server_running(timeout=0.5):
                started = True
                break
            time.sleep(0.3)

        if not started:
            print("Warning: Server initialization took longer than expected. Attempting to launch UI anyway.")
    else:
        print("Connected to active ULTRON backend server.")

    # 2. Launch in native standalone Application Mode
    browser = find_browser_executable()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    if browser:
        args = [
            browser,
            f"--app={URL}",
            f"--window-size={WINDOW_SIZE}",
            f"--user-data-dir={PROFILE_DIR}",
            "--disable-features=Translate",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-name=ULTRON",
        ]
        print(f"Launching ULTRON Standalone App Window via {os.path.basename(browser)}...")
        proc = subprocess.Popen(args)
        proc.wait()
    else:
        # Fallback to default browser
        import webbrowser
        print("Launching in default web environment...")
        webbrowser.open(URL)


if __name__ == "__main__":
    main()
