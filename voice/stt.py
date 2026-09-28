import os
import tempfile
import time
from typing import Optional, Dict, Any

class SpeechToText:
    """Fast Low-Latency Speech-to-Text engine for Magnas voice control."""

    def __init__(self, engine: str = "google"):
        self.engine = engine
        self._mic_error_logged = False

    def is_microphone_available(self) -> bool:
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devs = [d for d in devices if d.get('max_input_channels', 0) > 0]
            if input_devs:
                return True
        except Exception:
            pass

        try:
            import speech_recognition as sr
            with sr.Microphone() as source:
                pass
            return True
        except Exception:
            return False

    def transcribe_audio_bytes(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """Transcribe raw audio bytes from web sockets or API uploads."""
        try:
            import speech_recognition as sr
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                r = sr.Recognizer()
                with sr.AudioFile(tmp_path) as source:
                    audio_data = r.record(source)
                    text = r.recognize_google(audio_data)
                    return text
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            return f"[STT Error: {e}]"

    def transcribe_audio_file(self, audio_path: str) -> str:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                return text
        except Exception as e:
            return f"[STT Error: {e}]"

    def listen_microphone(self, timeout: int = 3, phrase_limit: int = 6) -> Optional[str]:
        # Strategy 1: Try PyAudio via speech_recognition
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            r.energy_threshold = 300
            r.dynamic_energy_threshold = True

            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                text = r.recognize_google(audio)
                return text
        except Exception:
            pass

        # Strategy 2: Ultra-Fast SoundDevice Streaming VAD (0.4s silence cutoff)
        try:
            import sounddevice as sd
            import numpy as np
            import scipy.io.wavfile as wav
            import speech_recognition as sr

            fs = 16000
            chunks = []
            silent_chunks = 0
            speech_started = False

            def audio_callback(indata, frames, time_info, status):
                nonlocal silent_chunks, speech_started
                volume_norm = float(np.linalg.norm(indata))
                if volume_norm > 80.0:  # Active speech energy
                    speech_started = True
                    silent_chunks = 0
                    chunks.append(indata.copy())
                elif speech_started:
                    silent_chunks += 1
                    chunks.append(indata.copy())

            start_time = time.time()
            with sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=audio_callback):
                while time.time() - start_time < timeout:
                    time.sleep(0.05)
                    # Once speech is detected and 400ms silence occurs, stop recording immediately!
                    if speech_started and silent_chunks >= 4:
                        break

            if not chunks:
                return None

            recording = np.concatenate(chunks, axis=0)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav.write(tmp.name, fs, recording)
                tmp_path = tmp.name

            try:
                r = sr.Recognizer()
                with sr.AudioFile(tmp_path) as source:
                    audio_data = r.record(source)
                    text = r.recognize_google(audio_data)
                    if text and text.strip():
                        return text.strip()
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as sd_err:
            if not self._mic_error_logged:
                print(f"[STT Native Mic Note] Streaming VAD fallback active: {sd_err}")
                self._mic_error_logged = True
        return None
