from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Protocol


class Speaker(Protocol):
    def say(self, text: str) -> None: ...
    def earcon(self, name: str) -> None: ...


class ConsoleSpeaker:
    """Prints instead of speaking — for tests and --text dev mode."""

    def __init__(self):
        self.spoken: list[str] = []

    def say(self, text: str) -> None:
        self.spoken.append(text)
        print(f"[VOIX] {text}")

    def earcon(self, name: str) -> None:
        print(f"[SON:{name}]")


class PiperSpeaker:
    """Synthesizes French speech with Piper and plays it (Linux)."""

    def __init__(self, voice: str, rate: float = 1.0, sounds_dir: str = "sounds"):
        self.voice = voice
        self.rate = rate
        self.sounds_dir = Path(sounds_dir)

    def say(self, text: str) -> None:
        if not text:
            return
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        # length-scale > 1.0 slows speech down (clearer for hard-of-hearing).
        length_scale = 1.0 / self.rate if self.rate else 1.0
        subprocess.run(
            ["piper", "--model", self.voice, "--length_scale", str(length_scale),
             "--output_file", wav_path],
            input=text.encode("utf-8"),
            check=True,
        )
        subprocess.run(["aplay", "-q", wav_path], check=False)

    def earcon(self, name: str) -> None:
        wav = self.sounds_dir / f"{name}.wav"
        if wav.exists():
            subprocess.run(["aplay", "-q", str(wav)], check=False)
