from __future__ import annotations

from typing import Protocol


class Recognizer(Protocol):
    def listen(self) -> str: ...


class ConsoleRecognizer:
    """Reads typed input — for tests and --text dev mode."""

    def listen(self) -> str:
        return input("Tu> ").strip()


class WhisperRecognizer:
    """Records the mic and transcribes French with faster-whisper (resident model)."""

    def __init__(self, model_size: str = "base"):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def listen(self) -> str:
        import numpy as np

        from .audio import SAMPLE_RATE, record_until_silence

        pcm = record_until_silence()
        if not pcm:
            return ""
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(audio, language="fr", beam_size=1)
        return " ".join(seg.text for seg in segments).strip()
