"""Generator syntetyczny: sygnaly choragiewkowe / semafor (kontrola
pozytywna).

Generuje sekwencje klatek z katami flag dla zadanej wiadomosci, korzystajac
z uproszczonego alfabetu w src/common/semaphore_table.py. Opcjonalnie
symuluje dryf katowy ('skret') i losowe defekty (okluzje -> niska
confidence), gotowe do przepuszczenia przez
src/decode/semaphore_decoder.py.
"""

import numpy as np

from src.common.semaphore_table import ALPHABET, letter_to_angles
from src.ingest.semaphore import SemaphoreFrame


def generate_semaphore_sequence(
    text: str,
    hold_s: float = 1.0,
    transition_s: float = 0.3,
    frame_rate: float = 20.0,
    angle_noise_std: float = 2.0,
    drift_deg_per_s: float = 0.0,
    defect_probability: float = 0.0,
) -> list[SemaphoreFrame]:
    letters = [c for c in text.upper() if c in ALPHABET]
    frames: list[SemaphoreFrame] = []
    t = 0.0
    dt = 1.0 / frame_rate

    prev_left, prev_right = letter_to_angles(letters[0]) if letters else (0.0, 0.0)

    for idx, letter in enumerate(letters):
        target_left, target_right = letter_to_angles(letter)

        if idx > 0:
            n_transition = max(1, int(round(transition_s * frame_rate)))
            for k in range(n_transition):
                frac = (k + 1) / n_transition
                left = prev_left + frac * _shortest_delta(prev_left, target_left)
                right = prev_right + frac * _shortest_delta(prev_right, target_right)
                frames.append(_make_frame(t, left, right, angle_noise_std, drift_deg_per_s, defect_probability))
                t += dt

        n_hold = max(1, int(round(hold_s * frame_rate)))
        for _ in range(n_hold):
            frames.append(
                _make_frame(t, target_left, target_right, angle_noise_std, drift_deg_per_s, defect_probability)
            )
            t += dt

        prev_left, prev_right = target_left, target_right

    return frames


def _shortest_delta(a: float, b: float) -> float:
    d = (b - a + 180) % 360 - 180
    return d


def _make_frame(
    t: float,
    left: float,
    right: float,
    angle_noise_std: float,
    drift_deg_per_s: float,
    defect_probability: float,
) -> SemaphoreFrame:
    drift = drift_deg_per_s * t
    left_noisy = (left + drift + np.random.normal(0, angle_noise_std)) % 360
    right_noisy = (right + drift + np.random.normal(0, angle_noise_std)) % 360
    confidence = 0.0 if np.random.rand() < defect_probability else 1.0
    return SemaphoreFrame(t, left_noisy, right_noisy, confidence)


def save_csv(path: str, frames: list[SemaphoreFrame]) -> None:
    import csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["t", "left_angle", "right_angle", "confidence"])
        for fr in frames:
            writer.writerow([fr.t_s, fr.left_angle_deg, fr.right_angle_deg, fr.confidence])
