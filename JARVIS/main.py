"""
JARVIS — Just A Rather Very Intelligent System
Main entry point

Usage:
    python main.py              — Launch full JARVIS (CLI + Web server)
    python main.py --cli        — CLI only
    python main.py --web        — Web server only
    python main.py --no-voice  — Disable voice
    python main.py --setup     — Run first-time setup
"""

import sys
import os
import argparse
import threading
import webbrowser
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_args():
    parser = argparse.ArgumentParser(
        description="JARVIS — Just A Rather Very Intelligent System",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--cli", action="store_true", help="CLI mode only (no web server)")
    parser.add_argument("--web", action="store_true", help="Web server only (no CLI)")
    parser.add_argument("--no-voice", action="store_true", help="Disable voice I/O")
    parser.add_argument("--setup", action="store_true", help="Run first-time setup wizard")
    parser.add_argument("--port", type=int, default=None, help="Web server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()


def run_setup():
    """Interactive first-time setup."""
    print("\n╔══════════════════════════════════════╗")
    print("║     JARVIS — First Time Setup         ║")
    print("╚══════════════════════════════════════╝\n")

    env_path = os.path.join(os.path.dirname(__file__), ".env")

    if os.path.exists(env_path):
        overwrite = input(".env already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            print("Keeping existing .env")
            return

    api_key = input("Enter your Gemini API Key: ").strip()
    owner_name = input("What should JARVIS call you? (default: Sir): ").strip() or "Sir"
    port = input("Web interface port (default: 5000): ").strip() or "5000"
    wolfram = input("WolframAlpha App ID (optional, press Enter to skip): ").strip()
    weather = input("OpenWeatherMap API Key (optional, press Enter to skip): ").strip()

    env_content = f"""GEMINI_API_KEY={api_key}
OWNER_NAME={owner_name}
JARVIS_WEB_PORT={port}
JARVIS_WAKE_WORD=jarvis
JARVIS_VOICE_RATE=175
JARVIS_VOICE_VOLUME=1.0
"""
    if wolfram:
        env_content += f"WOLFRAM_APP_ID={wolfram}\n"
    if weather:
        env_content += f"WEATHER_API_KEY={weather}\n"

    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"\n✅ Setup complete! .env created.")
    print(f"   Run 'python main.py' to start JARVIS.\n")


def check_env():
    """Verify environment configuration."""
    from core.config import GEMINI_API_KEY
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("\n [!] Notice: GEMINI_API_KEY is not yet set in .env.")
        print("     JARVIS will initialize in Local Protocol Mode (diagnostics, apps, HUD, and tasks operational).")
        print("     To activate full neural intelligence, add your free key at https://aistudio.google.com\n")
    return True


def main():
    args = parse_args()

    if args.setup:
        run_setup()
        return

    if not check_env():
        sys.exit(1)

    # Support Render.com / cloud PORT environment variable
    cloud_port = os.environ.get("PORT")
    if cloud_port:
        import core.config as cfg
        cfg.WEB_PORT = int(cloud_port)
        cfg.WEB_HOST = "0.0.0.0"

    # Override port if specified via CLI arg
    if args.port:
        import core.config as cfg
        cfg.WEB_PORT = args.port

    from core.config import WEB_HOST, WEB_PORT, JARVIS_NAME, OWNER_NAME
    from core.brain import JarvisBrain
    from core.voice import VoiceEngine
    from core.dispatcher import Dispatcher
    # Cloud-safe imports (VoiceEngine/CLIInterface are Windows-only)
    try:
        from core.cli import CLIInterface
        _has_cli = True
    except Exception:
        _has_cli = False

    from core.web_server import run_web, init_web
    from core.logger import log

    print(f"\n  Initializing {JARVIS_NAME}...")

    # ── Initialize Core Components ──────────────────────────────
    log.info("Starting JARVIS...")

    brain = JarvisBrain()

    voice = None
    if not args.no_voice and _has_cli:
        try:
            voice = VoiceEngine()
        except Exception as e:
            log.warning("Voice engine failed to initialize: %s", str(e))
            voice = None

    dispatcher = Dispatcher(brain, on_reminder=lambda msg, dt: (
        print(f"\n⏰ REMINDER: {msg}"),
        voice.speak(f"Reminder, {OWNER_NAME}: {msg}") if voice else None
    ))

    # ── Mode Selection ──────────────────────────────────────────
    run_cli = not args.web   # CLI enabled unless --web only
    run_web_server = not args.cli  # Web enabled unless --cli only

    # ── Start Web Server (background thread) ────────────────────
    if run_web_server:
        init_web(brain, dispatcher, voice)
        web_thread = threading.Thread(
            target=run_web,
            kwargs={"debug": args.debug},
            daemon=True,
            name="JARVIS-Web"
        )
        web_thread.start()
        log.info("Web interface: http://%s:%d", WEB_HOST, WEB_PORT)

        if not run_cli:
            # Web-only mode — open browser (skip on cloud where no display is available)
            is_cloud = bool(os.environ.get("PORT") or os.environ.get("RENDER"))
            if not is_cloud:
                time.sleep(1.5)
                webbrowser.open(f"http://{WEB_HOST}:{WEB_PORT}")
            print(f"\n  ULTRON Web Interface: http://{WEB_HOST}:{WEB_PORT}")
            print("  Press Ctrl+C to stop.\n")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n  ULTRON shutting down.")
            return

    # ── Start CLI ───────────────────────────────────────────────
    if run_cli and _has_cli:
        # Open browser alongside CLI
        if run_web_server:
            time.sleep(1.0)  # Wait for web server to start
            webbrowser.open(f"http://{WEB_HOST}:{WEB_PORT}")

        cli = CLIInterface(brain, voice)
        cli.run()

    if voice:
        voice.shutdown()


if __name__ == "__main__":
    main()
