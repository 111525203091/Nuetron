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
from core.config import OWNER_NAME


import threading as _threading

# ─── Background CPU Sampler ───────────────────────────────────────────────────
# psutil.cpu_percent(interval=None) returns 0 on first call and spikes on
# irregular polling. We fix this by sampling continuously on a daemon thread.
_cpu_sample = 0.0
_per_core_samples = []

def _cpu_sampler():
    global _cpu_sample, _per_core_samples
    # Warm-up: first blocking call initialises internal counters
    psutil.cpu_percent(interval=1)
    while True:
        _cpu_sample = psutil.cpu_percent(interval=2)          # blocks 2s, very accurate
        _per_core_samples = psutil.cpu_percent(percpu=True)   # non-blocking after first

_sampler_thread = _threading.Thread(target=_cpu_sampler, daemon=True, name="cpu-sampler")
_sampler_thread.start()


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
        """Return comprehensive system information as formatted string."""
        d = SystemSkills.get_system_metrics()
        return (
            f"OS: {d['os']}\n"
            f"Machine: {d['machine']} | Processor: {d['processor']}\n"
            f"CPU Usage: {d['cpu_percent']}% | Cores: {d['cpu_cores_physical']} physical, {d['cpu_cores_logical']} logical\n"
            f"CPU Frequency: {d['cpu_freq_mhz']} MHz\n"
            f"RAM: {d['ram_used_gb']:.1f} GB used / {d['ram_total_gb']:.1f} GB total ({d['ram_percent']}%)\n"
            f"Disk: {d['disk_used_gb']:.1f} GB used / {d['disk_total_gb']:.1f} GB total ({d['disk_percent']}%)\n"
            f"Hostname: {d['hostname']}"
            + (f"\nBattery: {d['battery_percent']}% ({d['battery_status']})" if d.get('battery_percent') else "")
        )

    @staticmethod
    def get_system_metrics() -> dict:
        """Return live system metrics as a structured dict (used by /api/status)."""
        global _cpu_sample
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu_freq = psutil.cpu_freq()

        metrics = {
            "cpu_percent": round(_cpu_sample, 1),
            "cpu_cores_physical": psutil.cpu_count(logical=False),
            "cpu_cores_logical": psutil.cpu_count(),
            "cpu_freq_mhz": round(cpu_freq.current) if cpu_freq else 0,
            "ram_used_gb": round(mem.used / 1e9, 1),
            "ram_total_gb": round(mem.total / 1e9, 1),
            "ram_percent": mem.percent,
            "disk_used_gb": round(disk.used / 1e9, 1),
            "disk_total_gb": round(disk.total / 1e9, 1),
            "disk_percent": disk.percent,
            "os": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "processor": platform.processor()[:50],
            "hostname": socket.gethostname(),
        }

        # Battery
        try:
            bat = psutil.sensors_battery()
            if bat:
                metrics["battery_percent"] = round(bat.percent, 1)
                metrics["battery_status"] = "Charging" if bat.power_plugged else "Discharging"
        except Exception:
            pass

        return metrics

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
        """Open a named application or terminal on Windows in a visible interactive window."""
        app_map = {
            # Terminals & Shells
            "terminal": 'start "" wt || start "" powershell',
            "windows terminal": 'start "" wt || start "" powershell',
            "powershell": 'start "" powershell',
            "cmd": 'start "" cmd',
            "command prompt": 'start "" cmd',
            "bash": 'start "" bash',

            # File Management
            "file explorer": 'start explorer',
            "explorer": 'start explorer',
            "my computer": 'start explorer',
            "this pc": 'start explorer',

            # Browsers
            "chrome": 'start "" chrome',
            "google chrome": 'start "" chrome',
            "firefox": 'start "" firefox',
            "edge": 'start "" msedge',
            "browser": 'start "" msedge',

            # Productivity
            "notepad": 'start "" notepad',
            "word": 'start "" winword',
            "excel": 'start "" excel',
            "powerpoint": 'start "" powerpnt',
            "outlook": 'start "" outlook',
            "teams": 'start "" teams',

            # System tools
            "calculator": 'start calc',
            "task manager": 'start taskmgr',
            "control panel": 'start control',
            "settings": 'start ms-settings:',
            "windows settings": 'start ms-settings:',
            "camera": 'start microsoft.windows.camera:',

            # Media
            "vlc": 'start "" vlc',
            "spotify": 'start spotify: || start https://open.spotify.com',
            "media player": 'start wmplayer',

            # Dev tools
            "vscode": 'start "" code',
            "vs code": 'start "" code',
            "visual studio code": 'start "" code',
            "pycharm": 'start "" pycharm64',
            "android studio": 'start "" studio64',

            # Communication & Social
            "discord": 'start discord: || start https://discord.com/app',
            "whatsapp": 'start whatsapp: || start https://web.whatsapp.com',
            "telegram": 'start tg: || start https://web.telegram.org',

            # Paint
            "paint": 'start mspaint',
            "paint 3d": 'start mspaint',
        }

        normalized = app_name.lower().strip()
        cmd = app_map.get(normalized, f'start "" {normalized}')

        try:
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return f"Initiated execution of **{app_name}**, {OWNER_NAME}."
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
        """
        Take a screenshot on Windows without relying on PIL/pyautogui
        (which fail on Python 3.15 due to C-extension slot ID incompatibility).
        Uses native Windows GDI+ via PowerShell and saves to both the user's
        Desktop and the web HUD screenshots directory for live preview.
        """
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ultron_screenshot_{ts}.png"

            # Determine Desktop path (supports OneDrive Desktop if present)
            desktop_dir = Path.home() / "OneDrive" / "Desktop"
            if not desktop_dir.is_dir():
                desktop_dir = Path.home() / "Desktop"

            if not save_path:
                target_file = desktop_dir / filename
            else:
                target_file = Path(save_path)

            target_file.parent.mkdir(parents=True, exist_ok=True)
            abs_target = str(target_file.resolve())

            # Static screenshots directory for Web HUD preview
            web_screenshots_dir = Path(__file__).resolve().parent.parent / "web" / "static" / "screenshots"
            web_screenshots_dir.mkdir(parents=True, exist_ok=True)
            web_file = web_screenshots_dir / "latest.png"
            abs_web = str(web_file.resolve())

            # Native PowerShell GDI+ script
            ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $screen.Size, [System.Drawing.CopyPixelOperation]::SourceCopy)
