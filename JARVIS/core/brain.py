"""
JARVIS Brain — Gemini + xAI Grok powered reasoning and conversation engine.
Uses REST APIs directly for maximum compatibility across all Python versions.
"""

import json
import datetime
import requests
from pathlib import Path
from typing import Optional

from core.config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODEL, GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE, SYSTEM_PROMPT, MEMORY_FILE, OWNER_NAME,
    XAI_API_KEY, XAI_MODEL, XAI_FALLBACK_MODEL, XAI_MAX_TOKENS, XAI_BASE_URL,
)
from core.logger import log



class JarvisBrain:
    """The central AI reasoning engine powered by Gemini + xAI Grok (REST APIs)."""

    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.fallback_model = GEMINI_FALLBACK_MODEL
        self.xai_api_key = XAI_API_KEY
        self.conversation_history = []
        self.memory = self._load_memory()
        self.session = requests.Session()
        self.offline_mode = not self.api_key or self.api_key == "your_gemini_api_key_here"
        self._quota_cooldown_until = 0   # epoch timestamp; Gemini skipped until this time

        if self.offline_mode and not self.xai_api_key:
            log.warning("No AI API keys configured. JARVIS running in Local Protocol Mode.")
        else:
            engines = []
            if not self.offline_mode:
                engines.append(f"Gemini ({self.model})")
            if self.xai_api_key:
                engines.append(f"xAI Grok ({XAI_MODEL})")
            log.info("JARVIS Brain initialized — engines: %s", " + ".join(engines))


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

    def _think_grok(self, prompt: str) -> Optional[str]:
        """
        Call xAI Grok via its OpenAI-compatible chat completions endpoint.
        Returns the reply string or None on failure.
        """
        if not self.xai_api_key:
            return None

        # Build messages list (OpenAI format)
        messages = [{"role": "system", "content": self._build_system_prompt()}]
        for msg in self.conversation_history[-6:]:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": XAI_MODEL,
            "messages": messages,
            "max_tokens": XAI_MAX_TOKENS,
            "temperature": GEMINI_TEMPERATURE,
        }

        models_to_try = [XAI_MODEL, XAI_FALLBACK_MODEL]
        for model in models_to_try:
            payload["model"] = model
            try:
                resp = self.session.post(
                    f"{XAI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.xai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        return data["choices"][0]["message"]["content"].strip()
                    except (KeyError, IndexError):
                        pass
                elif resp.status_code == 429:
                    log.warning("Grok %s rate-limited, trying fallback...", model)
                    continue
                elif resp.status_code == 401:
                    log.warning("xAI API key auth failed (401).")
                    return None
                else:
                    log.warning("Grok %s returned HTTP %d", model, resp.status_code)
                    continue
            except Exception as e:
                log.warning("Grok %s request failed: %s", model, e)
                continue

        return None

    def think(self, user_input: str, context: Optional[str] = None) -> str:
        """
        Process user input and return JARVIS's response.
        Engine priority: Gemini → xAI Grok → Local mode.

        Args:
            user_input: The user's message
            context: Optional additional context (system info, skill output, etc.)

        Returns:
            JARVIS's response as a string
        """
        # ── Offline mode (no keys at all) ─────────────────────────────────────
        if self.offline_mode and not self.xai_api_key:
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

        prompt = user_input
        if context:
            prompt = f"[Context from system tools]\n{context}\n\n[User request]: {user_input}"

        reply = None

        # ── 1. Try Gemini (unless in cooldown or offline) ─────────────────────
        import time as _time
        now_ts = _time.time()
        gemini_on_cooldown = now_ts < self._quota_cooldown_until

        if not self.offline_mode and not gemini_on_cooldown:
            contents = []
            for msg in self.conversation_history[-6:]:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            payload = {
                "contents": contents,
                "system_instruction": {"parts": [{"text": self._build_system_prompt()}]},
                "generationConfig": {
                    "temperature": GEMINI_TEMPERATURE,
                    "maxOutputTokens": GEMINI_MAX_TOKENS,
                }
            }

            for current_model in [self.model, self.fallback_model]:
                url = f"{self.GEMINI_BASE_URL}/{current_model}:generateContent?key={self.api_key}"
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
                        log.warning("Gemini %s rate-limited — trying Grok...", current_model)
                        break   # no point trying other Gemini model if rate-limited
                    elif response.status_code == 403:
                        log.warning("Gemini 403 auth error.")
                        break
                    else:
                        log.warning("Gemini %s returned HTTP %d", current_model, response.status_code)
                        continue
                except Exception as e:
                    log.warning("Gemini %s failed: %s", current_model, e)
                    continue

        # ── 2. Try xAI Grok if Gemini failed / on cooldown ───────────────────
        if not reply and self.xai_api_key:
            log.info("Gemini unavailable — falling back to xAI Grok...")
            reply = self._think_grok(prompt)
            if reply:
                log.info("Response served by xAI Grok.")

        # ── 3. Full fallback: local mode ──────────────────────────────────────
        if not reply:
            self._quota_cooldown_until = _time.time() + 30
            reply = (
                f"My cognitive mainframe is momentarily refreshing, {OWNER_NAME}. "
                f"Operating in local protocol mode. All local system tools, diagnostics, and controls remain active."
            )

        # ── Autonomous Terminal Execution Handler ─────────────────────────────
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

        # ── Log to conversation history ───────────────────────────────────────
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
