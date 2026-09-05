"""Ingest: Morse dzwiekowy.

Wczytuje nagranie audio (WAV) lub log czasow kluczowania, wykrywa
obwiednie tonu i zwraca ciag zdarzen on/off z ich czasami trwania,
gotowy dla src/decode/morse_decoder.py.
"""

import csv
import wave
from dataclasses import dataclass

import numpy as np

from src.common.signal_utils import (
    envelope_from_waveform,
    merge_short_runs,
    threshold_crossing_events,
)


@dataclass
class KeyingEvent:
    start_s: float
    end_s: float
    state: bool  # True = ton obecny (kluczowanie), False = cisza


def read_wav(path: str) -> tuple[np.ndarray, int]:
    """Wczytuje plik WAV (mono lub stereo, 16-bit) i zwraca (sygnal,
    sample_rate). Dla stereo usrednia kanaly.
    """
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sample_width != 2:
        raise ValueError(f"Obslugiwane jest tylko 16-bit WAV, otrzymano {sample_width * 8}-bit")

    data = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)
    data /= 32768.0
    return data, sample_rate


def signal_to_keying_events(
    waveform: np.ndarray,
    sample_rate: float,
    threshold: float | None = None,
    min_duration_s: float = 0.02,
) -> list[KeyingEvent]:
    """Zamienia surowy sygnal falowy na liste zdarzen kluczowania.

    Reuzywalne przez generatory syntetyczne i testy - dziala bezposrednio
    na tablicy numpy, bez potrzeby zapisu/odczytu pliku WAV.
    """
    t = np.arange(len(waveform)) / sample_rate
    env = envelope_from_waveform(waveform)
    raw_events = threshold_crossing_events(t, env, threshold)
    clean_events = merge_short_runs(raw_events, min_duration_s)
    return [KeyingEvent(start, end, state) for start, end, state in clean_events]


def load_audio_events(
    path: str, threshold: float | None = None, min_duration_s: float = 0.02
) -> list[KeyingEvent]:
    """Wczytuje plik WAV i zwraca sekwencje zdarzen kluczowania."""
    waveform, sample_rate = read_wav(path)
    return signal_to_keying_events(waveform, sample_rate, threshold, min_duration_s)


def load_keying_log(path: str) -> list[KeyingEvent]:
    """Wczytuje log czasow kluczowania z CSV (kolumny: start,end,state)."""
    events: list[KeyingEvent] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = row["state"].strip().lower() in ("1", "true", "on")
            events.append(KeyingEvent(float(row["start"]), float(row["end"]), state))
    return events
