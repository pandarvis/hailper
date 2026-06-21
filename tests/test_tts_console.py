from hailper.tts import ConsoleSpeaker

def test_console_speaker_records(capsys):
    sp = ConsoleSpeaker()
    sp.say("Bonjour")
    sp.earcon("listening")
    assert sp.spoken == ["Bonjour"]
    out = capsys.readouterr().out
    assert "Bonjour" in out
    assert "listening" in out
