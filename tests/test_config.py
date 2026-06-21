import os
from hailper.config import Config

def test_load_from_toml(tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        '[secrets]\n'
        'anthropic_api_key = "key-from-file"\n'
        'orange_email = "a@orange.fr"\n'
        'orange_app_password = "pw"\n'
        '[audio]\n'
        'whisper_model = "tiny"\n',
        encoding="utf-8",
    )
    cfg = Config.load(cfg_file)
    assert cfg.anthropic_api_key == "key-from-file"
    assert cfg.orange_email == "a@orange.fr"
    assert cfg.whisper_model == "tiny"
    assert cfg.imap_host == "imap.orange.fr"  # default
    assert cfg.model == "claude-haiku-4-5-20251001"  # default

def test_env_overrides_file(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('[secrets]\nanthropic_api_key = "from-file"\n', encoding="utf-8")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    cfg = Config.load(cfg_file)
    assert cfg.anthropic_api_key == "from-env"

def test_missing_file_uses_defaults_and_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    cfg = Config.load(tmp_path / "does-not-exist.toml")
    assert cfg.anthropic_api_key == "x"
    assert cfg.whisper_model == "base"
