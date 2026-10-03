"""
JARVIS Skills — System Control & Information
"""

import os
import sys
import platform
import subprocess
import datetime
import shutil
import psutil
import socket
from pathlib import Path
from typing import Optional

from core.logger import log


class SystemSkills:
    """Skills for system awareness and control."""

    # ─── Time & Date ──────────────────────────────────────────────────────────

    @staticmethod
    def get_datetime_info() -> str:
        """Return current date, time, and day."""
        now = datetime.datetime.now()
        return (
            f"Current time: {now.strftime('%I:%M:%S %p')}\n"
            f"Current date: {now.strftime('%A, %B %d, %Y')}\n"
            f"Week number: {now.isocalendar()[1]}\n"
            f"Day of year: {now.timetuple().tm_yday}"
        )

    @staticmethod
    def get_uptime() -> str:
        """Return system uptime."""
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"System uptime: {hours}h {minutes}m {seconds}s (booted at {boot_time.strftime('%I:%M %p')})"

    # ─── System Info ──────────────────────────────────────────────────────────

    @staticmethod
    def get_system_info() -> str:
        """Return comprehensive system information."""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_if_stats()

        # Battery info
        battery_info = ""
        try:
            battery = psutil.sensors_battery()
            if battery:
                status = "Charging" if battery.power_plugged else "Discharging"
                battery_info = f"\nBattery: {battery.percent:.1f}% ({status})"
        except Exception:
            pass

        info = (
            f"OS: {platform.system()} {platform.release()} ({platform.version()})\n"
            f"Machine: {platform.machine()} | Processor: {platform.processor()[:50]}\n"
            f"CPU Usage: {cpu_percent}% | Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical\n"
            f"CPU Frequency: {cpu_freq.current:.0f} MHz\n"
            f"RAM: {mem.used / 1e9:.1f} GB used / {mem.total / 1e9:.1f} GB total ({mem.percent}%)\n"
            f"Disk: {disk.used / 1e9:.1f} GB used / {disk.total / 1e9:.1f} GB total ({disk.percent}%)\n"
            f"Hostname: {socket.gethostname()}"
            f"{battery_info}"
        )
        return info

    @staticmethod
    def get_running_processes(top_n: int = 10) -> str:
        """Return top N processes by CPU usage."""
        procs = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                procs.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        procs.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        lines = [f"{'PID':<8} {'Name':<30} {'CPU%':<8} {'MEM%':<8}"]
        lines.append("-" * 56)
        for p in procs[:top_n]:
            lines.append(
                f"{p['pid']:<8} {(p['name'] or 'unknown')[:29]:<30} "
                f"{p.get('cpu_percent', 0):<8.1f} {p.get('memory_percent', 0):<8.2f}"
            )
        return "\n".join(lines)

    @staticmethod
    def get_network_info() -> str:
        """Return network interface information."""
        lines = []
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            lines.append(f"Local IP: {local_ip}")
        except Exception:
            lines.append("Local IP: Unable to determine")

        try:
            net_io = psutil.net_io_counters()
            lines.append(f"Bytes Sent: {net_io.bytes_sent / 1e6:.1f} MB")
            lines.append(f"Bytes Received: {net_io.bytes_recv / 1e6:.1f} MB")
        except Exception:
            pass

        return "\n".join(lines)

    # ─── App Launcher ─────────────────────────────────────────────────────────

    @staticmethod
    def open_application(app_name: str) -> str:
        """Open a named application on Windows."""
        app_map = {
            # Browsers
            "chrome": "chrome",
            "firefox": "firefox",
            "edge": "msedge",
            "browser": "msedge",

            # Productivity
            "notepad": "notepad",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "outlook": "outlook",
            "teams": "teams",

            # System tools
            "calculator": "calc",
            "task manager": "taskmgr",
            "control panel": "control",
            "file explorer": "explorer",
            "explorer": "explorer",
            "cmd": "cmd",
            "powershell": "powershell",
            "terminal": "wt",

            # Media
            "vlc": "vlc",
            "spotify": "spotify",
            "media player": "wmplayer",

            # Dev tools
            "vscode": "code",
            "vs code": "code",
            "visual studio code": "code",
            "pycharm": "pycharm64",
            "android studio": "studio64",

            # Communication
            "discord": "discord",
            "whatsapp": "whatsapp",
            "telegram": "telegram",

            # Paint
            "paint": "mspaint",
            "paint 3d": "mspaint",
        }

        normalized = app_name.lower().strip()
        cmd = app_map.get(normalized, normalized)

        try:
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return f"Opening {app_name}..."
        except Exception as e:
            return f"Could not open {app_name}: {str(e)}"

    @staticmethod
    def close_application(app_name: str) -> str:
        """Close a running application by name."""
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", f"{app_name}.exe"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return f"Closed {app_name}."
            return f"Could not close {app_name}: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def run_command(command: str) -> str:
        """Execute a shell command and return output."""
        try:
            result = subprocess.run(
                command, shell=True,
                capture_output=True, text=True,
                timeout=30
            )
            output = result.stdout or result.stderr or "(no output)"
            return output[:2000]  # Limit output
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds."
        except Exception as e:
            return f"Command error: {str(e)}"

    # ─── File Operations ──────────────────────────────────────────────────────

    @staticmethod
    def list_directory(path: str = ".") -> str:
        """List contents of a directory."""
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return f"Directory not found: {path}"
            
            items = list(p.iterdir())
            dirs = sorted([i for i in items if i.is_dir()], key=lambda x: x.name)
            files = sorted([i for i in items if i.is_file()], key=lambda x: x.name)
            
            lines = [f"Contents of {p.resolve()}:", ""]
            for d in dirs:
                lines.append(f"📁 {d.name}/")
            for f in files:
                size = f.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB" if size < 1024**2 else f"{size/1024**2:.1f} MB"
                lines.append(f"📄 {f.name} ({size_str})")
            
            return "\n".join(lines)
        except PermissionError:
            return f"Permission denied: {path}"
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    @staticmethod
    def read_file(path: str) -> str:
        """Read and return file contents (up to 5000 chars)."""
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return f"File not found: {path}"
            if p.stat().st_size > 1_000_000:
                return "File too large to read (> 1 MB)."
            content = p.read_text(encoding="utf-8", errors="replace")
            if len(content) > 5000:
                return content[:5000] + "\n...[truncated]..."
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @staticmethod
    def search_files(query: str, directory: str = ".", extension: str = "*") -> str:
        """Search for files matching a pattern."""
        try:
            p = Path(directory).expanduser()
            pattern = f"**/*{query}*" if "*" not in query else f"**/{query}"
            matches = list(p.glob(pattern))[:20]
            if not matches:
                return f"No files found matching '{query}' in {directory}"
            return "\n".join(str(m) for m in matches)
        except Exception as e:
            return f"Search error: {str(e)}"

    # ─── Clipboard ────────────────────────────────────────────────────────────

    @staticmethod
    def get_clipboard() -> str:
        """Return current clipboard contents."""
        try:
            import pyperclip
            content = pyperclip.paste()
            return f"Clipboard contents:\n{content}" if content else "Clipboard is empty."
        except Exception as e:
            return f"Clipboard error: {str(e)}"

    @staticmethod
    def set_clipboard(text: str) -> str:
        """Set clipboard content."""
        try:
            import pyperclip
            pyperclip.copy(text)
            return "Text copied to clipboard."
        except Exception as e:
            return f"Clipboard error: {str(e)}"

    # ─── Screenshots ──────────────────────────────────────────────────────────

    @staticmethod
    def take_screenshot(save_path: Optional[str] = None) -> str:
        """Take a screenshot and optionally save it."""
        try:
            import pyautogui
            from PIL import Image
            
            screenshot = pyautogui.screenshot()
            
            if not save_path:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = str(Path.home() / "Desktop" / f"jarvis_screenshot_{ts}.png")
            
            screenshot.save(save_path)
            return f"Screenshot saved to: {save_path}"
        except Exception as e:
            return f"Screenshot error: {str(e)}"

    # ─── Volume Control ───────────────────────────────────────────────────────

    @staticmethod
    def set_volume(level: int) -> str:
        """Set system volume (0-100) on Windows."""
        try:
            level = max(0, min(100, level))
            # Uses PowerShell to set volume
            script = f"""
$wshShell = new-object -com wscript.shell;
for($i=0;$i -lt 50;$i++){{$wshShell.SendKeys([char]174)}};
$steps = [math]::Round({level}/2);
for($i=0;$i -lt $steps;$i++){{$wshShell.SendKeys([char]175)}};
"""
            subprocess.run(["powershell", "-Command", script], capture_output=True)
            return f"Volume set to approximately {level}%"
        except Exception as e:
            return f"Volume control error: {str(e)}"

    # ─── Shutdown / Restart ───────────────────────────────────────────────────

    @staticmethod
    def shutdown(delay: int = 60) -> str:
        """Schedule system shutdown."""
        subprocess.run(["shutdown", "/s", "/t", str(delay)], capture_output=True)
        return f"System will shut down in {delay} seconds."

    @staticmethod
    def restart(delay: int = 60) -> str:
        """Schedule system restart."""
        subprocess.run(["shutdown", "/r", "/t", str(delay)], capture_output=True)
        return f"System will restart in {delay} seconds."

    @staticmethod
    def cancel_shutdown() -> str:
        """Cancel a pending shutdown."""
        subprocess.run(["shutdown", "/a"], capture_output=True)
        return "Shutdown cancelled."

    # ─── Lock Screen ─────────────────────────────────────────────────────────

    @staticmethod
    def lock_screen() -> str:
        """Lock the Windows screen."""
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "Workstation locked."
        except Exception as e:
            return f"Lock error: {str(e)}"
