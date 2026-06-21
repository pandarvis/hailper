from __future__ import annotations

import os
import subprocess
import sys
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
        try:
            subprocess.run(
                [self._piper_bin(), "--model", self.voice,
                 "--length_scale", str(length_scale), "--output_file", wav_path],
                input=text.encode("utf-8"),
                check=True,
            )
            subprocess.run(["aplay", "-q", wav_path], check=False)
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                pass

    @staticmethod
    def _piper_bin() -> str:
        # piper-tts is installed in the venv; a bare "piper" may not be on PATH
        # when launched via the venv's python (e.g. from systemd).
        venv_piper = os.path.join(sys.prefix, "bin", "piper")
        return venv_piper if os.path.exists(venv_piper) else "piper"

    def earcon(self, name: str) -> None:
        wav = self.sounds_dir / f"{name}.wav"
        if wav.exists():
            subprocess.run(["aplay", "-q", str(wav)], check=False)
