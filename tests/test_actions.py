from hailper.actions import Actions
from hailper.favorites import FavoritesStore
from hailper.music import FakeMusicPlayer
from hailper.models import Track, Email

class FakeMail:
    def __init__(self, emails):
        self._emails = emails
    def fetch_recent(self, count):
        return self._emails[:count]

def build(tmp_path, search_result=None, emails=None):
    player = FakeMusicPlayer(search_result=search_result)
    favorites = FavoritesStore(tmp_path / "fav.json")
    mail = FakeMail(emails or [])
    summarize = lambda items: f"Tu as {len(items)} mails."
    return Actions(player, favorites, mail, summarize, fetch_count=5), player, favorites

def test_play_music_found(tmp_path):
    actions, _, _ = build(tmp_path, search_result=Track("Brel", "v1"))
    assert "Brel" in actions.play_music(query="brel")

def test_play_music_not_found(tmp_path):
    actions, _, _ = build(tmp_path, search_result=None)
    assert "trouv" in actions.play_music(query="zzz").lower()

def test_add_favorite_when_playing(tmp_path):
    actions, player, favorites = build(tmp_path, search_result=Track("Brel", "v1"))
    actions.play_music(query="brel")
    msg = actions.add_favorite()
    assert "favoris" in msg.lower()
    assert favorites.contains("v1")

def test_add_favorite_nothing_playing(tmp_path):
    actions, _, _ = build(tmp_path)
    assert "aucune" in actions.add_favorite().lower()

def test_play_favorites_empty(tmp_path):
    actions, _, _ = build(tmp_path)
    assert "aucun" in actions.play_favorites().lower()

def test_control_playback_actions(tmp_path):
    actions, player, _ = build(tmp_path, search_result=Track("Brel", "v1"))
    actions.play_music(query="brel")
    assert "pause" in actions.control_playback(action="pause").lower()
    assert player.paused is True
    actions.control_playback(action="volume_up")
    assert player.volume == 110

def test_read_recent_emails(tmp_path):
    emails = [Email(1, "EDF", "Facture", "2026-06-20", "corps")]
    actions, _, _ = build(tmp_path, emails=emails)
    assert "1 mails" in actions.read_recent_emails()

def test_read_email_full_requires_prior_list(tmp_path):
    emails = [Email(1, "EDF", "Facture", "2026-06-20", "Le corps complet")]
    actions, _, _ = build(tmp_path, emails=emails)
    actions.read_recent_emails()
    out = actions.read_email_full(index=1)
    assert "Le corps complet" in out
    assert "EDF" in out
