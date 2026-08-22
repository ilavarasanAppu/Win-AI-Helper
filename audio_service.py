import os
import wave
import tempfile
import threading
import time

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    sd = None
    np = None


class AudioService:
    """Speech-to-text (faster-whisper) + Text-to-speech (pyttsx3)."""

    def __init__(self, whisper_size: str = "base"):
        self.whisper_size = whisper_size
        self._is_recording = False
        self._audio_frames = []
        self._sample_rate = 16000
        self._stt_model = None

    # ── Text-to-Speech (non-blocking) ────────────────────────
    def speak(self, text: str):
        """Non-blocking TTS playback supporting English & Tamil."""
        if not text or not text.strip():
            return

        def _run_tts():
            # Check for Tamil or Unicode characters
            has_tamil = any(0x0B80 <= ord(c) <= 0x0BFF for c in text)
            is_unicode = any(ord(c) > 127 for c in text)

            if has_tamil or is_unicode:
                try:
                    import urllib.request
                    import urllib.parse
                    import subprocess

                    lang = "ta" if has_tamil else "en"
                    # Split into chunks of max 150 chars for Google TTS
                    chunks = [text[i:i+150] for i in range(0, len(text), 150)][:3]
                    for chunk in chunks:
                        encoded = urllib.parse.quote(chunk.strip())
                        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl={lang}&client=tw-ob"
                        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                        
                        temp_path = os.path.join(tempfile.gettempdir(), f"tts_{int(time.time()*1000)}.mp3")
                        with urllib.request.urlopen(req, timeout=8) as resp:
                            with open(temp_path, "wb") as f:
                                f.write(resp.read())

                        ps_script = f'Add-Type -AssemblyName presentationCore; $p = New-Object System.Windows.Media.MediaPlayer; $p.Open("{temp_path}"); $p.Play(); Start-Sleep -s 4'
                        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)

                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass
                    return
                except Exception as e:
                    print(f"Online TTS error: {e}")

            # Native SAPI fallback for standard English text
            if pyttsx3 is not None:
                try:
                    engine = pyttsx3.init()
                    rate = int(os.environ.get("TTS_RATE", 180))
                    engine.setProperty("rate", rate)
                    engine.setProperty("volume", 1.0)
                    engine.say(text)
                    engine.runAndWait()
                    time.sleep(0.2)
                except Exception:
                    pass

        t = threading.Thread(target=_run_tts, daemon=True)
        t.start()

    # ── Speech-to-Text (on-demand whisper) ───────────────────
    def start_recording(self):
        """Start recording from default microphone."""
        if not sd or not np:
            return False
        self._is_recording = True
        self._audio_frames = []

        def callback(indata, frames, time_info, status):
            if self._is_recording:
                self._audio_frames.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype="int16",
            callback=callback
        )
        self.stream.start()
        return True

    def stop_and_transcribe(self) -> str:
        """Stop recording and transcribe via faster-whisper."""
        self._is_recording = False
        if hasattr(self, "stream"):
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass

        if not self._audio_frames:
            return ""

        audio_data = np.concatenate(self._audio_frames, axis=0)
        temp_wav_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

        try:
            with wave.open(temp_wav_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self._sample_rate)
                wf.writeframes(audio_data.tobytes())

            # Lazy load whisper model on first use
            if self._stt_model is None:
                try:
                    from faster_whisper import WhisperModel
                    self._stt_model = WhisperModel(
                        self.whisper_size, device="cpu", compute_type="int8"
                    )
                except Exception as e:
                    return f"[Whisper model error: {str(e)}]"

            # High-accuracy transcription with VAD filtering to prevent noise hallucinations
            segments, _ = self._stt_model.transcribe(
                temp_wav_path,
                beam_size=5,
                vad_filter=True,
                initial_prompt="Clear spoken audio transcription in English, Tamil, or Tanglish."
            )
            transcription = " ".join([seg.text for seg in segments]).strip()
            return transcription
        except Exception as e:
            return f"[Transcription error: {str(e)}]"
        finally:
            if os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except Exception:
                    pass

    def stop_recording(self):
        """Stop recording without transcribing."""
        self._is_recording = False
        if hasattr(self, "stream"):
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass