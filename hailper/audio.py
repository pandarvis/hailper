from __future__ import annotations

import collections

SAMPLE_RATE = 16000
FRAME_MS = 30


def record_until_silence(max_seconds: float = 10.0, silence_ms: int = 800) -> bytes:
    """Record 16 kHz mono PCM from the default mic until a pause is detected."""
    import sounddevice as sd
    import webrtcvad

    vad = webrtcvad.Vad(2)
    frame_len = int(SAMPLE_RATE * FRAME_MS / 1000)
    ring = collections.deque(maxlen=int(silence_ms / FRAME_MS))
    voiced: list[bytes] = []
    started = False

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=frame_len,
                           dtype="int16", channels=1) as stream:
        for _ in range(int(max_seconds * 1000 / FRAME_MS)):
            block, _ = stream.read(frame_len)
            frame = bytes(block)
            is_speech = vad.is_speech(frame, SAMPLE_RATE)
            if is_speech:
                started = True
            if started:
                voiced.append(frame)
                ring.append(is_speech)
                if len(ring) == ring.maxlen and not any(ring):
                    break
    return b"".join(voiced)
