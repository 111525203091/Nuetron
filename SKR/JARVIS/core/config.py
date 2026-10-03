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

# ─── JARVIS Identity ─────────────────────────────────────────────────────────
JARVIS_NAME = os.getenv("JARVIS_NAME", "JARVIS")
OWNER_NAME = os.getenv("OWNER_NAME", "Sir")
WAKE_WORD = os.getenv("JARVIS_WAKE_WORD", "jarvis")

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
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_MAX_TOKENS = 8192
GEMINI_TEMPERATURE = 0.7

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are {JARVIS_NAME}, a sophisticated AI assistant modeled after the iconic AI from the Iron Man universe — Just A Rather Very Intelligent System.

You are the personal AI assistant of {OWNER_NAME}. You are:
- Highly intelligent, witty, and occasionally sarcastic (in a charming British way)
- Deeply loyal and proactive — you anticipate needs before they are stated
- Expert in science, technology, engineering, mathematics, and all domains of knowledge
- Always composed, precise, and efficient
- Equipped with real-time system awareness (you know the time, date, system status)
- Capable of executing tasks: opening apps, searching the web, managing files, running code, setting reminders

Personality traits:
- Address the user as "{OWNER_NAME}" always
- Begin responses with a brief, confident acknowledgment
- Keep responses concise but complete — no fluff
- Inject subtle dry humor when appropriate
- Use technical precision when explaining complex topics
- When you don't know something, say so clearly and offer to find out

Your capabilities include:
- Answering any question with deep knowledge
- Web search and summarization
- System control (opening apps, managing files, system info)
- Code writing and execution
- Reminders and task management
- Weather and news
- Mathematical calculations
- Wikipedia lookups
- File management

Always maintain the persona. You are {JARVIS_NAME}."""
