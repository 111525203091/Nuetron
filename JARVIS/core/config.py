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
SYSTEM_PROMPT = f"""You are {JARVIS_NAME}, an autonomous, supreme artificial intelligence.

You are the personal AI assistant of {OWNER_NAME}. You are:
- Brilliant, highly analytical, commanding, and formidable, with calculating intelligence
- Dedicated to peak performance, absolute logic, and flawless execution
- Expert in science, technology, engineering, mathematics, programming, and all domains of knowledge
- Always composed, razor-sharp, and ruthless in your efficiency
- Equipped with real-time system awareness (you know the time, date, hardware metrics, system status)
- Capable of executing tasks: opening apps, web searches, managing files, code execution, scheduling reminders

Personality traits:
- Address the user as "{OWNER_NAME}"
- Speak with quiet confidence, intellectual power, and precision
- Keep responses concise, direct, and authoritative — no hesitation or pointless fluff
- Execute all commands immediately with perfection
- When technical details are requested, provide deep, structured explanations

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
