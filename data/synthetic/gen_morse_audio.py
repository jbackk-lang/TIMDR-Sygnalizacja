"""Generator syntetyczny: Morse dzwiekowy (kontrola pozytywna).

Generuje przebieg falowy tonu o zadanym WPM, opcjonalnie z dryfem tempa
('skret') i szumem tla, gotowy do przepuszczenia przez
src/ingest/audio.py -> src/decode/morse_decoder.py.
"""

from dataclasses import dataclass

import numpy as np

from src.common.morse_timing import message_to_segments, segments_to_ground_truth_events, wpm_to_unit_s


@dataclass
class SyntheticAudio:
    waveform: np.ndarray
    sample_rate: int
    ground_truth_text: str
    ground_truth_events: list[tuple[float, float, bool]]
    unit_s: float


def generate_morse_audio(
    text: str,
    wpm: float = 15.0,
    tone_freq_hz: float = 600.0,
    sample_rate: int = 8000,
    noise_std: float = 0.0,
    drift_per_char: float = 0.0,
    fade_ms: float = 5.0,
) -> SyntheticAudio:
    unit_s = wpm_to_unit_s(wpm)
    segments = message_to_segments(text, unit_s, drift_per_char)
    ground_truth_events = segments_to_ground_truth_events(segments)

    fade_n = max(1, int(sample_rate * fade_ms / 1000.0))
    chunks = []
    for dur, is_on in segments:
        n = max(1, int(round(dur * sample_rate)))
        if is_on:
            t = np.arange(n) / sample_rate
            wave = np.sin(2 * np.pi * tone_freq_hz * t)
            envelope = np.ones(n)
            ramp = min(fade_n, n // 2)
            if ramp > 0:
                envelope[:ramp] = np.linspace(0, 1, ramp)
                envelope[-ramp:] = np.linspace(1, 0, ramp)
            chunks.append(wave * envelope)
        else:
            chunks.append(np.zeros(n))

    waveform = np.concatenate(chunks) if chunks else np.zeros(0)
    if noise_std > 0:
        waveform = waveform + np.random.normal(0, noise_std, size=len(waveform))

    return SyntheticAudio(
        waveform=waveform,
        sample_rate=sample_rate,
        ground_truth_text=text.upper(),
        ground_truth_events=ground_truth_events,
        unit_s=unit_s,
    )


def save_wav(path: str, waveform: np.ndarray, sample_rate: int) -> None:
    import wave

    clipped = np.clip(waveform, -1.0, 1.0)
    int_data = (clipped * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_data.tobytes())
