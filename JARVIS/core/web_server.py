"""
JARVIS Web Server — Flask + SocketIO web interface backend
"""

import re
import threading
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from core.config import WEB_HOST, WEB_PORT, JARVIS_NAME, OWNER_NAME
from core.brain import JarvisBrain
from core.intent_parser import IntentParser
from core.dispatcher import Dispatcher
from core.logger import log


def to_speech(text: str) -> str:
    """
    Convert a formatted display response into a clean, natural spoken sentence.
    Strips markdown, emoji, tables, code blocks, bullet lists, and technical noise.
    Returns only the first meaningful spoken portion (max ~2 sentences) so Ultron
    sounds like he's *talking*, not reading a report.
    """
    if not text:
        return ""

    # 1. Remove fenced code blocks entirely
    text = re.sub(r'```[\s\S]*?```', '', text)

    # 2. Remove inline code
    text = re.sub(r'`[^`]+`', '', text)

    # 3. Strip markdown links — keep label only
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # 4. Strip bold / italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)

    # 5. Strip markdown headings (#, ##, ###)
    text = re.sub(r'#{1,6}\s+', '', text)

    # 6. Strip all emoji (Unicode ranges)
    text = re.sub(
        r'[\U00002600-\U000027BF]|[\U0001F300-\U0001FAFF]|'
        r'[\U00002702-\U000027B0]|[\U0000FE00-\U0000FE0F]|'
        r'[\U0001F1E0-\U0001F1FF]|[\u2600-\u26FF]|[\u2700-\u27BF]|'
        r'[\u23E9-\u23F3]|[\u23F8-\u23FA]|[\u25AA-\u25AB]|'
        r'[\u25B6]|[\u25C0]|[\u25FB-\u25FE]|[\u2614-\u2615]|'
        r'[\u2648-\u2653]|[\u267F]|[\u2693]|[\u26A1]|[\u26AA-\u26AB]|'
        r'[\u26BD-\u26BE]|[\u26C4-\u26C5]|[\u26CE]|[\u26D4]|'
        r'[\u26EA]|[\u26F2-\u26F3]|[\u26F5]|[\u26FA]|[\u26FD]|'
        r'[\u2702]|[\u2705]|[\u2708-\u270D]|[\u270F]|[\u2712]|'
        r'[\u2714]|[\u2716]|[\u271D]|[\u2721]|[\u2728]|[\u2733-\u2734]|'
        r'[\u2744]|[\u2747]|[\u274C]|[\u274E]|[\u2753-\u2755]|'
        r'[\u2757]|[\u2763-\u2764]|[\u2795-\u2797]|[\u27A1]|[\u27B0]|'
        r'[\u27BF]|[\u2934-\u2935]|[\u2B05-\u2B07]|[\u2B1B-\u2B1C]|'
        r'[\u2B50]|[\u2B55]|[\u3030]|[\u303D]|[\u3297]|[\u3299]|'
        r'[\U0001F004]|[\U0001F0CF]|[\U0001F170-\U0001F171]|'
        r'[\U0001F17E-\U0001F17F]|[\U0001F18E]|[\U0001F191-\U0001F19A]|'
        r'[\U0001F1E0-\U0001F1FF]|✓|✅|⚠|⚡|🔴|🟢|🔵|🟡|•|·',
        '', text
    )

    # 7. Strip lines that look like table rows, status lines, or raw data
    lines = text.split('\n')
    spoken_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip pure table rows (|...|...|)
        if re.match(r'^\|.+\|', line):
            continue
        # Skip lines that are mostly dashes (table separators)
        if re.match(r'^[-=|+\s]{3,}$', line):
            continue
        # Skip lines that look like "Key: value" system telemetry (short label: data)
        if re.match(r'^[A-Za-z ]{2,25}:\s+[\d.]+', line) and len(line) < 60:
            continue
        # Skip bullet-list lines (-, *, •)
        if re.match(r'^[-*•]\s+', line):
            # Extract the content after the bullet
            content = re.sub(r'^[-*•]\s+', '', line).strip()
            if content:
                spoken_lines.append(content)
            continue
        spoken_lines.append(line)

    text = ' '.join(spoken_lines)

    # 8. Collapse multiple spaces/newlines
    text = re.sub(r'\s{2,}', ' ', text).strip()

    # 9. Remove residual special chars (except common punctuation)
    text = re.sub(r'[^\w\s.,!?;:\'"()\-]', '', text)

    # 10. Trim to ~400 chars so TTS stays conversational, not a wall of text
    if len(text) > 400:
        # Cut at last sentence boundary before 400 chars
        cut = text[:400]
        last_period = max(cut.rfind('.'), cut.rfind('!'), cut.rfind('?'))
        if last_period > 100:
            text = cut[:last_period + 1]
        else:
            text = cut.rsplit(' ', 1)[0] + '.'

    return text.strip()

# Global references (set by main.py)
_brain: JarvisBrain = None
_dispatcher: Dispatcher = None
_voice = None

from pathlib import Path
_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
app = Flask(
    __name__,
    template_folder=str(_WEB_DIR / "templates"),
    static_folder=str(_WEB_DIR / "static")
)
app.config["SECRET_KEY"] = "jarvis-secret-42"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


def init_web(brain: JarvisBrain, dispatcher: Dispatcher, voice=None):
    """Initialize the web server with JARVIS components."""
    global _brain, _dispatcher, _voice
    _brain = brain
    _dispatcher = dispatcher
    _voice = voice


@app.route("/")
def index():
    """Serve the main web interface."""
    return render_template("index.html", jarvis_name=JARVIS_NAME, owner_name=OWNER_NAME)


