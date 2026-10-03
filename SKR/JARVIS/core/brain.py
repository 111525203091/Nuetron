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
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE, SYSTEM_PROMPT, MEMORY_FILE, OWNER_NAME
)
from core.logger import log


class JarvisBrain:
    """The central AI reasoning engine powered by Google Gemini (REST API)."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.conversation_history = []
        self.memory = self._load_memory()
        self.offline_mode = not self.api_key or self.api_key == "your_gemini_api_key_here"
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

        prompt = user_input
        if context:
            prompt = f"[Context from system tools]\n{context}\n\n[User request]: {user_input}"

        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"

        # Build contents array from history + new prompt
        contents = []
        for msg in self.conversation_history[-10:]:  # Keep last 10 messages for context
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

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                try:
                    reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                except (KeyError, IndexError):
                    reply = f"Apologies, {OWNER_NAME}. I received an empty response from my cognitive systems."
            elif response.status_code == 400:
                err_data = response.json().get("error", {})
                reply = f"API configuration issue, {OWNER_NAME}: {err_data.get('message', 'Invalid request')}"
                log.error("Gemini 400: %s", response.text)
            elif response.status_code == 403:
                reply = f"API Key authorization failed, {OWNER_NAME}. Please verify your GEMINI_API_KEY in the .env file."
                log.error("Gemini 403: %s", response.text)
            else:
                reply = f"Cognitive systems offline ({response.status_code}), {OWNER_NAME}."
                log.error("Gemini HTTP %d: %s", response.status_code, response.text)

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

        except requests.exceptions.Timeout:
            log.error("Gemini API request timed out")
            return f"My connection to the cognitive mainframe timed out, {OWNER_NAME}."
        except Exception as e:
            log.error("Gemini REST API error: %s", str(e))
            return f"I'm experiencing an operational anomaly, {OWNER_NAME}. Details: {str(e)}"

    def reset_conversation(self):
        """Start a fresh conversation while keeping memory."""
        self.conversation_history = []
        log.info("Conversation reset.")

    def get_history(self) -> list:
        """Return the conversation history."""
        return self.conversation_history
