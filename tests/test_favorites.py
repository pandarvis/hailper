from hailper.favorites import FavoritesStore
from hailper.models import Track

def make_store(tmp_path):
    return FavoritesStore(tmp_path / "favorites.json")

def test_add_and_list(tmp_path):
    s = make_store(tmp_path)
    assert s.add(Track("Song A", "id1", "2026-06-21")) is True
    assert s.add(Track("Song B", "id2", "2026-06-21")) is True
    titles = [t.title for t in s.list()]
    assert titles == ["Song A", "Song B"]

def test_add_duplicate_is_rejected(tmp_path):
    s = make_store(tmp_path)
    assert s.add(Track("Song A", "id1")) is True
    assert s.add(Track("Song A", "id1")) is False
    assert len(s.list()) == 1

def test_remove(tmp_path):
    s = make_store(tmp_path)
    s.add(Track("Song A", "id1"))
    s.add(Track("Song B", "id2"))
    assert s.remove("id1") is True
    assert [t.video_id for t in s.list()] == ["id2"]
    assert s.remove("missing") is False

def test_contains(tmp_path):
    s = make_store(tmp_path)
    s.add(Track("Song A", "id1"))
    assert s.contains("id1") is True
    assert s.contains("id2") is False

def test_persists_across_instances(tmp_path):
    make_store(tmp_path).add(Track("Song A", "id1"))
    assert [t.video_id for t in make_store(tmp_path).list()] == ["id1"]

def test_empty_when_no_file(tmp_path):
    assert make_store(tmp_path).list() == []
