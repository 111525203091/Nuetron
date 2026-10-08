"""
JARVIS Voice Engine — Text-to-Speech and Speech-to-Text
"""

import threading
import queue
import time
from typing import Optional

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    sr = None
    SR_AVAILABLE = False

from core.config import VOICE_RATE, VOICE_VOLUME, VOICE_INDEX, WAKE_WORD, OWNER_NAME
from core.logger import log


class VoiceEngine:
    """Handles all voice I/O for JARVIS."""

    def __init__(self):
        self._init_tts()
        self._init_stt()
        self._speech_queue = queue.Queue()
        self._speaking = False
        self._tts_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self._tts_thread.start()
        log.info("Voice engine initialized.")

    def _init_tts(self):
        """Initialize text-to-speech engine with natural cadence."""
        try:
            self.tts = pyttsx3.init()
            # 165-170 WPM produces the most natural conversational human cadence
            natural_rate = min(175, max(155, VOICE_RATE))
            self.tts.setProperty("rate", natural_rate)
            self.tts.setProperty("volume", VOICE_VOLUME)

            voices = self.tts.getProperty("voices")
            if voices:
                selected_voice = None
                # Prioritize natural/online sounding voice if installed
                for v in voices:
                    name = v.name.lower()
                    if "natural" in name or "george" in name or "hazel" in name or "david" in name:
                        selected_voice = v.id
                        break
                if not selected_voice and len(voices) > VOICE_INDEX:
                    selected_voice = voices[VOICE_INDEX].id

                if selected_voice:
                    self.tts.setProperty("voice", selected_voice)

            self.tts_available = True
            log.info("TTS initialized with %d voices available.", len(voices or []))
        except Exception as e:
            log.warning("TTS unavailable: %s", str(e))
            self.tts_available = False

    def _init_stt(self):
        """Initialize speech recognition."""
        if not SR_AVAILABLE:
            log.warning("STT unavailable: speech_recognition package not installed.")
            self.mic_available = False
            return
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.mic_available = True
            log.info("STT (speech recognition) initialized.")
        except Exception as e:
            log.warning("STT unavailable: %s", str(e))
            self.mic_available = False

    def _speech_worker(self):
        """Background worker that processes the speech queue sequentially."""
        while True:
            text = self._speech_queue.get()
            if text is None:
                break
            self._speak_now(text)
            self._speech_queue.task_done()

    def _speak_now(self, text: str):
        """Actually speak the text (runs in TTS thread)."""
        if not self.tts_available:
            print(f"[JARVIS]: {text}")
            return
        try:
            self._speaking = True
            self.tts.say(text)
            self.tts.runAndWait()
        except Exception as e:
            log.error("TTS error: %s", str(e))
        finally:
            self._speaking = False

    def speak(self, text: str, interrupt: bool = False):
        """
        Queue text for speaking.
        
        Args:
            text: Text to speak
            interrupt: If True, clear queue and speak immediately
        """
        if interrupt:
            while not self._speech_queue.empty():
                try:
                    self._speech_queue.get_nowait()
                    self._speech_queue.task_done()
                except queue.Empty:
                    break
        self._speech_queue.put(text)

    def listen(self, timeout: int = 10, phrase_limit: int = 15) -> Optional[str]:
        """
        Listen for voice input and return transcribed text.
        
        Args:
            timeout: Seconds to wait for speech to start
            phrase_limit: Maximum seconds of speech to record
        
        Returns:
            Transcribed text or None if failed
        """
        if not self.mic_available:
            log.warning("Microphone not available.")
            return None

        try:
            with sr.Microphone() as source:
                log.info("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )

            text = self.recognizer.recognize_google(audio)
            log.info("Heard: %s", text)
            return text.lower()

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            log.error("STT request error: %s", str(e))
            return None
        except Exception as e:
            log.error("Unexpected STT error: %s", str(e))
            return None

    def wait_for_wake_word(self, callback=None) -> bool:
        """
        Continuously listen for the wake word.
        
        Args:
            callback: Optional function to call when wake word detected
        
        Returns:
            True if wake word detected
        """
        log.info("Waiting for wake word: '%s'", WAKE_WORD)
        text = self.listen(timeout=5, phrase_limit=5)
        if text and WAKE_WORD in text.lower():
            log.info("Wake word detected!")
            if callback:
                callback()
            return True
        return False

    def is_speaking(self) -> bool:
        """Return True if JARVIS is currently speaking."""
        return self._speaking or not self._speech_queue.empty()

    def stop_speaking(self):
        """Stop current speech."""
        try:
            if self.tts_available:
                self.tts.stop()
        except Exception:
            pass

    def shutdown(self):
        """Clean up voice engine resources."""
        self._speech_queue.put(None)
        self._tts_thread.join(timeout=2)
