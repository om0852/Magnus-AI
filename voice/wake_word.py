import time
import threading
import re
from typing import Callable, Optional
from voice.stt import SpeechToText
from voice.tts import TextToSpeech

WAKE_WORDS = ["hey magnas", "hey magnus", "hi magnas", "hi magnus", "magnas", "magnus", "ok magnas"]

class WakeWordListener:
    """
    Continuous background Wake-Word detector for Magnas AI.
    Listens for 'Hey Magnas' wake trigger and executes speech commands instantly.
    """

    def __init__(self, on_command_callback: Optional[Callable[[str], None]] = None):
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.on_command_callback = on_command_callback
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.last_command: Optional[str] = None
        self.activation_count = 0

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("[WakeWord] Continuous 'Hey Magnas' listener initialized.")

    def stop(self):
        self.is_running = False
        print("[WakeWord] Listener stopped.")

    def _listen_loop(self):
        consecutive_nones = 0
        while self.is_running:
            try:
                raw_speech = self.stt.listen_microphone(timeout=3)
                if not raw_speech:
                    consecutive_nones += 1
                    sleep_time = 0.5 if consecutive_nones > 3 else 0.1
                    time.sleep(sleep_time)
                    continue

                consecutive_nones = 0
                raw_speech_clean = raw_speech.lower().strip()
                print(f"[WakeWord Heard]: {raw_speech_clean}")

                wake_found = False
                detected_command = ""

                for wake in WAKE_WORDS:
                    if wake in raw_speech_clean:
                        wake_found = True
                        idx = raw_speech_clean.find(wake)
                        after_wake = raw_speech_clean[idx + len(wake):].strip()
                        after_wake = re.sub(r'^[,\.\?\!\s]+', '', after_wake)
                        if after_wake:
                            detected_command = after_wake
                        break

                if wake_found:
                    self.activation_count += 1
                    print(f"[WakeWord Triggered!] Command: '{detected_command or raw_speech_clean}'")
                    
                    if not detected_command:
                        detected_command = raw_speech_clean

                    self.last_command = detected_command
                    if self.on_command_callback:
                        self.on_command_callback(detected_command)

                # Even if wake word was not in speech, if a command is heard directly while active, pass it
                elif raw_speech_clean and len(raw_speech_clean) > 3:
                    print(f"[Voice Direct Command]: '{raw_speech_clean}'")
                    self.last_command = raw_speech_clean
                    if self.on_command_callback:
                        self.on_command_callback(raw_speech_clean)

            except Exception as e:
                time.sleep(0.5)

    def process_text_for_wake_word(self, text: str) -> Optional[str]:
        """Utility to parse text input for wake word presence."""
        text_lower = text.lower().strip()
        for wake in WAKE_WORDS:
            if wake in text_lower:
                idx = text_lower.find(wake)
                after = text_lower[idx + len(wake):].strip()
                return re.sub(r'^[,\.\?\!\s]+', '', after) or text
        return text
