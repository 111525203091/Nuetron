"""
JARVIS Intent Parser — Parses user commands into structured intents
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Intent:
    action: str           # e.g. "open_app", "search_web", "get_weather", "chat"
    target: str = ""      # e.g. "chrome", "python tutorials"
    params: dict = field(default_factory=dict)
    raw: str = ""         # original input


class IntentParser:
    """
    Rule-based intent parser for fast, skill-routing decisions.
    Falls back to JARVIS Brain (Gemini) for anything it doesn't recognize.
    """

    # ─── Command Patterns ─────────────────────────────────────────────────────

    PATTERNS = [
        # Time / Date
        (r"\b(what(?:'s| is) the time|current time|tell me the time)\b", "get_time", {}),
        (r"\b(what(?:'s| is) (today'?s? )?(date|day))\b", "get_date", {}),
        (r"\b(what time is it)\b", "get_time", {}),

        # System info
        (r"\b(system (info|status|specs|information))\b", "get_system_info", {}),
        (r"\b(cpu|memory|ram) (usage|status|info)\b", "get_system_info", {}),
        (r"\b(battery (level|status|info))\b", "get_system_info", {}),
        (r"\b(how much (ram|memory|disk|storage))\b", "get_system_info", {}),
        (r"\b(uptime)\b", "get_uptime", {}),
        (r"\b(running processes|top processes)\b", "get_processes", {}),
        (r"\b(network (info|status|details))\b", "get_network_info", {}),
        (r"\b(public ip|my ip|ip address)\b", "get_public_ip", {}),
        (r"\b(internet (status|connection|online))\b", "check_internet", {}),

        # App control
        (r"\b(open|launch|start|run) (.+)", "open_app", {"group": 2}),
        (r"\b(close|kill|exit|quit) (.+)", "close_app", {"group": 2}),

        # Search
        (r"\b(search|google|look up|find|search for) (.+)", "search_web", {"group": 2}),
        (r"\b(open (https?://\S+|www\.\S+))\b", "open_url", {"group": 2}),

        # Wikipedia
        (r"\b(wikipedia|wiki) (.+)", "wikipedia", {"group": 2}),
        (r"\bwho is (.+)", "wikipedia", {"group": 1}),
        (r"\bwhat is (.+)", "wikipedia", {"group": 1}),

        # Weather
        (r"\b(?:weather|temperature|forecast)\b.*?\bin (.+)", "get_weather", {"group": 1}),
        (r"\b(?:weather|temperature|forecast)\b", "get_weather", {}),

        # News
        (r"\b(news|headlines|latest news)\b.*\babout (.+)", "get_news", {"group": 2}),
        (r"\b(news|headlines|latest news)\b", "get_news", {}),

        # Tasks / Reminders
        (r"\b(remind me to|set a reminder to) (.+?) (in|at) (.+)", "add_reminder", {"msg_group": 2, "time_group": 3}),
        (r"\b(add task|create task|add a task) (.+)", "add_task", {"group": 2}),
        (r"\b(list tasks|show tasks|my tasks|what are my tasks)\b", "list_tasks", {}),
        (r"\b(complete|done|finish) task (.+)", "complete_task", {"group": 2}),

        # File operations
        (r"\b(list|show|ls) (files|directory|folder)(?: in (.+))?", "list_directory", {"group": 3}),
        (r"\b(read|open|show) file (.+)", "read_file", {"group": 2}),
        (r"\bsearch files? (?:for )?(.+)", "search_files", {"group": 1}),

        # Clipboard
        (r"\b(clipboard|paste|what('s| is) in (the )?clipboard)\b", "get_clipboard", {}),
        (r"\bcopy (.+) to clipboard\b", "set_clipboard", {"group": 1}),

        # Screenshot
        (r"\b(take|capture) (a )?screenshot\b", "take_screenshot", {}),

        # Volume
        (r"\bset volume to (\d+)\b", "set_volume", {"group": 1}),
        (r"\b(mute|unmute)\b", "set_volume", {"mute": True}),

        # Power
        (r"\b(shutdown|shut down|power off)\b", "shutdown", {}),
        (r"\b(restart|reboot)\b", "restart", {}),
        (r"\bcancel (shutdown|restart)\b", "cancel_shutdown", {}),
        (r"\block (screen|workstation|computer|pc)\b", "lock_screen", {}),

        # Memory
        (r"\bremember that (.+)", "remember", {"group": 1}),
        (r"\bwhat do you (know|remember) about me\b", "get_memory", {}),

        # Conversation reset
        (r"\b(reset|clear|start over|new conversation)\b", "reset_conversation", {}),

        # Jokes / fun
        (r"\btell me a joke\b", "tell_joke", {}),
        (r"\bflip a coin\b", "flip_coin", {}),
        (r"\broll (a )?dice?\b", "roll_dice", {}),

        # Greetings
        (r"\b(hello|hi|hey|good morning|good afternoon|good evening|greetings)\b", "greeting", {}),

        # Exit
        (r"\b(goodbye|bye|exit|quit|shutdown (?:jarvis|ultron))\b", "exit", {}),
    ]

    @classmethod
    def parse(cls, text: str) -> Intent:
        """
        Parse user input into an Intent.
        Returns an Intent with action='chat' if no pattern matches.
        """
        text_lower = text.lower().strip()

        for pattern, action, config in cls.PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                params = {}

                # Extract group captures
                if "group" in config:
                    try:
                        params["target"] = match.group(config["group"]).strip()
                    except IndexError:
                        pass

                # Special: reminder has two groups
                if "msg_group" in config and "time_group" in config:
                    try:
                        params["message"] = match.group(config["msg_group"]).strip()
                        time_start = match.start(config["time_group"])
                        params["when"] = text_lower[time_start:].strip()
                    except IndexError:
                        pass

                if "mute" in config:
                    params["mute"] = config["mute"]

                target = params.pop("target", "")
                return Intent(
                    action=action,
                    target=target,
                    params=params,
                    raw=text
                )

        # No pattern matched — send to AI brain
        return Intent(action="chat", target="", params={}, raw=text)
