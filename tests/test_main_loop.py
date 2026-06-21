from hailper.main import run_once

class FakeTrigger:
    def wait(self): pass

class FakeRecognizer:
    def __init__(self, text): self._text = text
    def listen(self): return self._text

class RecordingSpeaker:
    def __init__(self): self.spoken = []; self.earcons = []
    def say(self, text): self.spoken.append(text)
    def earcon(self, name): self.earcons.append(name)

class FakeBrain:
    def __init__(self, reply): self._reply = reply; self.heard = None
    def handle(self, text): self.heard = text; return self._reply

def test_run_once_happy_path():
    speaker = RecordingSpeaker()
    brain = FakeBrain("Je lance Brel.")
    run_once(FakeTrigger(), FakeRecognizer("mets du brel"), brain, speaker)
    assert brain.heard == "mets du brel"
    assert speaker.spoken == ["Je lance Brel."]
    assert "listening" in speaker.earcons and "thinking" in speaker.earcons

def test_run_once_empty_speech_asks_again():
    speaker = RecordingSpeaker()
    brain = FakeBrain("unused")
    run_once(FakeTrigger(), FakeRecognizer(""), brain, speaker)
    assert brain.heard is None  # brain not called
    assert any("compris" in s.lower() for s in speaker.spoken)

def test_run_once_handles_brain_error():
    class BoomBrain:
        def handle(self, text): raise RuntimeError("boom")
    speaker = RecordingSpeaker()
    run_once(FakeTrigger(), FakeRecognizer("x"), BoomBrain(), speaker)
    assert "error" in speaker.earcons
    assert any("problème" in s.lower() for s in speaker.spoken)