@app.route("/api/chat", methods=["POST"])
def chat():
    """HTTP endpoint for chat (non-WebSocket)."""
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    try:
        intent = IntentParser.parse(user_input)
        response = _dispatcher.dispatch(intent)
        return jsonify({
            "response": response,
            "intent": intent.action,
        })
    except Exception as e:
        log.error("Web chat error: %s", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/status")
def status():
    """Return JARVIS system status with structured metrics."""
    from skills.system_skills import SystemSkills
    metrics = SystemSkills.get_system_metrics()
    return jsonify({
        "online": True,
        "name": JARVIS_NAME,
        "owner": OWNER_NAME,
        "model": "Gemini 3.5 Flash Lite",
        "metrics": metrics,
        # keep 'system' string for backward compat with chat skill
        "system": SystemSkills.get_system_info(),
    })


@app.route("/api/history")
def history():
    """Return conversation history."""
    return jsonify({"history": _brain.get_history()})


@app.route("/api/tasks")
def tasks():
    """Return task list."""
    return jsonify({"tasks": _dispatcher.tasks.tasks})


@app.route("/api/terminal", methods=["POST"])
def terminal():
    """Execute a shell command and return structured output."""
    data = request.get_json()
    command = (data.get("command") or "").strip()
    cwd = data.get("cwd", None)

    if not command:
        return jsonify({"error": "No command provided"}), 400

    from skills.system_skills import SystemSkills
    result = SystemSkills.run_terminal_command(command, cwd=cwd)
    return jsonify(result)


@app.route("/api/location", methods=["GET", "POST"])
def location():
    """Return or update the user's detected location via IP or GPS geolocation."""
    from skills.web_skills import WebSkills
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        lat = data.get("lat")
        lon = data.get("lon")
        city = data.get("city")
        if lat is not None and lon is not None:
            res = WebSkills.update_gps_location(float(lat), float(lon))
            return jsonify(res)
        elif city:
            res = WebSkills.set_custom_location(str(city))
            return jsonify({"ok": True, "message": res, "location": WebSkills.get_location()})
    loc = WebSkills.get_location()
    return jsonify(loc)


@app.route("/api/screenshot", methods=["GET", "POST"])
def screenshot_endpoint():
    """Trigger or upload a screenshot."""
    from skills.system_skills import SystemSkills
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        image_b64 = data.get("image")
        if image_b64:
            # Client provided base64 screenshot from browser
            import base64
            try:
                if "," in image_b64:
                    image_b64 = image_b64.split(",", 1)[1]
                raw_bytes = base64.b64decode(image_b64)
                web_screenshots_dir = Path(__file__).resolve().parent.parent / "web" / "static" / "screenshots"
                web_screenshots_dir.mkdir(parents=True, exist_ok=True)
                latest_path = web_screenshots_dir / "latest.png"
                with open(latest_path, "wb") as f:
                    f.write(raw_bytes)
                return jsonify({"ok": True, "url": "/static/screenshots/latest.png"})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)}), 400

    result = SystemSkills.take_screenshot()
    return jsonify({"result": result, "url": "/static/screenshots/latest.png"})


@app.route("/api/apps")
def list_apps():
    """Return the full installed app catalog (UWP + Win32 Start Menu apps)."""
    from skills.system_skills import SystemSkills
    catalog = SystemSkills.get_app_catalog()
    return jsonify({"apps": catalog, "count": len(catalog)})


@app.route("/api/apps/refresh")
def refresh_apps():
    """Force rebuild of the installed app catalog."""
    from skills.system_skills import SystemSkills
    SystemSkills._catalog_built = False
    catalog = SystemSkills.get_app_catalog()
    return jsonify({"ok": True, "apps": catalog, "count": len(catalog)})








# ─── Active session tracking ──────────────────────────────────────────────────
_active_sid = None

@socketio.on("connect")
def on_connect():
    global _active_sid
    _active_sid = request.sid
    log.info("WebSocket client connected: %s", _active_sid)
    emit("status", {"connected": True, "name": JARVIS_NAME})


@socketio.on("disconnect")
def on_disconnect():
    log.info("WebSocket client disconnected")


@socketio.on("message")
def on_message(data):
    """Handle real-time chat messages via WebSocket."""
    global _active_sid
    user_input = data.get("message", "").strip()
    if not user_input:
        return

    log.info("WebSocket message: %s", user_input)
    sid = request.sid
    _active_sid = sid  # update to latest
    emit("thinking", {"status": True})

    def process():
        response = None
        intent_action = "chat"
        try:
            intent = IntentParser.parse(user_input)
            intent_action = intent.action
            response = _dispatcher.dispatch(intent)
        except Exception as e:
            log.error("WebSocket dispatch error: %s", str(e))
            response = f"I encountered an error, {OWNER_NAME}: {str(e)}"
        finally:
            if response is None:
                response = f"My apologies, {OWNER_NAME}. That request didn't complete. Please try again."
            # spoken = clean natural TTS version; message = full formatted display text
            spoken = to_speech(response)
            target = _active_sid or sid
            if target:
                socketio.emit("response", {"message": response, "spoken": spoken, "intent": intent_action}, to=target)
                socketio.emit("thinking", {"status": False}, to=target)
            else:
                socketio.emit("response", {"message": response, "spoken": spoken, "intent": intent_action})
                socketio.emit("thinking", {"status": False})


    socketio.start_background_task(process)


def run_web(debug: bool = False):
    """Start the Flask-SocketIO web server."""
    from core.config import WEB_HOST as current_host, WEB_PORT as current_port
    log.info("Starting web server at http://%s:%d", current_host, current_port)
    socketio.run(
        app,
        host=current_host,
        port=current_port,
        debug=debug,
        use_reloader=False,
        log_output=False,
        allow_unsafe_werkzeug=True
    )
