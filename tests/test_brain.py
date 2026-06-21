from types import SimpleNamespace
from hailper.brain import Brain, build_tools

class SpyActions:
    def __init__(self):
        self.calls = []
    def play_music(self, query):
        self.calls.append(("play_music", query))
        return f"Je lance {query}."

def block_text(text):
    return SimpleNamespace(type="text", text=text)

def block_tool(name, inp, tool_id="t1"):
    return SimpleNamespace(type="tool_use", name=name, input=inp, id=tool_id)

class FakeMessages:
    """Returns scripted responses in order."""
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)

class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)

def test_direct_text_response():
    client = FakeClient([
        SimpleNamespace(stop_reason="end_turn", content=[block_text("Bonjour !")]),
    ])
    brain = Brain(client, SpyActions(), model="m")
    assert brain.handle("bonjour") == "Bonjour !"

def test_tool_call_then_text():
    client = FakeClient([
        SimpleNamespace(stop_reason="tool_use",
                        content=[block_tool("play_music", {"query": "brel"})]),
        SimpleNamespace(stop_reason="end_turn", content=[block_text("Voilà.")]),
    ])
    actions = SpyActions()
    brain = Brain(client, actions, model="m")
    out = brain.handle("mets du brel")
    assert actions.calls == [("play_music", "brel")]
    assert out == "Voilà."

def test_unknown_tool_is_handled():
    client = FakeClient([
        SimpleNamespace(stop_reason="tool_use",
                        content=[block_tool("nope", {})]),
        SimpleNamespace(stop_reason="end_turn", content=[block_text("ok")]),
    ])
    brain = Brain(client, SpyActions(), model="m")
    assert brain.handle("x") == "ok"  # does not crash

def test_tools_have_required_names():
    names = {t["name"] for t in build_tools()}
    assert {"play_music", "control_playback", "add_favorite", "remove_favorite",
            "list_favorites", "play_favorites", "read_recent_emails",
            "read_email_full", "say"} <= names
