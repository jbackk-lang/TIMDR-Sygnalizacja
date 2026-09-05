"""Prawdziwe wejscie/wyjscie audio: mikrofon (nagrywanie) i glosnik
(odtwarzanie), przez biblioteke `sounddevice`.

Wymaga dzialajacego sprzetu audio (mikrofon/glosnik) i biblioteki
`sounddevice` (patrz requirements.txt). Nie da sie tego przetestowac w
odizolowanym srodowisku bez dostepu do sprzetu - uruchom lokalnie
(np. przez run.bat) na maszynie z mikrofonem/glosnikiem.
"""

import numpy as np

try:
    import sounddevice as sd

    _HAS_SOUNDDEVICE = True
except (ImportError, OSError):
    _HAS_SOUNDDEVICE = False


def _require_sounddevice() -> None:
    if not _HAS_SOUNDDEVICE:
        raise RuntimeError(
            "Modul 'sounddevice' jest niedostepny (brak biblioteki lub brak "
            "sprzetu audio w tym srodowisku). Zainstaluj: pip install "
            "sounddevice, i uruchom na maszynie z mikrofonem/glosnikiem."
        )


def list_audio_devices() -> list[dict]:
    """Zwraca liste dostepnych urzadzen audio (do wyboru mikrofonu/glosnika)."""
    _require_sounddevice()
    return list(sd.query_devices())


def record_audio(
    duration_s: float, sample_rate: int = 8000, device: int | None = None
) -> np.ndarray:
    """Nagrywa `duration_s` sekund z mikrofonu (mono) i zwraca sygnal
    znormalizowany do zakresu [-1, 1], gotowy dla
    src/ingest/audio.py:signal_to_keying_events.
    """
    _require_sounddevice()
    recording = sd.rec(
        int(duration_s * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        device=device,
    )
    sd.wait()
    return recording[:, 0]


def play_waveform(waveform: np.ndarray, sample_rate: int, device: int | None = None) -> None:
    """Odtwarza przebieg falowy (np. z data/synthetic/gen_morse_audio.py)
    przez glosnik. Blokuje az do konca odtwarzania.
    """
    _require_sounddevice()
    sd.play(waveform.astype(np.float32), samplerate=sample_rate, device=device)
    sd.wait()
