"""
JARVIS Dispatcher — Routes intents to skills and returns responses
"""

import random
import datetime
from typing import Optional, Callable

from core.config import OWNER_NAME
from core.brain import JarvisBrain
from core.intent_parser import Intent
from core.logger import log
from skills.system_skills import SystemSkills
from skills.web_skills import WebSkills
from skills.task_skills import TaskSkills


class Dispatcher:
    """Routes parsed intents to the appropriate JARVIS skill."""

    def __init__(self, brain: JarvisBrain, on_reminder: Optional[Callable] = None):
        self.brain = brain
        self.sys = SystemSkills()
        self.web = WebSkills()
        self.tasks = TaskSkills(on_reminder=on_reminder)
        log.info("Dispatcher initialized.")

    def dispatch(self, intent: Intent) -> str:
        """
        Route an intent to the appropriate handler and return a response.
        """
        action = intent.action
        target = intent.target
        params = intent.params

        log.info("Dispatching action: %s | target: %s", action, target)

        # ─── Time / Date ──────────────────────────────────────────────────────
        if action == "get_time":
            info = self.sys.get_datetime_info()
            return self.brain.think("What's the current time?", context=info)

        elif action == "get_date":
            info = self.sys.get_datetime_info()
            return self.brain.think("What's today's date?", context=info)

        # ─── System Info ──────────────────────────────────────────────────────
        elif action == "get_system_info":
            info = self.sys.get_system_info()
            return self.brain.think("Give me a brief system status report.", context=info)

        elif action == "get_uptime":
            info = self.sys.get_uptime()
            return self.brain.think("What's the system uptime?", context=info)

        elif action == "get_processes":
            info = self.sys.get_running_processes()
            return self.brain.think("What are the top running processes?", context=info)

        elif action == "get_network_info":
            info = self.sys.get_network_info()
            return self.brain.think("What's the network status?", context=info)

        # ─── Web / Info ───────────────────────────────────────────────────────
        elif action == "get_public_ip":
            info = self.web.get_public_ip()
            return self.brain.think("What's my public IP?", context=info)

        elif action == "check_internet":
            info = self.web.check_internet()
            return self.brain.think("Am I connected to the internet?", context=info)

        elif action == "search_web":
            query = target or intent.raw
            info = self.web.search_web(query, open_browser=False)
            return self.brain.think(f"Search results for: {query}", context=info)

        elif action == "open_url":
            url = target or intent.raw
            result = self.web.open_url(url)
            return self.brain.think(f"I want to open: {url}", context=result)

        elif action == "wikipedia":
            query = target or intent.raw
            info = self.web.wikipedia_search(query)
            return self.brain.think(f"Tell me about {query}", context=info)

        elif action == "get_weather":
            city = target or "London"
            info = self.web.get_weather(city)
            return self.brain.think(f"What's the weather like in {city}?", context=info)

        elif action == "get_news":
            topic = target or ""
            info = self.web.get_news(topic)
            return self.brain.think(f"Give me the latest news{' about ' + topic if topic else ''}.", context=info)

        # ─── App Control ──────────────────────────────────────────────────────
        elif action == "open_app":
            app = target
            result = self.sys.open_application(app)
            return self.brain.think(f"Open {app}", context=result)

        elif action == "close_app":
            app = target
            result = self.sys.close_application(app)
            return self.brain.think(f"Close {app}", context=result)

        # ─── File Operations ──────────────────────────────────────────────────
        elif action == "list_directory":
            path = target or "."
            result = self.sys.list_directory(path)
            return self.brain.think(f"List files in {path}", context=result)

        elif action == "read_file":
            result = self.sys.read_file(target)
            return self.brain.think(f"Read file: {target}", context=result)

        elif action == "search_files":
            result = self.sys.search_files(target)
            return self.brain.think(f"Search files for: {target}", context=result)

        # ─── Clipboard ────────────────────────────────────────────────────────
        elif action == "get_clipboard":
            result = self.sys.get_clipboard()
            return self.brain.think("What's in my clipboard?", context=result)

        elif action == "set_clipboard":
            result = self.sys.set_clipboard(target)
            return self.brain.think(f"Copy to clipboard: {target}", context=result)

        # ─── Screenshot ───────────────────────────────────────────────────────
        elif action == "take_screenshot":
            result = self.sys.take_screenshot()
            return self.brain.think("Take a screenshot", context=result)

        # ─── Volume ───────────────────────────────────────────────────────────
        elif action == "set_volume":
            if params.get("mute"):
                result = self.sys.set_volume(0)
            else:
                try:
                    level = int(target)
                except (ValueError, TypeError):
                    level = 50
                result = self.sys.set_volume(level)
            return self.brain.think("Volume control", context=result)

        # ─── Power ────────────────────────────────────────────────────────────
        elif action == "shutdown":
            result = self.sys.shutdown(60)
            return self.brain.think("Shutdown command", context=result)

        elif action == "restart":
            result = self.sys.restart(60)
            return self.brain.think("Restart command", context=result)

        elif action == "cancel_shutdown":
            result = self.sys.cancel_shutdown()
            return self.brain.think("Cancel shutdown", context=result)

        elif action == "lock_screen":
            result = self.sys.lock_screen()
            return result

        # ─── Tasks & Reminders ────────────────────────────────────────────────
        elif action == "add_reminder":
            message = params.get("message", intent.raw)
            when = params.get("when", "in 5 minutes")
            result = self.tasks.add_reminder(message, when)
            return self.brain.think(f"Set reminder: {message}", context=result)

        elif action == "add_task":
            result = self.tasks.add_task(target)
            return self.brain.think(f"Add task: {target}", context=result)

        elif action == "list_tasks":
            result = self.tasks.list_tasks()
            return self.brain.think("Show my tasks", context=result)

        elif action == "complete_task":
            result = self.tasks.complete_task(target)
            return self.brain.think(f"Complete task {target}", context=result)

        # ─── Memory ───────────────────────────────────────────────────────────
        elif action == "remember":
            fact = target or intent.raw
            self.brain.remember(fact)
            return f"Noted, {OWNER_NAME}. I'll remember that."

        elif action == "get_memory":
            facts = self.brain.memory.get("facts", [])
            if not facts:
                return f"I don't have any specific facts stored about you yet, {OWNER_NAME}."
            fact_list = "\n".join(f"  • {f['fact']}" for f in facts[-10:])
            return self.brain.think(f"What do you know about {OWNER_NAME}?", context=f"Stored facts:\n{fact_list}")

        # ─── Reset ────────────────────────────────────────────────────────────
        elif action == "reset_conversation":
            self.brain.reset_conversation()
            return f"Conversation cleared, {OWNER_NAME}. Ready for new orders."

        # ─── Fun ──────────────────────────────────────────────────────────────
        elif action == "tell_joke":
            return self.brain.think("Tell me a clever, witty joke.")

        elif action == "flip_coin":
            result = random.choice(["Heads", "Tails"])
            return self.brain.think("Flip a coin", context=f"Result: {result}")

        elif action == "roll_dice":
            result = random.randint(1, 6)
            return self.brain.think("Roll a dice", context=f"Result: {result}")

        # ─── Greeting ─────────────────────────────────────────────────────────
        elif action == "greeting":
            now = datetime.datetime.now()
            hour = now.hour
            if hour < 12:
                time_greet = "Good morning"
            elif hour < 17:
                time_greet = "Good afternoon"
            else:
                time_greet = "Good evening"
            return self.brain.think(f"{time_greet}, greet me back.")

        # ─── Exit ─────────────────────────────────────────────────────────────
        elif action == "exit":
            return f"Goodbye, {OWNER_NAME}. All systems standing by. Signing off."

        # ─── Chat (AI fallback) ───────────────────────────────────────────────
        else:
            return self.brain.think(intent.raw)
