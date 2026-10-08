"""
JARVIS Brain — Gemini-powered reasoning and conversation engine
Uses the Gemini REST API directly for maximum compatibility across all Python versions.
"""

import json
import datetime
import requests
from pathlib import Path
from typing import Optional

from core.config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODEL, GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE, SYSTEM_PROMPT, MEMORY_FILE, OWNER_NAME
)
from core.logger import log


class JarvisBrain:
    """The central AI reasoning engine powered by Google Gemini (REST API)."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.fallback_model = GEMINI_FALLBACK_MODEL
        self.conversation_history = []
        self.memory = self._load_memory()
        self.session = requests.Session()
        self.offline_mode = not self.api_key or self.api_key == "your_gemini_api_key_here"
        self._quota_cooldown_until = 0   # epoch timestamp; Gemini skipped until this time
        if self.offline_mode:
            log.warning("GEMINI_API_KEY is not configured. JARVIS running in Local Protocol Mode.")
        else:
            log.info("JARVIS Brain initialized via Gemini REST API: %s", self.model)

    def _build_system_prompt(self) -> str:
        """Build dynamic system prompt with current context."""
        now = datetime.datetime.now()
        context = f"""Current Date & Time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}
Timezone: Local system time

{SYSTEM_PROMPT}"""
        return context

    def _load_memory(self) -> dict:
        """Load persistent memory from disk."""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"facts": [], "preferences": {}, "interactions": 0}

    def save_memory(self):
        """Persist memory to disk."""
        self.memory["interactions"] = self.memory.get("interactions", 0) + 1
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            log.error("Could not save memory: %s", str(e))

    def remember(self, fact: str):
        """Store a fact in persistent memory."""
        self.memory["facts"].append({
            "fact": fact,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self.save_memory()

    def think(self, user_input: str, context: Optional[str] = None) -> str:
        """
        Process user input and return JARVIS's response using the Gemini REST API.

        Args:
            user_input: The user's message
            context: Optional additional context (system info, skill output, etc.)

        Returns:
            JARVIS's response as a string
        """
        if self.offline_mode:
            if context:
                reply = f"{context}"
            else:
                reply = (
                    f"At your service, {OWNER_NAME}. All system diagnostics, application controls, "
                    f"file operations, and local tools are fully operational.\n\n"
                    f"💡 *To activate full AI conversational intelligence, add your free Google Gemini API key to the `.env` file.*"
                )
            self.conversation_history.append({"role": "user", "content": user_input, "timestamp": datetime.datetime.now().isoformat()})
            self.conversation_history.append({"role": "jarvis", "content": reply, "timestamp": datetime.datetime.now().isoformat()})
            self.save_memory()
            return reply

        # ── Quota cooldown check ──────────────────────────────────────────────
        import time as _time
        now_ts = _time.time()
        if now_ts < self._quota_cooldown_until:
            remaining = int(self._quota_cooldown_until - now_ts)
            log.info("Quota cooldown active — %ds remaining. Serving locally.", remaining)
            reply = (
                f"My conversational systems are in a brief cooldown, {OWNER_NAME} ({remaining}s remaining). "
                f"All local commands — time, system info, apps, tasks, weather — are fully operational. "
                f"Ask me something local, or wait a moment and I'll be back online."
            )
            return reply

        prompt = user_input
        if context:
            prompt = f"[Context from system tools]\n{context}\n\n[User request]: {user_input}"

        # Build contents array from history + new prompt (keep last 6 for speed)
        contents = []
        for msg in self.conversation_history[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        # Add the new message
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "system_instruction": {
                "parts": [{"text": self._build_system_prompt()}]
            },
            "generationConfig": {
                "temperature": GEMINI_TEMPERATURE,
                "maxOutputTokens": GEMINI_MAX_TOKENS,
            }
        }

        reply = None
        models_to_try = [self.model, self.fallback_model]

        for current_model in models_to_try:
            url = f"{self.BASE_URL}/{current_model}:generateContent?key={self.api_key}"
            try:
                response = self.session.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=7
                )
                if response.status_code == 200:
                    data = response.json()
                    try:
                        reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        break
                    except (KeyError, IndexError):
                        pass
                elif response.status_code == 429:
                    log.warning("Model %s returned 429 (rate limited) — trying fallback...", current_model)
                    continue
                elif response.status_code == 403:
                    reply = f"API Key authorization failed, {OWNER_NAME}. Please verify your GEMINI_API_KEY in .env."
                    break
                else:
                    log.warning("Model %s returned HTTP %d — trying fallback...", current_model, response.status_code)
                    continue
            except Exception as e:
                log.warning("Model %s request failed (%s) — trying fallback...", current_model, str(e))
                continue

        if not reply:
            import time as _time
            self._quota_cooldown_until = _time.time() + 30
            reply = (
                f"My cognitive mainframe is momentarily refreshing, {OWNER_NAME}. "
                f"Operating in local protocol mode. All local system tools, diagnostics, and controls remain active."
            )

        # Autonomous Terminal Execution Handler
        if reply:
            import re as _re
            exec_cmds = _re.findall(r"\[(?:EXEC|TERMINAL):\s*(.+?)\]", reply, _re.IGNORECASE)
            if exec_cmds:
                from skills.system_skills import SystemSkills
                for cmd in exec_cmds:
                    clean_cmd = cmd.strip()
                    log.info("ULTRON executing autonomous command: %s", clean_cmd)
                    exec_res = SystemSkills.run_terminal_command(clean_cmd)
                    formatted = SystemSkills.format_terminal_result(exec_res)
                    tag_regex = _re.compile(rf"\[(?:EXEC|TERMINAL):\s*{_re.escape(cmd)}\]", _re.IGNORECASE)
                    reply = tag_regex.sub(lambda _m, f=formatted: f"\n\n{f}\n\n", reply)

        # Log to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self.conversation_history.append({
            "role": "jarvis",
            "content": reply,
            "timestamp": datetime.datetime.now().isoformat()
        })

        self.save_memory()
        return reply

    def reset_conversation(self):
        """Start a fresh conversation while keeping memory."""
        self.conversation_history = []
        log.info("Conversation reset.")

    def get_history(self) -> list:
        """Return the conversation history."""
        return self.conversation_history
