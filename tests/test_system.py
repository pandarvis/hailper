from datetime import datetime
from hailper.system import SystemControl

class Spy:
    def __init__(self):
        self.calls = []
    def __call__(self, *a, **k):
        self.calls.append((a, k))

def test_get_datetime_french():
    s = SystemControl(clock=lambda: datetime(2026, 6, 21, 14, 5))  # dimanche
    out = s.get_datetime()
    assert "14 heures 05" in out
    assert "dimanche" in out and "juin" in out and "2026" in out

def test_power_requires_confirmation():
    run = Spy()
    s = SystemControl(runner=run)
    msg = s.power_control("shutdown")
    assert "oui" in msg.lower()
    assert run.calls == []  # nothing executed before confirmation
    done = s.confirm()
    assert "éteins" in done.lower()
    assert run.calls[0][0][0] == ["systemctl", "poweroff"]

def test_reboot_confirmation():
    run = Spy()
    s = SystemControl(runner=run)
    s.power_control("reboot")
    s.confirm()
    assert run.calls[0][0][0] == ["systemctl", "reboot"]

def test_confirm_without_pending_is_safe():
    run = Spy()
    s = SystemControl(runner=run)
    assert "rien" in s.confirm().lower()
    assert run.calls == []

def test_cancel_clears_pending():
    run = Spy()
    s = SystemControl(runner=run)
    s.power_control("reboot")
    assert "annule" in s.cancel().lower()
    assert "rien" in s.confirm().lower()
    assert run.calls == []

def test_system_volume():
    run = Spy()
    s = SystemControl(runner=run)
    s.system_volume("up")
    s.system_volume("down")
    assert run.calls[0][0][0] == ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"]
    assert run.calls[1][0][0] == ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"]

def test_restart_uses_spawner():
    spawn = Spy()
    s = SystemControl(spawner=spawn)
    assert "redémarre" in s.restart_assistant().lower()
    assert spawn.calls  # detached restart was scheduled

def test_get_weather_uses_fetch():
    s = SystemControl(weather_city="Lyon", fetch_weather=lambda city: f"Ensoleillé à {city}")
    assert "Lyon" in s.get_weather()

def test_get_weather_handles_failure():
    def boom(city):
        raise RuntimeError("net")
    s = SystemControl(fetch_weather=boom)
    assert "pas" in s.get_weather().lower()
