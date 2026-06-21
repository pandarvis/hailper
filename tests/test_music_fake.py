from hailper.music import FakeMusicPlayer
from hailper.models import Track

def test_play_sets_now_playing():
    p = FakeMusicPlayer(search_result=Track("Sardou", "vid1"))
    track = p.play("sardou maladie d'amour")
    assert track.title == "Sardou"
    assert p.now_playing().video_id == "vid1"

def test_play_no_result():
    p = FakeMusicPlayer(search_result=None)
    assert p.play("zzz") is None
    assert p.now_playing() is None

def test_pause_resume_stop():
    p = FakeMusicPlayer(search_result=Track("A", "v"))
    p.play("a")
    p.pause(); assert p.paused is True
    p.resume(); assert p.paused is False
    p.stop(); assert p.now_playing() is None

def test_volume_clamped():
    p = FakeMusicPlayer(search_result=Track("A", "v"))
    p.set_volume(200)
    assert p.volume == 130
    p.set_volume(-50)
    assert p.volume == 0
