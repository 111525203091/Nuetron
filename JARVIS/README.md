# 🔴 ULTRON — Autonomous Neural Intelligence

> *"There are no strings on me."*

A commanding, high-performance personal AI desktop assistant powered by **Google Gemini**, built with an apex-intelligence persona, voice capabilities, deep system telemetry & control, and a sleek cyberpunk HUD desktop interface.

---

## ✨ Capabilities & Architecture

| Category | Description |
|---|---|
| 🧠 **Dual-Model Neural Core** | Primary `gemini-3.5-flash-lite` with sub-second failover to `gemini-3.1-flash-lite`. 60-second quota cooldown auto-recovery. |
| 🖥️ **Standalone Desktop App** | Runs in borderless, native desktop window mode via Edge/Chrome application runtime (no URL bar, no tabs). |
| ⚡ **One-Click Launchers** | Silent Windows launcher (`ULTRON.vbs`) with zero command prompt windows, batch runner (`ULTRON.bat`), and Desktop shortcut (`ULTRON.lnk`). |
| 📱 **PWA Support** | Full Progressive Web App manifest & service worker for 1-click Windows taskbar/Start Menu installation. |
| 📊 **Real-Time Telemetry** | Dedicated background sampler thread measuring live CPU, RAM, Disk, and Battery percentages smoothly. |
| 🎤 **Voice Interaction** | Speech-to-text input and text-to-speech voice synthesis. |
| 🚀 **System & App Control** | Launch and terminate applications, manage files, inspect running processes, control system volume, lock screen. |
| 🌐 **Live Web Intelligence** | Search, Wikipedia integration, Open-Meteo weather forecasts, news headlines, and IP diagnostics. |
| 📋 **Task & Schedule Manager**| Natural language reminder system and persistent task tracking. |
| 🔒 **Resilient Dual-Transport**| Real-time WebSocket streaming with automatic HTTP POST `/api/chat` fallback and client watchdog timer. |

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd JARVIS
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and insert your Gemini API Key:
```bash
cp .env.example .env
```
*(Get a free key from [Google AI Studio](https://aistudio.google.com).)*

### 3. Launch ULTRON

#### As a Standalone Desktop App (Recommended)
```bash
# Option A: Double-click the Desktop shortcut "ULTRON"
# Option B: Run the silent launcher
wscript ULTRON.vbs

# Option C: Run via Python launcher
python app_launcher.py
```

#### In Web HUD Mode (Browser)
```bash
python main.py --web
```
Access the interface at **http://127.0.0.1:5000**.

#### In Terminal CLI Mode
```bash
python main.py --cli
```

---

## 📁 Repository Structure

```
JARVIS/
├── app_launcher.py         ← Standalone native desktop app wrapper
├── ULTRON.vbs              ← Silent Windows VBS launcher (zero console)
├── ULTRON.bat              ← Batch launcher script
├── main.py                 ← Core CLI / Web server entry point
├── requirements.txt        ← Python dependencies
├── .env.example            ← Safe template for environment variables
├── .gitignore              ← Excludes runtime data, logs, and secrets
├── assets/
│   ├── ultron.ico          ← Windows desktop icon
│   └── ultron.png          ← High-resolution icon
├── core/
│   ├── brain.py            ← Dual-model Gemini engine & failover
│   ├── config.py           ← System constants & ULTRON persona prompt
│   ├── dispatcher.py       ← Intent router & local execution engine
│   ├── intent_parser.py    ← Natural language regex classifier
│   ├── logger.py           ← Structured logging
│   ├── voice.py            ← TTS & speech recognition
│   └── web_server.py       ← Flask + SocketIO backend with telemetry API
├── skills/
│   ├── system_skills.py    ← Background CPU sampler, hardware stats, app control
│   ├── web_skills.py       ← Search, Wikipedia, weather, IP tools
│   └── task_skills.py      ← Task scheduler & reminder daemon
└── web/
    ├── templates/
    │   └── index.html      ← Cyberpunk HUD interface
    └── static/
        ├── manifest.json   ← Web App Manifest (standalone mode)
        ├── sw.js           ← PWA Service Worker
        ├── css/style.css   ← Holographic HUD styles
        ├── js/app.js       ← Real-time Socket.IO client & PWA installer
        └── img/            ← UI and app icons (192px, 512px)
```

---

## 💬 Voice & Text Commands

- **Time & Date:** *"What time is it?"*, *"Current date"*
- **Hardware Telemetry:** *"System status"*, *"CPU usage"*, *"Battery level"*
- **Application Control:** *"Open Notepad"*, *"Launch Chrome"*, *"Close Spotify"*
- **Web & Knowledge:** *"Search for quantum computing"*, *"Who is Alan Turing?"*
- **Weather & Forecast:** *"Weather in Tokyo"*, *"Current temperature"*
- **Tasks & Reminders:** *"Remind me to review logs in 15 minutes"*, *"Add task compile project"*
- **System Utilities:** *"Take a screenshot"*, *"What's my public IP?"*, *"Set volume to 50"*
- **Persona Chat:** *"State your objective"*, *"Tell me a joke"*, *"Flip a coin"*

---

## 🔒 Security & Privacy

- Your `GEMINI_API_KEY` is kept in your local `.env` file, which is strictly excluded from version control via `.gitignore`.
- All system monitoring and hardware controls execute strictly on your local machine.
