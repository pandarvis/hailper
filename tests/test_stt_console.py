from hailper.stt import ConsoleRecognizer

def test_console_recognizer_reads_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a: "mets du brel")
    r = ConsoleRecognizer()
    assert r.listen() == "mets du brel"
