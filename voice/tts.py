import os
import threading
import subprocess
from typing import Optional

class TextToSpeech:
    """Local Text-to-Speech engine using pyttsx3 / Windows SAPI5 & PowerShell fallback."""

    def __init__(self, rate: int = 175, volume: float = 1.0):
        self.rate = rate
        self.volume = volume

    def speak(self, text: str, async_speech: bool = True):
        if not text or not text.strip():
            return

        def _speak_worker():
            # Method 1: pyttsx3 (SAPI5 native)
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', self.rate)
                engine.setProperty('volume', self.volume)
                engine.say(text)
                engine.runAndWait()
                return
            except Exception as e:
                pass

            # Method 2: Native Windows PowerShell System.Speech Synthesizer (Built into Windows 10/11)
            try:
                clean_text = text.replace('"', "'").replace('`', "'")
                ps_script = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Rate = 1; $synth.Speak("{clean_text}")'
                subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
            except Exception as e2:
                print(f"[TTS Console Fallback]: {text} (Error: {e2})")

        if async_speech:
            thread = threading.Thread(target=_speak_worker, daemon=True)
            thread.start()
        else:
            _speak_worker()
