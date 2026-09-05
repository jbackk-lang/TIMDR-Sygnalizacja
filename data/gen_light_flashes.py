"""Generator syntetyczny: sygnaly swietlne / Morse swietlny (kontrola
pozytywna).

Generuje szereg czasowy jasnosci (i opcjonalnie barwy, dla symulacji
dryfu koloru jako sygnalu 'skret') o zadanym WPM, gotowy do
przepuszczenia przez src/ingest/light.py -> src/decode/morse_decoder.py.
"""

from dataclasses import dataclass

import numpy as np

from src.common.morse_timing import message_to_segments, segments_to_ground_truth_events, wpm_to_unit_s


@dataclass
class SyntheticLight:
    t: np.ndarray
    brightness: np.ndarray
    hue: np.ndarray | None
    sample_rate: float
    ground_truth_text: str
    ground_truth_events: list[tuple[float, float, bool]]
    unit_s: float


def generate_light_flashes(
    text: str,
    wpm: float = 15.0,
    sample_rate: float = 200.0,
    noise_std: float = 0.02,
    drift_per_char: float = 0.0,
    hue_drift_per_s: float = 0.0,
    baseline: float = 0.05,
    peak: float = 1.0,
    base_hue: float = 0.0,
) -> SyntheticLight:
    unit_s = wpm_to_unit_s(wpm)
    segments = message_to_segments(text, unit_s, drift_per_char)
    ground_truth_events = segments_to_ground_truth_events(segments)

    brightness_chunks, hue_chunks = [], []
    t_cursor = 0.0
    use_hue = hue_drift_per_s != 0.0
    for dur, is_on in segments:
        n = max(1, int(round(dur * sample_rate)))
        level = peak if is_on else baseline
        brightness_chunks.append(np.full(n, level))
        if use_hue:
            local_t = t_cursor + np.arange(n) / sample_rate
            hue_chunks.append((base_hue + hue_drift_per_s * local_t) % 360 if is_on else np.full(n, base_hue))
        t_cursor += dur

    brightness = np.concatenate(brightness_chunks) if brightness_chunks else np.zeros(0)
    if noise_std > 0:
        brightness = brightness + np.random.normal(0, noise_std, size=len(brightness))
    hue = np.concatenate(hue_chunks) if use_hue and hue_chunks else None

    t = np.arange(len(brightness)) / sample_rate

    return SyntheticLight(
        t=t,
        brightness=brightness,
        hue=hue,
        sample_rate=sample_rate,
        ground_truth_text=text.upper(),
        ground_truth_events=ground_truth_events,
        unit_s=unit_s,
    )


def save_csv(path: str, t: np.ndarray, brightness: np.ndarray, hue: np.ndarray | None = None) -> None:
    import csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["t", "brightness"] + (["hue"] if hue is not None else [])
        writer.writerow(header)
        for i in range(len(t)):
            row = [t[i], brightness[i]] + ([hue[i]] if hue is not None else [])
            writer.writerow(row)
