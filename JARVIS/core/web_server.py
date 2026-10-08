"""
JARVIS Web Server — Flask + SocketIO web interface backend
"""

import threading
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from core.config import WEB_HOST, WEB_PORT, JARVIS_NAME, OWNER_NAME
from core.brain import JarvisBrain
from core.intent_parser import IntentParser
from core.dispatcher import Dispatcher
from core.logger import log

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
            target = _active_sid or sid
            if target:
                socketio.emit("response", {"message": response, "intent": intent_action}, to=target)
                socketio.emit("thinking", {"status": False}, to=target)
            else:
                socketio.emit("response", {"message": response, "intent": intent_action})
                socketio.emit("thinking", {"status": False})


    socketio.start_background_task(process)


def run_web(debug: bool = False):
    """Start the Flask-SocketIO web server."""
    log.info("Starting web server at http://%s:%d", WEB_HOST, WEB_PORT)
    socketio.run(
        app,
        host=WEB_HOST,
        port=WEB_PORT,
        debug=debug,
        use_reloader=False,
        log_output=False,
        allow_unsafe_werkzeug=True
    )
