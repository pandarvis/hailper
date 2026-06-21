from __future__ import annotations

import json
import socket
import subprocess
import time
from datetime import datetime
from typing import Optional, Protocol

from .models import Track


def search_youtube(query: str) -> Optional[Track]:
    """Return the top YouTube result for a query, or None. Uses yt-dlp."""
    from yt_dlp import YoutubeDL

    opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "skip_download": True}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
    entries = (info or {}).get("entries") or []
    if not entries:
        return None
    entry = entries[0]
    video_id = entry.get("id")
    if not video_id:
        return None
    return Track(
        title=entry.get("title", query),
        video_id=video_id,
        added_at=datetime.now().isoformat(timespec="seconds"),
    )


class MusicPlayer(Protocol):
    def play(self, query: str) -> Optional[Track]: ...
    def play_track(self, track: Track) -> None: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def stop(self) -> None: ...
    def next(self) -> Optional[Track]: ...
    def set_volume(self, level: int) -> None: ...
    def now_playing(self) -> Optional[Track]: ...


class FakeMusicPlayer:
    """In-memory player for tests and --text dev mode."""

    def __init__(self, search_result: Optional[Track] = None):
        self._search_result = search_result
        self._current: Optional[Track] = None
        self.paused = False
        self.volume = 100

    def play(self, query: str) -> Optional[Track]:
        self._current = self._search_result
        self.paused = False
        return self._current

    def play_track(self, track: Track) -> None:
        self._current = track
        self.paused = False

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def stop(self) -> None:
        self._current = None

    def next(self) -> Optional[Track]:
        self.stop()
        return None

    def set_volume(self, level: int) -> None:
        self.volume = max(0, min(130, level))

    def now_playing(self) -> Optional[Track]:
        return self._current


class MpvPlayer:
    """Controls a background mpv process via its JSON IPC socket (Linux)."""

    def __init__(self, socket_path: str = "/tmp/hailper-mpv.sock"):
        self.socket_path = socket_path
        self._proc: Optional[subprocess.Popen] = None
        self._current: Optional[Track] = None
        self.volume = 100
        self._queue: list[Track] = []
        self._queue_pos = 0

    def _ensure_running(self) -> None:
        if self._proc and self._proc.poll() is None:
            return
        self._proc = subprocess.Popen(
            [
                "mpv", "--idle=yes", "--no-video", "--no-terminal",
                f"--input-ipc-server={self.socket_path}",
                f"--volume={self.volume}",
            ]
        )
        for _ in range(50):  # wait up to 5s for the socket
            try:
                self._command(["get_property", "idle-active"])
                return
            except OSError:
                time.sleep(0.1)

    def _command(self, cmd: list) -> dict:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)  # borne connect/sendall/recv : ne jamais bloquer la boucle
            s.connect(self.socket_path)
            s.sendall((json.dumps({"command": cmd}) + "\n").encode("utf-8"))
            return json.loads(s.recv(65536).decode("utf-8").splitlines()[0])

    def _load(self, track: Track) -> None:
        self._ensure_running()
        url = f"https://www.youtube.com/watch?v={track.video_id}"
        self._command(["loadfile", url, "replace"])
        self._command(["set_property", "pause", False])
        self._current = track

    def play(self, query: str) -> Optional[Track]:
        track = search_youtube(query)
        if track is None:
            return None
        self._queue = [track]
        self._queue_pos = 0
        self._load(track)
        return track

    def play_track(self, track: Track) -> None:
        self._queue = [track]
        self._queue_pos = 0
        self._load(track)

    def play_queue(self, tracks: list[Track]) -> Optional[Track]:
        if not tracks:
            return None
        self._queue = list(tracks)
        self._queue_pos = 0
        self._load(self._queue[0])
        return self._queue[0]

    def pause(self) -> None:
        self._command(["set_property", "pause", True])

    def resume(self) -> None:
        self._command(["set_property", "pause", False])

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._command(["stop"])
        self._current = None

    def next(self) -> Optional[Track]:
        if self._queue_pos + 1 < len(self._queue):
            self._queue_pos += 1
            self._load(self._queue[self._queue_pos])
            return self._current
        self.stop()
        return None

    def set_volume(self, level: int) -> None:
        self.volume = max(0, min(130, level))
        if self._proc and self._proc.poll() is None:
            self._command(["set_property", "volume", self.volume])

    def now_playing(self) -> Optional[Track]:
        return self._current
