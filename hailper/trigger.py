from __future__ import annotations

from typing import Protocol


class Trigger(Protocol):
    def wait(self) -> None: ...


class ConsoleTrigger:
    """Press Enter to trigger — for --text dev mode."""

    def wait(self) -> None:
        input("[Appuie sur Entrée pour parler] ")


class EvdevTrigger:
    """Blocks until the configured key (default Right Ctrl) is pressed (Linux)."""

    def __init__(self, key_name: str = "KEY_SPACE"):
        self.key_name = key_name
        self._device = self._find_keyboard()

    def _find_keyboard(self):
        import evdev

        target = getattr(evdev.ecodes, self.key_name)
        for path in evdev.list_devices():
            dev = evdev.InputDevice(path)
            caps = dev.capabilities()
            if evdev.ecodes.EV_KEY in caps and target in caps[evdev.ecodes.EV_KEY]:
                return dev
        raise RuntimeError("Aucun clavier trouvé pour le déclencheur.")

    def wait(self) -> None:
        import evdev

        target = getattr(evdev.ecodes, self.key_name)
        for event in self._device.read_loop():
            if event.type == evdev.ecodes.EV_KEY and event.code == target and event.value == 1:
                return
