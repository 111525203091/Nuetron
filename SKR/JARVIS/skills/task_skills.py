"""
JARVIS Task & Reminder Skills
"""

import json
import uuid
import datetime
import threading
import time
from pathlib import Path
from typing import Optional, List, Callable

from core.config import TASKS_FILE
from core.logger import log


class TaskSkills:
    """Skills for managing tasks, reminders, and schedules."""

    def __init__(self, on_reminder: Optional[Callable] = None):
        """
        Args:
            on_reminder: Callback called when a reminder fires.
                         Called with (task_title: str, message: str)
        """
        self.tasks = self._load_tasks()
        self.on_reminder = on_reminder
        self._reminder_thread = threading.Thread(
            target=self._reminder_loop, daemon=True
        )
        self._reminder_thread.start()

    def _load_tasks(self) -> list:
        if TASKS_FILE.exists():
            try:
                with open(TASKS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_tasks(self):
        with open(TASKS_FILE, "w") as f:
            json.dump(self.tasks, f, indent=2, default=str)

    def add_task(self, title: str, description: str = "", due: Optional[str] = None) -> str:
        """Add a task to the list."""
        task = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "description": description,
            "due": due,
            "created": datetime.datetime.now().isoformat(),
            "done": False,
            "type": "task"
        }
        self.tasks.append(task)
        self._save_tasks()
        return f"Task added: '{title}'" + (f" — due: {due}" if due else "")

    def add_reminder(self, message: str, when: str) -> str:
        """
        Add a reminder.

        Args:
            message: What to remind about
            when: Natural language time string like "in 5 minutes", "at 3:30 PM",
                  "in 1 hour", "tomorrow at 9 AM"

        Returns:
            Confirmation string
        """
        remind_time = self._parse_time(when)
        if not remind_time:
            return f"Could not parse time: '{when}'. Try 'in 5 minutes' or 'at 3:30 PM'"

        reminder = {
            "id": str(uuid.uuid4())[:8],
            "title": message,
            "remind_at": remind_time.isoformat(),
            "created": datetime.datetime.now().isoformat(),
            "done": False,
            "type": "reminder"
        }
        self.tasks.append(reminder)
        self._save_tasks()
        return f"Reminder set for {remind_time.strftime('%I:%M %p on %B %d')}: '{message}'"

    def _parse_time(self, when: str) -> Optional[datetime.datetime]:
        """Parse natural language time expressions."""
        now = datetime.datetime.now()
        when_lower = when.lower().strip()

        try:
            # "in X minutes/hours/seconds"
            if when_lower.startswith("in "):
                parts = when_lower[3:].split()
                if len(parts) >= 2:
                    amount = int(parts[0])
                    unit = parts[1].rstrip("s")  # normalize plural
                    if unit in ["second", "sec"]:
                        return now + datetime.timedelta(seconds=amount)
                    elif unit in ["minute", "min"]:
                        return now + datetime.timedelta(minutes=amount)
                    elif unit in ["hour", "hr"]:
                        return now + datetime.timedelta(hours=amount)
                    elif unit == "day":
                        return now + datetime.timedelta(days=amount)

            # "at HH:MM" or "at HH:MM AM/PM"
            elif when_lower.startswith("at "):
                time_str = when_lower[3:].strip()
                for fmt in ["%I:%M %p", "%H:%M", "%I %p"]:
                    try:
                        t = datetime.datetime.strptime(time_str.upper(), fmt)
                        result = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
                        if result < now:
                            result += datetime.timedelta(days=1)
                        return result
                    except ValueError:
                        continue

            # "tomorrow at HH:MM"
            elif "tomorrow" in when_lower:
                time_part = when_lower.replace("tomorrow", "").replace("at", "").strip()
                for fmt in ["%I:%M %p", "%H:%M", "%I %p"]:
                    try:
                        t = datetime.datetime.strptime(time_part.upper(), fmt)
                        return (now + datetime.timedelta(days=1)).replace(
                            hour=t.hour, minute=t.minute, second=0, microsecond=0
                        )
                    except ValueError:
                        continue
                return now + datetime.timedelta(days=1)

        except (ValueError, IndexError):
            pass

        return None

    def list_tasks(self, show_done: bool = False) -> str:
        """List all tasks and reminders."""
        items = [t for t in self.tasks if not t.get("done") or show_done]
        if not items:
            return "No tasks or reminders pending."

        lines = []
        tasks = [t for t in items if t.get("type") == "task"]
        reminders = [t for t in items if t.get("type") == "reminder"]

        if tasks:
            lines.append("📋 Tasks:")
            for t in tasks:
                done_mark = "✅" if t.get("done") else "⬜"
                due = f" — Due: {t['due']}" if t.get("due") else ""
                lines.append(f"  {done_mark} [{t['id']}] {t['title']}{due}")

        if reminders:
            lines.append("\n⏰ Reminders:")
            for r in reminders:
                done_mark = "✅" if r.get("done") else "⏳"
                remind_at = datetime.datetime.fromisoformat(r["remind_at"])
                lines.append(
                    f"  {done_mark} [{r['id']}] {r['title']} — "
                    f"at {remind_at.strftime('%I:%M %p, %b %d')}"
                )

        return "\n".join(lines)

    def complete_task(self, task_id: str) -> str:
        """Mark a task as done."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["done"] = True
                self._save_tasks()
                return f"Task '{task['title']}' marked as complete."
        return f"No task found with ID: {task_id}"

    def delete_task(self, task_id: str) -> str:
        """Delete a task by ID."""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                removed = self.tasks.pop(i)
                self._save_tasks()
                return f"Deleted: '{removed['title']}'"
        return f"No task found with ID: {task_id}"

    def clear_completed(self) -> str:
        """Remove all completed tasks."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t.get("done")]
        self._save_tasks()
        removed = before - len(self.tasks)
        return f"Cleared {removed} completed task(s)."

    def _reminder_loop(self):
        """Background loop that fires reminders at the right time."""
        while True:
            now = datetime.datetime.now()
            for task in self.tasks:
                if task.get("type") == "reminder" and not task.get("done"):
                    remind_at = datetime.datetime.fromisoformat(task["remind_at"])
                    if now >= remind_at:
                        task["done"] = True
                        self._save_tasks()
                        log.info("Reminder fired: %s", task["title"])
                        if self.on_reminder:
                            try:
                                self.on_reminder(task["title"], remind_at)
                            except Exception as e:
                                log.error("Reminder callback error: %s", str(e))
            time.sleep(15)  # Check every 15 seconds