$bitmap.Save('{abs_target}', [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Save('{abs_web}', [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
"""
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )

            if target_file.exists() and target_file.stat().st_size > 0:
                return (
                    f"📸 **Screenshot captured successfully**, {OWNER_NAME}!\n\n"
                    f"• **Saved to:** `{abs_target}`\n"
                    f"• **File size:** {target_file.stat().st_size // 1024} KB\n"
                    f"• **Web Preview:** [/static/screenshots/latest.png](/static/screenshots/latest.png)"
                )
            else:
                # If background service execution limits GDI, provide clear fallback
                err_msg = res.stderr.strip() if res.stderr else "Unknown capture failure"
                return f"Could not capture screen: {err_msg}"

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

    # ─── Terminal / Shell Access ───────────────────────────────────────────────

    # Blocked commands for safety
    _BLOCKED_CMDS = {
        "rm -rf", "del /f /s /q", "format", "mkfs", "dd if=",
        "shutdown /f", ":(){:|:&};:", "reg delete", "bcdedit",
        "diskpart", "cipher /w", "sfc /scannow",
    }

    @classmethod
    def run_terminal_command(cls, command: str, cwd: str = None, timeout: int = 15) -> dict:
        """
        Execute a shell command and return structured output.
        Returns a dict with keys: command, stdout, stderr, returncode, cwd.
        Dangerous commands are blocked.
        """
        cmd_lower = command.lower().strip()
        for blocked in cls._BLOCKED_CMDS:
            if blocked in cmd_lower:
                return {
                    "command": command,
                    "stdout": "",
                    "stderr": f"⛔ BLOCKED: Command contains disallowed pattern: '{blocked}'",
                    "returncode": -1,
                    "cwd": cwd or os.getcwd(),
                }

        # Resolve working directory
        work_dir = cwd or os.path.expanduser("~")
        if not os.path.isdir(work_dir):
            work_dir = os.path.expanduser("~")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            return {
                "command": command,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
                "cwd": work_dir,
            }
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "stdout": "",
                "stderr": f"⏱ Command timed out after {timeout}s",
                "returncode": -1,
                "cwd": work_dir,
            }
        except Exception as e:
            return {
                "command": command,
                "stdout": "",
                "stderr": f"Error: {str(e)}",
                "returncode": -1,
                "cwd": work_dir,
            }

    @staticmethod
    def format_terminal_result(result: dict) -> str:
        """Format a terminal result dict into a readable response string."""
        lines = [f"```\n$ {result['command']}"]
        if result["stdout"]:
            lines.append(result["stdout"])
        if result["stderr"]:
            lines.append(f"[stderr] {result['stderr']}")
        rc = result["returncode"]
        lines.append(f"```\n*Exit code: {rc} | Directory: {result['cwd']}*")
        return "\n".join(lines)
