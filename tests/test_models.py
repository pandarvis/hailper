from hailper.models import Track, Email

def test_track_fields():
    t = Track(title="Sardou - La Maladie d'amour", video_id="abc123", added_at="2026-06-21T10:00:00")
    assert t.title.startswith("Sardou")
    assert t.video_id == "abc123"

def test_email_fields():
    e = Email(index=1, sender="EDF", subject="Facture", date="2026-06-20", body="Bonjour")
    assert e.index == 1
    assert e.body == "Bonjour"
