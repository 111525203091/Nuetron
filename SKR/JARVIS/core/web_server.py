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
    """Return JARVIS system status."""
    from skills.system_skills import SystemSkills
    return jsonify({
        "online": True,
        "name": JARVIS_NAME,
        "owner": OWNER_NAME,
        "model": "Gemini 2.0 Flash",
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


# ─── WebSocket Events ─────────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    log.info("WebSocket client connected")
    emit("status", {"connected": True, "name": JARVIS_NAME})


@socketio.on("disconnect")
def on_disconnect():
    log.info("WebSocket client disconnected")


@socketio.on("message")
def on_message(data):
    """Handle real-time chat messages via WebSocket."""
    user_input = data.get("message", "").strip()
    if not user_input:
        return

    log.info("WebSocket message: %s", user_input)
    emit("thinking", {"status": True})

    def process():
        try:
            intent = IntentParser.parse(user_input)
            response = _dispatcher.dispatch(intent)

            socketio.emit("response", {
                "message": response,
                "intent": intent.action,
            })

            # Also speak if voice available
            if _voice and _voice.tts_available:
                _voice.speak(response)

        except Exception as e:
            log.error("WebSocket handler error: %s", str(e))
            socketio.emit("error", {"message": str(e)})
        finally:
            socketio.emit("thinking", {"status": False})

    thread = threading.Thread(target=process, daemon=True)
    thread.start()


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
