from __future__ import annotations

from typing import Callable, Optional

from .favorites import FavoritesStore
from .models import Email, Track


class Actions:
    def __init__(
        self,
        player,
        favorites: FavoritesStore,
        mail_reader,
        summarize_emails: Callable[[list[Email]], str],
        fetch_count: int = 5,
    ):
        self.player = player
        self.favorites = favorites
        self.mail_reader = mail_reader
        self.summarize_emails = summarize_emails
        self.fetch_count = fetch_count
        self._last_emails: list[Email] = []

    # --- voix ---
    def say(self, text: str) -> str:
        return text

    # --- music ---
    def play_music(self, query: str) -> str:
        track = self.player.play(query)
        if track is None:
            return "Je n'ai pas trouvé cette musique."
        return f"Je lance {track.title}."

    def control_playback(self, action: str) -> str:
        if action == "pause":
            self.player.pause()
            return "Pause."
        if action == "resume":
            self.player.resume()
            return "Je reprends."
        if action == "stop":
            self.player.stop()
            return "J'arrête la musique."
        if action == "next":
            track = self.player.next()
            return f"Suivant : {track.title}." if track else "Il n'y a pas de suivante."
        return "Je n'ai pas compris la commande de lecture."

    # --- favorites ---
    def add_favorite(self) -> str:
        track = self.player.now_playing()
        if track is None:
            return "Aucune musique en cours."
        added = self.favorites.add(track)
        return "C'est ajouté à tes favoris." if added else "C'est déjà dans tes favoris."

    def remove_favorite(self) -> str:
        track = self.player.now_playing()
        if track is None:
            return "Aucune musique en cours."
        removed = self.favorites.remove(track.video_id)
        return "C'est retiré de tes favoris." if removed else "Ce n'était pas dans tes favoris."

    def list_favorites(self) -> str:
        favs = self.favorites.list()
        if not favs:
            return "Tu n'as aucun favori pour l'instant."
        titles = ", ".join(t.title for t in favs)
        return f"Tu as {len(favs)} favoris : {titles}."

    def play_favorites(self) -> str:
        favs = self.favorites.list()
        if not favs:
            return "Tu n'as aucun favori à jouer."
        if hasattr(self.player, "play_queue"):
            self.player.play_queue(favs)
        else:
            self.player.play_track(favs[0])
        return f"Je joue tes {len(favs)} favoris."

    # --- mail ---
    def read_recent_emails(self, count: Optional[int] = None) -> str:
        emails = self.mail_reader.fetch_recent(count or self.fetch_count)
        self._last_emails = emails
        if not emails:
            return "Tu n'as aucun nouveau mail."
        return self.summarize_emails(emails)

    def read_email_full(self, index: int) -> str:
        match = next((e for e in self._last_emails if e.index == index), None)
        if match is None:
            return "Je n'ai pas ce mail. Demande d'abord le récap des mails."
        return f"Mail de {match.sender}, sujet : {match.subject}. {match.body}"


class Toolbox:
    """Aggregates several tool providers; the brain dispatches by method name."""

    def __init__(self, *providers):
        self._providers = providers

    def __getattr__(self, name):
        for provider in self._providers:
            fn = getattr(provider, name, None)
            if fn is not None:
                return fn
        raise AttributeError(name)
