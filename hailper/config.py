from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    anthropic_api_key: str = ""
    orange_email: str = ""
    orange_app_password: str = ""
    imap_host: str = "imap.orange.fr"
    imap_port: int = 993
    mail_fetch_count: int = 5
    whisper_model: str = "base"
    trigger_key: str = "KEY_RIGHTCTRL"
    tts_voice: str = "fr_FR-siwis-medium"
    tts_rate: float = 1.0
    model: str = "claude-haiku-4-5-20251001"
    weather_city: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        data: dict = {}
        p = Path(path)
        if p.exists():
            with open(p, "rb") as f:
                data = tomllib.load(f)
        secrets = data.get("secrets", {})
        mail = data.get("mail", {})
        audio = data.get("audio", {})
        general = data.get("general", {})
        weather = data.get("weather", {})

        def pick(env_key: str, value: str) -> str:
            return os.environ.get(env_key, value)

        return cls(
            anthropic_api_key=pick("ANTHROPIC_API_KEY", secrets.get("anthropic_api_key", "")),
            orange_email=pick("ORANGE_EMAIL", secrets.get("orange_email", "")),
            orange_app_password=pick("ORANGE_APP_PASSWORD", secrets.get("orange_app_password", "")),
            imap_host=mail.get("imap_host", "imap.orange.fr"),
            imap_port=int(mail.get("imap_port", 993)),
            mail_fetch_count=int(mail.get("fetch_count", 5)),
            whisper_model=audio.get("whisper_model", "base"),
            trigger_key=audio.get("trigger_key", "KEY_RIGHTCTRL"),
            tts_voice=audio.get("tts_voice", "fr_FR-siwis-medium"),
            tts_rate=float(audio.get("tts_rate", 1.0)),
            model=general.get("model", "claude-haiku-4-5-20251001"),
            weather_city=weather.get("city", ""),
        )
