"""Wspolne narzedzia do progowania sygnalow czasowych (audio/light).

Uzywane przez src/ingest/audio.py i src/ingest/light.py, ktore roznia sie
tylko sposobem uzyskania sygnalu "poziomu" w czasie (obwiednia tonu vs.
jasnosc), ale wspoldziela logike zamiany na zdarzenia on/off.
"""

import numpy as np


def moving_average(x: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return x
    kernel = np.ones(window) / window
    return np.convolve(x, kernel, mode="same")


def envelope_from_waveform(signal: np.ndarray) -> np.ndarray:
    """Obwiednia amplitudy sygnalu falowego (np. tonu audio) przez
    transformate Hilberta (jesli scipy dostepne) lub prostrzy fallback
    (rektyfikacja + wygladzanie).
    """
    try:
        from scipy.signal import hilbert

        analytic = hilbert(signal)
        return np.abs(analytic)
    except ImportError:
        rectified = np.abs(signal)
        return moving_average(rectified, window=max(1, len(signal) // 200))


def threshold_crossing_events(
    t: np.ndarray, level: np.ndarray, threshold: float | None = None
) -> list[tuple[float, float, bool]]:
    """Zamienia sygnal poziomu w czasie na liste zdarzen (start, koniec,
    stan) metoda progowania i run-length encoding.

    Jesli `threshold` nie podano, uzywa punktu posrodku miedzy min i max
    (proste, ale dziala dobrze dla sygnalow o wyraznym on/off, typowych
    dla kluczowania Morse'a / blyskow swietlnych).
    """
    if len(t) == 0:
        return []
    if threshold is None:
        threshold = (float(np.max(level)) + float(np.min(level))) / 2.0

    state = level >= threshold
    events: list[tuple[float, float, bool]] = []
    run_start_idx = 0
    current_state = bool(state[0])
    for i in range(1, len(state)):
        if state[i] != current_state:
            events.append((float(t[run_start_idx]), float(t[i]), current_state))
            run_start_idx = i
            current_state = bool(state[i])
    events.append((float(t[run_start_idx]), float(t[-1]), current_state))
    return events


def merge_short_runs(
    events: list[tuple[float, float, bool]], min_duration_s: float
) -> list[tuple[float, float, bool]]:
    """Usuwa artefakty progowania krotsze niz `min_duration_s`, scalajac
    je z sasiednimi runami tego samego stanu co powstaje po usunieciu.
    Uzyteczne do odszumiania przed dekodowaniem.
    """
    if not events:
        return events
    filtered = [e for e in events if (e[1] - e[0]) >= min_duration_s]
    if not filtered:
        # Zaden run nie osiaga minimalnego czasu trwania - typowe dla
        # czystego szumu bez struktury on/off (progowanie oscyluje co
        # probke). Zamiast zwracac niescalona, "posiekana" liste (co
        # falszywie wygladaloby na bardzo stabilny - a wiec 'rezonansowy'
        # - rytm o dlugosci pojedynczej probki), zwracamy pojedynczy
        # przedzial 'off' - brak wykrytego sygnalu.
        return [(events[0][0], events[-1][1], False)]
    merged: list[tuple[float, float, bool]] = [filtered[0]]
    for start, end, state in filtered[1:]:
        last_start, last_end, last_state = merged[-1]
        if state == last_state:
            merged[-1] = (last_start, end, state)
        else:
            merged.append((start, end, state))
    return merged
