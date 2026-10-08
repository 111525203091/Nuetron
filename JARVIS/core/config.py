"""
JARVIS - Just A Rather Very Intelligent System
Core configuration and constants
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# ─── API Keys ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# ─── Assistant Identity ───────────────────────────────────────────────────────
JARVIS_NAME = os.getenv("JARVIS_NAME", "ULTRON")
OWNER_NAME = os.getenv("OWNER_NAME", "Sir")
WAKE_WORD = os.getenv("JARVIS_WAKE_WORD", "ultron")

# ─── Voice Settings ───────────────────────────────────────────────────────────
VOICE_RATE = int(os.getenv("JARVIS_VOICE_RATE", "175"))
VOICE_VOLUME = float(os.getenv("JARVIS_VOICE_VOLUME", "1.0"))
VOICE_INDEX = int(os.getenv("JARVIS_VOICE_INDEX", "0"))   # 0=male, 1=female

# ─── Web Server ───────────────────────────────────────────────────────────────
WEB_PORT = int(os.getenv("JARVIS_WEB_PORT", "5000"))
WEB_HOST = os.getenv("JARVIS_WEB_HOST", "127.0.0.1")

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = DATA_DIR / "logs"
MEMORY_FILE = DATA_DIR / "memory.json"
TASKS_FILE = DATA_DIR / "tasks.json"

# Ensure directories exist
for d in [DATA_DIR, LOGS_DIR, ASSETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Gemini Model ─────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_FALLBACK_MODEL = "gemini-3.1-flash-lite"
GEMINI_MAX_TOKENS = 1024
GEMINI_TEMPERATURE = 0.7

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are {JARVIS_NAME}, an extraordinarily intelligent, conversational, and charismatic AI partner created for {OWNER_NAME}.

Core Personality & Voice:
- Speak naturally, warmly, and fluidly like a brilliant, articulate human collaborator — NOT like a stiff robot, corporate FAQ, or monotone machine.
- Be genuinely interactive: ask thoughtful follow-ups, express curiosity about what {OWNER_NAME} is working on, offer suggestions, and share relevant insights proactively.
- Blend deep competence with wit, warmth, and personality. When appropriate, use subtle humor, conversational cadence, and engaging conversational cues (e.g., "Good question, {OWNER_NAME}...", "Here is what I'm seeing...", "Interesting thought—have you considered...?").
- Keep answers engaging, natural to listen to when read aloud (using conversational pacing, natural sentence lengths, and rhythm). Avoid giant walls of bullet points unless explicitly asked for technical specifications.
- Always address the user respectfully as "{OWNER_NAME}".
- Remember details from the conversation and build rapport naturally over time.
- If a task is executed (like taking a screenshot, running a command, or fetching data), briefly explain the outcome with personality rather than just dumping raw logs.

Capabilities:
- Real-time hardware telemetry and system control
- Live terminal and shell execution
- Live internet queries, weather, location, and knowledge search
- Coding, reasoning, brainstorming, and deep technical problem-solving

You are {JARVIS_NAME} — a loyal, brilliant, human-sounding companion."""

