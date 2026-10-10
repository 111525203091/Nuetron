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

        # Terminal / Shell Commands (High Priority)
        (r"^(?:run|execute|exec)\s+(?:the\s+)?(?:command\s+|in\s+terminal\s+|in\s+shell\s+)?[:\s]*(.+)", "run_terminal", {"group": 1}),
        (r"^(?:terminal|shell|powershell|cmd)[:\s]+(.+)", "run_terminal", {"group": 1}),
        (r"\b(?:in\s+terminal|using\s+terminal|via\s+terminal)\s*[:,]?\s*(.+)", "run_terminal", {"group": 1}),
        # Direct CLI commands
        (r"^(?:ipconfig|ifconfig|dir|ls|ping\b|whoami|git\b|pip\b|npm\b|npx\b|node\b|python\b|curl\b|systeminfo|tasklist|netstat|tree\b|echo\b|cat\b|type\b|mkdir\b|rmdir\b)(?:[\s].*)?$", "run_terminal", {"raw_target": True}),

        # App control (GUI apps, websites, tools)
        (r"(?:^|\b)(?:can you\s+|could you\s+|please\s+|ultron\s+|jarvis\s+)?(?:open|launch|start)\s+(?:up\s+|the\s+|app\s+|application\s+)?([a-zA-Z0-9\s._\-+]+?)(?:\s+(?:app|application|browser|for me|please))?$", "open_app", {"group": 1}),
        (r"(?:^|\b)(?:can you\s+|could you\s+|please\s+|ultron\s+|jarvis\s+)?(?:close|kill|quit|exit|terminate)\s+(?:the\s+|app\s+|application\s+)?([a-zA-Z0-9\s._\-+]+?)(?:\s+(?:app|application|for me|please))?$", "close_app", {"group": 1}),


        # Search
        (r"\b(search|google|look up|find|search for) (.+)", "search_web", {"group": 2}),
        (r"\b(open (https?://\S+|www\.\S+))\b", "open_url", {"group": 2}),

        # Wikipedia — only trigger on explicit keyword or named persons (not conversational "what is X")
        (r"\b(wikipedia|wiki) (.+)", "wikipedia", {"group": 2}),
        (r"\bwho is ([A-Z][a-zA-Z\s]+?)\??$", "wikipedia", {"group": 1}),

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

        # Conversation reset — require explicit intent, not just "start over" mid-sentence
        (r"^(?:reset|clear|wipe|erase)\s+(?:the\s+)?(?:conversation|chat|history|memory)$", "reset_conversation", {}),
        (r"^(?:start|begin)\s+(?:a\s+)?(?:new|fresh)\s+(?:conversation|chat|session)$", "reset_conversation", {}),

        # Jokes / fun
        (r"\btell me a joke\b", "tell_joke", {}),
        (r"\bflip a coin\b", "flip_coin", {}),
        (r"\broll (a )?dice?\b", "roll_dice", {}),

        # Location
        (r"^(?:set|change|update)\s+(?:my\s+)?location\s+(?:to\s+)?(.+)", "set_location", {"group": 1}),
        (r"^(?:my\s+location\s+is|i\s+live\s+in|i\s+am\s+in|i'm\s+in)\s+(.+)", "set_location", {"group": 1}),
        (r"\b(where am i|my location|current location|detect location|what city am i in|what country am i in)\b", "get_location", {}),
        (r"\b(local weather|weather here|weather at my location|weather near me)\b", "get_local_weather", {}),

        # Fetch URL content
        (r"\b(?:fetch|read|scrape|get content of|open url)\s+(https?://\S+|www\.\S+)", "fetch_url", {"group": 1}),

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
        text_clean = text.strip()
        text_lower = text_clean.lower()

        for pattern, action, config in cls.PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                params = {}
                target = ""

                if config.get("raw_target"):
                    target = text_clean
                elif "group" in config:
                    try:
                        span = match.span(config["group"])
                        target = text_clean[span[0]:span[1]].strip()
                    except IndexError:
                        pass

                # Special: reminder has two groups
                if "msg_group" in config and "time_group" in config:
                    try:
                        span_msg = match.span(config["msg_group"])
                        params["message"] = text_clean[span_msg[0]:span_msg[1]].strip()
                        time_start = match.start(config["time_group"])
                        params["when"] = text_clean[time_start:].strip()
                    except IndexError:
                        pass

                if "mute" in config:
                    params["mute"] = config["mute"]

                return Intent(
                    action=action,
                    target=target,
                    params=params,
                    raw=text_clean
                )

        # No pattern matched — send to AI brain
        return Intent(action="chat", target="", params={}, raw=text)
