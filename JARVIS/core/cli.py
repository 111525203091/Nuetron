"""
JARVIS CLI Interface — Terminal-based interactive mode
"""

import sys
import threading
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.spinner import Spinner
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from core.config import OWNER_NAME, JARVIS_NAME, WAKE_WORD
from core.brain import JarvisBrain
from core.voice import VoiceEngine
from core.intent_parser import IntentParser
from core.dispatcher import Dispatcher
from core.logger import log


BANNER = r"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
     Just A Rather Very Intelligent System
"""

HELP_TEXT = """
┌─ JARVIS Commands ──────────────────────────────────────┐
│  /voice      — Toggle voice mode (mic input)           │
│  /speak      — Toggle voice output (text-to-speech)    │
│  /web        — Open the web interface in browser       │
│  /history    — Show conversation history               │
│  /tasks      — List all tasks and reminders            │
│  /sysinfo    — System status report                    │
│  /reset      — Clear conversation context              │
│  /help       — Show this help                          │
│  /exit       — Exit JARVIS                             │
│                                                        │
│  Or just type naturally — JARVIS understands you!      │
└────────────────────────────────────────────────────────┘
"""


class CLIInterface:
    """Terminal interface for JARVIS with optional voice integration."""

    def __init__(self, brain: JarvisBrain, voice: Optional[VoiceEngine] = None):
        self.brain = brain
        self.voice = voice
        self.dispatcher = Dispatcher(brain, on_reminder=self._on_reminder)
        self.voice_input_enabled = False
        self.voice_output_enabled = voice is not None and voice.tts_available

        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    def _print(self, text: str, style: str = ""):
        if self.console:
            self.console.print(text, style=style)
        else:
            print(text)

    def _print_banner(self):
        if self.console:
            self.console.print(BANNER, style="bold cyan")
            self.console.print(
                f"  Initializing systems... Ready, {OWNER_NAME}.\n",
                style="bold green"
            )
        else:
            print(BANNER)
            print(f"  Ready, {OWNER_NAME}.\n")

    def _print_jarvis(self, text: str):
        """Print JARVIS response with formatting."""
        if self.console:
            panel = Panel(
                Markdown(text),
                title=f"[bold cyan]{JARVIS_NAME}[/bold cyan]",
                border_style="cyan",
                padding=(0, 1)
            )
            self.console.print(panel)
        else:
            print(f"\n[JARVIS]: {text}\n")

    def _speak(self, text: str):
        """Speak text if voice output is enabled."""
        if self.voice_output_enabled and self.voice:
            self.voice.speak(text)

    def _on_reminder(self, message: str, remind_at):
        """Called when a reminder fires."""
        alert = f"⏰ REMINDER: {message}"
        self._print(f"\n{alert}", style="bold yellow")
        self._speak(f"Reminder, {OWNER_NAME}: {message}")

    def _get_input(self) -> Optional[str]:
        """Get user input (text or voice)."""
        if self.voice_input_enabled and self.voice and self.voice.mic_available:
            self._print("🎤 Listening...", style="dim")
            text = self.voice.listen()
            if text:
                self._print(f"[You]: {text}", style="green")
                return text
            return None
        else:
            if self.console:
                return Prompt.ask(f"[bold green]You[/bold green]")
            else:
                try:
                    return input(f"\n{OWNER_NAME}> ").strip()
                except (EOFError, KeyboardInterrupt):
                    return "/exit"

    def _handle_command(self, text: str) -> bool:
        """
        Handle CLI slash commands.
        Returns True if handled (don't pass to dispatcher).
        """
        cmd = text.strip().lower()

        if cmd == "/exit" or cmd == "/quit":
            self._print_jarvis(f"Goodbye, {OWNER_NAME}. All systems standing by.")
            self._speak(f"Goodbye, {OWNER_NAME}.")
            return True

        elif cmd == "/help":
            self._print(HELP_TEXT, style="dim")
            return True

        elif cmd == "/voice":
            if not self.voice or not self.voice.mic_available:
                self._print("⚠ Microphone not available.", style="yellow")
            else:
                self.voice_input_enabled = not self.voice_input_enabled
                status = "ON" if self.voice_input_enabled else "OFF"
                self._print(f"🎤 Voice input: {status}", style="cyan")
            return True

        elif cmd == "/speak":
            self.voice_output_enabled = not self.voice_output_enabled
            status = "ON" if self.voice_output_enabled else "OFF"
            self._print(f"🔊 Voice output: {status}", style="cyan")
            return True

        elif cmd == "/history":
            history = self.brain.get_history()
            if not history:
                self._print("No conversation history yet.", style="dim")
            else:
                for msg in history[-20:]:
                    role_style = "cyan" if msg["role"] == "jarvis" else "green"
                    self._print(
                        f"[{msg['role'].upper()}]: {msg['content'][:200]}",
                        style=role_style
                    )
            return True

        elif cmd == "/tasks":
            result = self.dispatcher.tasks.list_tasks()
            self._print(result)
            return True

        elif cmd == "/sysinfo":
            from skills.system_skills import SystemSkills
            info = SystemSkills.get_system_info()
            self._print(info)
            return True

        elif cmd == "/reset":
            self.brain.reset_conversation()
            self._print(f"Conversation reset, {OWNER_NAME}.", style="cyan")
            return True

        elif cmd == "/web":
            import webbrowser
            from core.config import WEB_HOST, WEB_PORT
            url = f"http://{WEB_HOST}:{WEB_PORT}"
            webbrowser.open(url)
            self._print(f"Opening web interface: {url}", style="cyan")
            return True

        return False

    def run(self):
        """Start the CLI interface main loop."""
        self._print_banner()
        self._print(HELP_TEXT, style="dim")

        # Greet on startup
        greeting = self.brain.think(
            "I just started up. Greet the user briefly and mention you're ready."
        )
        self._print_jarvis(greeting)
        self._speak(greeting)

        while True:
            try:
                user_input = self._get_input()

                if not user_input or not user_input.strip():
                    continue

                text = user_input.strip()

                # Handle slash commands
                if text.startswith("/"):
                    if self._handle_command(text):
                        if text.lower() in ["/exit", "/quit"]:
                            break
                        continue

                # Show thinking spinner
                if self.console:
                    with self.console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                        intent = IntentParser.parse(text)
                        response = self.dispatcher.dispatch(intent)
                else:
                    intent = IntentParser.parse(text)
                    response = self.dispatcher.dispatch(intent)

                self._print_jarvis(response)
                self._speak(response)

                # Check for exit action
                if intent.action == "exit":
                    break

            except KeyboardInterrupt:
                self._print("\n\n[Interrupted]", style="yellow")
                farewell = f"Standing by, {OWNER_NAME}."
                self._print_jarvis(farewell)
                self._speak(farewell)
                break
            except Exception as e:
                log.error("CLI error: %s", str(e))
                self._print(f"⚠ Error: {str(e)}", style="red")
