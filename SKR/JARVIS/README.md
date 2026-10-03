# JARVIS — Just A Rather Very Intelligent System

> *"At your service, Sir."*

A full-featured personal AI assistant powered by **Google Gemini**, built with a Jarvis-inspired personality, voice support, system control, and a slick HUD-style web interface.

---

## ✨ Features

| Category | Capabilities |
|---|---|
| 🤖 **AI Brain** | Gemini 2.0 Flash — persistent memory, conversation history |
| 🎤 **Voice** | Speech-to-text input + text-to-speech output |
| 💻 **System** | CPU/RAM/disk stats, uptime, running processes, network info |
| 🚀 **App Control** | Open/close Chrome, VS Code, Notepad, Spotify, and 20+ apps |
| 🌐 **Web** | DuckDuckGo search, Wikipedia, weather, news headlines |
| 📋 **Tasks** | Add tasks, set reminders with natural language times |
| 📁 **Files** | List directories, read files, search files |
| 📋 **Clipboard** | Read and write clipboard |
| 📸 **Screenshot** | Capture and save screenshots |
| 🔇 **Volume** | Set system volume |
| 🔒 **Security** | Lock screen, schedule shutdown/restart |
| 🎨 **3 Interfaces** | Terminal CLI + Web UI (HUD) + REST API |

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd JARVIS
pip install -r requirements.txt
```

> **Note:** `pyaudio` may require manual installation on Windows:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 2. Configure JARVIS
```bash
python main.py --setup
```
Enter your **Gemini API Key** (get one free at [aistudio.google.com](https://aistudio.google.com)).

### 3. Launch JARVIS
```bash
python main.py
```
This starts the CLI and opens the web interface at **http://127.0.0.1:5000**

---

## 🖥 Launch Modes

```bash
python main.py              # Full mode: CLI + Web + Voice
python main.py --cli        # Terminal only
python main.py --web        # Web interface only (opens browser)
python main.py --no-voice   # Disable voice I/O
python main.py --port 8080  # Custom port
python main.py --setup      # First-time setup
```

---

## 💬 Example Commands

```
"What's the time?"
"Open Chrome"
"Weather in Mumbai"
"Search for Python tutorials"
"Who is Nikola Tesla?"
"System status"
"Remind me to drink water in 30 minutes"
"Add task finish the report"
"List my tasks"
"Take a screenshot"
"What's my public IP?"
"Tell me a joke"
"Set volume to 60"
"Lock the screen"
```

---

## 🌐 Web Interface

The web UI features:
- **Iron Man / HUD aesthetic** with arc reactor animations
- **Real-time chat** via WebSocket
- **Browser TTS** for voice output
- **Browser STT** for voice input
- **Live system metrics** (CPU, RAM, Disk)
- **Quick action buttons**
- **Dark/light theme toggle**

---

## 📁 Project Structure

```
JARVIS/
├── main.py              ← Entry point
├── requirements.txt
├── .env                 ← Your API keys (created by --setup)
├── core/
│   ├── brain.py         ← Gemini AI engine
│   ├── voice.py         ← TTS + STT
│   ├── cli.py           ← Terminal interface
│   ├── web_server.py    ← Flask + SocketIO server
│   ├── dispatcher.py    ← Intent → Skill router
│   ├── intent_parser.py ← Natural language parser
│   ├── config.py        ← Configuration
│   └── logger.py        ← Logging
├── skills/
│   ├── system_skills.py ← OS, files, apps
│   ├── web_skills.py    ← Search, weather, news
│   └── task_skills.py   ← Tasks & reminders
├── web/
│   ├── templates/
│   │   └── index.html   ← Main web UI
│   └── static/
│       ├── css/style.css
│       └── js/app.js
└── data/
    ├── memory.json      ← Persistent memory
    └── tasks.json       ← Tasks & reminders
```

---

## 🔑 API Keys

| Service | Required | Get it at |
|---|---|---|
| Google Gemini | ✅ Required | [aistudio.google.com](https://aistudio.google.com) |
| OpenWeatherMap | ⚡ Optional | [openweathermap.org](https://openweathermap.org/api) |
| WolframAlpha | ⚡ Optional | [developer.wolframalpha.com](https://developer.wolframalpha.com) |

---

## 🛠 Troubleshooting

**`pyaudio` install fails:**
```bash
pip install pipwin && pipwin install pyaudio
```
Or download the wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).

**Voice not working:**
- Run with `--no-voice` flag to skip voice entirely
- Voice input requires a working microphone
- Voice output requires system audio

**Port already in use:**
```bash
python main.py --port 8080
```
