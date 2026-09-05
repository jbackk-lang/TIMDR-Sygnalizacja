"""Generator kontrol negatywnych (szum bez struktury sygnalizacyjnej) dla
wszystkich trzech modalnosci - patrz docs/PROPOSAL.md, sekcja 7.
"""

import numpy as np

from src.ingest.semaphore import SemaphoreFrame


def generate_noise_audio(duration_s: float, sample_rate: int = 8000, noise_std: float = 0.3) -> np.ndarray:
    """Czysty szum gaussowski - brak tonu, brak struktury on/off."""
    n = int(duration_s * sample_rate)
    return np.random.normal(0, noise_std, size=n)


def generate_noise_light(
    duration_s: float, sample_rate: float = 200.0, mean: float = 0.3, noise_std: float = 0.1
) -> tuple[np.ndarray, np.ndarray]:
    """Losowe, ciagle fluktuacje jasnosci (random walk) - brak
    zdefiniowanych, powtarzalnych blyskow o proporcjach kropka/kreska.
    """
    n = int(duration_s * sample_rate)
    t = np.arange(n) / sample_rate
    steps = np.random.normal(0, noise_std, size=n)
    walk = mean + np.cumsum(steps) * 0.1
    brightness = np.clip(walk, 0.0, 1.0)
    return t, brightness


def generate_noise_semaphore(duration_s: float, frame_rate: float = 20.0) -> list[SemaphoreFrame]:
    """Niezalezne, losowe katy obu ramion w kazdej klatce - brak
    trzymanych, stabilnych pozycji odpowiadajacych znakom.
    """
    n = int(duration_s * frame_rate)
    dt = 1.0 / frame_rate
    frames = []
    for i in range(n):
        left = float(np.random.uniform(0, 360))
        right = float(np.random.uniform(0, 360))
        frames.append(SemaphoreFrame(i * dt, left, right, confidence=1.0))
    return frames
