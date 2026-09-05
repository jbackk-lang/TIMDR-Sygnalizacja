"""Detektor sygnalu TIMDR: rezonans.

Rdzen: stabilnosc (niska zmiennosc) rytmu - wspolczynnik zmiennosci
(coefficient of variation, CV = std/mean) serii wartosci reprezentujacej
takt nadawania. Niska CV -> wysoki rezonans (stabilny, powtarzalny rytm).
Adaptery per modalnosc (patrz docs/PROPOSAL.md, sekcja 4):
- Morse: dlugosci elementow sklasyfikowanych jako kropka (powinny byc
  zblizone przy stabilnej predkosci nadawania).
- Semafor: czasy trzymania poszczegolnych znakow.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class RezonansResult:
    score: float  # w [0, 1], 1 = idealnie stabilny rytm
    coefficient_of_variation: float
    mean_period_s: float | None = None


def detect(values: list[float]) -> RezonansResult:
    """Ocena stabilnosci rytmu na podstawie listy okresow/dlugosci."""
    if len(values) < 2:
        return RezonansResult(score=0.0, coefficient_of_variation=float("nan"))

    arr = np.asarray(values, dtype=float)
    mean = arr.mean()
    if mean <= 1e-9:
        return RezonansResult(score=0.0, coefficient_of_variation=float("nan"))

    cv = float(arr.std() / mean)
    score = max(0.0, 1.0 - cv)
    return RezonansResult(score=score, coefficient_of_variation=cv, mean_period_s=float(mean))


def from_decoded_morse(decoded) -> RezonansResult:
    """Adapter: dlugosci elementow 'kropka' jako miara taktu nadawania."""
    dot_durations = [e.duration_s for e in decoded.elements if e.kind == "dot"]
    return detect(dot_durations)


def from_decoded_semaphore(decoded) -> RezonansResult:
    """Adapter: czasy trzymania znakow semaforowych."""
    return detect(decoded.hold_durations_s)
