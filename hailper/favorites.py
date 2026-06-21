from __future__ import annotations

import json
from pathlib import Path

from .models import Track


class FavoritesStore:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, items: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def list(self) -> list[Track]:
        return [Track(**item) for item in self._read()]

    def contains(self, video_id: str) -> bool:
        return any(item["video_id"] == video_id for item in self._read())

    def add(self, track: Track) -> bool:
        items = self._read()
        if any(item["video_id"] == track.video_id for item in items):
            return False
        items.append(
            {"title": track.title, "video_id": track.video_id, "added_at": track.added_at}
        )
        self._write(items)
        return True

    def remove(self, video_id: str) -> bool:
        items = self._read()
        remaining = [item for item in items if item["video_id"] != video_id]
        if len(remaining) == len(items):
            return False
        self._write(remaining)
        return True
