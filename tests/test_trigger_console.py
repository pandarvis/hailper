from hailper.trigger import ConsoleTrigger

def test_console_trigger_waits_for_enter(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a: "")
    ConsoleTrigger().wait()  # should return without error
