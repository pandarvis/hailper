from __future__ import annotations

import argparse
import sys
from functools import partial
from pathlib import Path


def run_once(trigger, recognizer, brain, speaker) -> None:
    """One full interaction cycle. Never raises."""
    trigger.wait()
    speaker.earcon("listening")
    try:
        text = recognizer.listen()
    except Exception:
        speaker.earcon("error")
        speaker.say("Je n'ai pas réussi à t'entendre. Réappuie et réessaie.")
        return
    if not text:
        speaker.say("Je n'ai pas compris, réappuie et réessaie.")
        return
    speaker.earcon("thinking")
    try:
        reply = brain.handle(text)
    except Exception:
        speaker.earcon("error")
        speaker.say("Désolé, j'ai eu un problème. Réessaie dans un instant.")
        return
    if reply:
        speaker.say(reply)
    speaker.earcon("done")


def build_components(cfg, text_mode: bool):
    import anthropic

    from .actions import Actions
    from .brain import Brain, summarize_emails
    from .favorites import FavoritesStore
    from .mail import MailReader

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    favorites = FavoritesStore(Path.home() / ".hailper" / "favorites.json")
    mail_reader = MailReader(cfg.imap_host, cfg.imap_port, cfg.orange_email, cfg.orange_app_password)
    summarize = partial(summarize_emails, client, model=cfg.model)

    if text_mode:
        from .music import FakeMusicPlayer
        from .stt import ConsoleRecognizer
        from .trigger import ConsoleTrigger
        from .tts import ConsoleSpeaker

        player = FakeMusicPlayer()
        trigger, recognizer, speaker = ConsoleTrigger(), ConsoleRecognizer(), ConsoleSpeaker()
    else:
        from .music import MpvPlayer
        from .stt import WhisperRecognizer
        from .trigger import EvdevTrigger
        from .tts import PiperSpeaker

        player = MpvPlayer()
        trigger = EvdevTrigger(cfg.trigger_key)
        recognizer = WhisperRecognizer(cfg.whisper_model)
        speaker = PiperSpeaker(cfg.tts_voice, cfg.tts_rate)

    actions = Actions(player, favorites, mail_reader, summarize, fetch_count=cfg.mail_fetch_count)
    brain = Brain(client, actions, model=cfg.model)
    return trigger, recognizer, brain, speaker


def main() -> None:
    from .config import Config

    parser = argparse.ArgumentParser(description="Hailper voice assistant")
    parser.add_argument("--text", action="store_true", help="Text mode (no mic/voice/Linux deps)")
    parser.add_argument("--config", default=str(Path.home() / ".hailper" / "config.toml"))
    args = parser.parse_args()

    cfg = Config.load(args.config)
    if not cfg.anthropic_api_key:
        print("ANTHROPIC_API_KEY manquante (config.toml ou variable d'environnement).", file=sys.stderr)
        sys.exit(1)

    trigger, recognizer, brain, speaker = build_components(cfg, text_mode=args.text)
    speaker.say("Je suis prêt.")
    while True:
        run_once(trigger, recognizer, brain, speaker)


if __name__ == "__main__":
    main()
