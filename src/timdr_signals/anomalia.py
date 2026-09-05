"""Detektor sygnalu TIMDR: anomalia.

Rdzen: odchylenie standaryzowane (z-score) wartosci wzgledem oczekiwanej
normy. Adaptery per modalnosc dostarczaja wlasciwa serie wartosci
(patrz docs/PROPOSAL.md, sekcja 4):
- Morse (audio/light): reszta unit_ratio wzgledem oczekiwanej wartosci
  dla danego typu elementu (1 dla kropki, 3 dla kreski).
- Semafor: blad katowy dopasowania do najblizszego znaku.
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class AnomaliaResult:
    score: float  # srednia |z-score| - wieksza = wiecej anomalii
    z_scores: list[float] = field(default_factory=list)
    flagged_indices: list[int] = field(default_factory=list)


def detect(
    values: list[float], expected: list[float] | float | None = None, z_threshold: float = 2.0
) -> AnomaliaResult:
    """Wykrywa anomalie w serii wartosci wzgledem oczekiwanej normy.

    `expected` moze byc pojedyncza wartoscia (ta sama norma dla
    wszystkich probek) lub lista wartosci oczekiwanych rownej dlugosci
    co `values` (norma per-probka, np. 1 dla kropek, 3 dla kresek).
    Jesli None, norma = srednia wartosci.
    """
    if not values:
        return AnomaliaResult(score=0.0)

    arr = np.asarray(values, dtype=float)
    if expected is None:
        exp = np.full_like(arr, arr.mean())
    elif isinstance(expected, (int, float)):
        exp = np.full_like(arr, float(expected))
    else:
        exp = np.asarray(expected, dtype=float)

    residuals = arr - exp
    std = residuals.std()
    if std < 1e-9:
        z_scores = np.zeros_like(residuals)
    else:
        z_scores = residuals / std

    flagged = [i for i, z in enumerate(z_scores) if abs(z) > z_threshold]
    score = float(np.mean(np.abs(z_scores)))
    return AnomaliaResult(score=score, z_scores=z_scores.tolist(), flagged_indices=flagged)


def from_decoded_morse(decoded, z_threshold: float = 2.0) -> AnomaliaResult:
    """Adapter: elementy Morse'a (dot=~1 unit, dash=~3 unit)."""
    values = [e.unit_ratio for e in decoded.elements]
    expected = [1.0 if e.kind == "dot" else 3.0 for e in decoded.elements]
    return detect(values, expected, z_threshold)


def from_decoded_semaphore(decoded, z_threshold: float = 2.0) -> AnomaliaResult:
    """Adapter: blad katowy dopasowania kazdego znaku semaforowego."""
    values = decoded.angle_deviations_deg
    return detect(values, expected=0.0, z_threshold=z_threshold)
