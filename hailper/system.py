from __future__ import annotations

import subprocess
from datetime import datetime
from typing import Callable, Optional

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

# Une confirmation d'action destructrice (extinction/redémarrage) expire après
# ce délai, pour qu'un « oui » sans rapport prononcé plus tard ne déclenche rien.
PENDING_TTL_SECONDS = 30


def _default_fetch_weather(city: str) -> str:
    import urllib.parse
    import urllib.request

    loc = urllib.parse.quote(city) if city else ""
    url = f"https://wttr.in/{loc}?format=%C+%t&lang=fr"
    with urllib.request.urlopen(url, timeout=8) as resp:
        text = resp.read().decode("utf-8").strip()
    where = f" à {city}" if city else ""
    return f"Météo{where} : {text}."


class SystemControl:
    """Safe, voice-driven system actions. Each method does one well-defined
    thing; destructive actions (power) require explicit confirmation."""

    def __init__(
        self,
        weather_city: str = "",
        clock: Callable[[], datetime] = datetime.now,
        runner: Callable = subprocess.run,
        spawner: Callable = subprocess.Popen,
        fetch_weather: Optional[Callable[[str], str]] = None,
    ):
        self.weather_city = weather_city
        self._clock = clock
        self._run = runner
        self._spawn = spawner
        self._fetch_weather = fetch_weather or _default_fetch_weather
        self._pending: Optional[str] = None  # "shutdown" | "reboot"
        self._pending_at: Optional[datetime] = None

    def get_datetime(self) -> str:
        now = self._clock()
        jour = JOURS[now.weekday()]
        return (
            f"Il est {now.hour} heures {now.minute:02d}. "
            f"Nous sommes le {jour} {now.day} {MOIS[now.month - 1]} {now.year}."
        )

    def power_control(self, action: str) -> str:
        if action not in ("shutdown", "reboot"):
            return "Je ne sais pas faire ça."
        self._pending = action
        self._pending_at = self._clock()
        verbe = "éteindre" if action == "shutdown" else "redémarrer"
        return f"Veux-tu vraiment {verbe} l'ordinateur ? Dis oui pour confirmer."

    def confirm(self) -> str:
        if self._pending is None:
            return "Il n'y a rien à confirmer."
        elapsed = (self._clock() - self._pending_at).total_seconds()
        if elapsed > PENDING_TTL_SECONDS:
            self._pending = None
            self._pending_at = None
            return "C'est trop tard, j'annule par sécurité. Redemande si besoin."
        action = self._pending
        self._pending = None
        self._pending_at = None
        cmd = ["systemctl", "poweroff"] if action == "shutdown" else ["systemctl", "reboot"]
        self._run(cmd, check=False)
        return "D'accord, j'éteins." if action == "shutdown" else "D'accord, je redémarre."

    def cancel(self) -> str:
        if self._pending is None:
            return "Il n'y a rien à annuler."
        self._pending = None
        self._pending_at = None
        return "D'accord, j'annule."

    def system_volume(self, action: str) -> str:
        if action == "up":
            self._run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"], check=False)
            return "Plus fort."
        if action == "down":
            self._run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"], check=False)
            return "Moins fort."
        return "Je n'ai pas compris pour le volume."

    def restart_assistant(self) -> str:
        # Speak first, then restart shortly after (detached so it survives our exit).
        self._spawn(
            ["bash", "-c", "sleep 5 && systemctl --user restart hailper"],
            start_new_session=True,
        )
        return "Je redémarre, un instant."

    def get_weather(self) -> str:
        try:
            return self._fetch_weather(self.weather_city)
        except Exception:
            return "Je n'arrive pas à avoir la météo pour le moment."
