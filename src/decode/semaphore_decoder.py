"""Dekoder semaforowy (choragiewkowy).

Wejscie: sekwencja klatek z katami obu flag (SemaphoreFrame z
src/ingest/semaphore.py). Algorytm:

1. Segmentacja sekwencji na okresy "trzymanej" pozycji (kat stabilny w
   obrebie tolerancji przez min. `min_hold_s`) rozdzielone okresami
   przejscia (szybka zmiana kata) - przejscia sa pomijane, nie
   traktowane jako osobne znaki.
2. Dla kazdego trzymanego segmentu: usrednienie katow, dopasowanie do
   najblizszej litery w src/common/semaphore_table.py, zapisanie bledu
   katowego dopasowania (do wykorzystania jako sygnal 'anomalia') oraz
   sredniej pewnosci klatek w segmencie (niska pewnosc -> 'defekt').
"""

from dataclasses import dataclass, field

import numpy as np

from src.common.semaphore_table import nearest_letter


@dataclass
class SemaphoreSymbol:
    letter: str
    start_s: float
    end_s: float
    hold_duration_s: float
    angle_error_deg: float
    mean_confidence: float


@dataclass
class DecodedSemaphore:
    text: str
    symbols: list[SemaphoreSymbol] = field(default_factory=list)

    @property
    def angle_deviations_deg(self) -> list[float]:
        return [s.angle_error_deg for s in self.symbols]

    @property
    def hold_durations_s(self) -> list[float]:
        return [s.hold_duration_s for s in self.symbols]

    @property
    def confidences(self) -> list[float]:
        return [s.mean_confidence for s in self.symbols]


def _angular_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _segment_holds(
    frames: list, angle_tolerance_deg: float, min_hold_s: float
) -> list[list]:
    """Grupuje klatki w segmenty stabilnej pozycji (oba katy zmieniaja sie
    o mniej niz `angle_tolerance_deg` wzgledem poczatku segmentu).
    """
    if not frames:
        return []
    segments: list[list] = [[frames[0]]]
    for frame in frames[1:]:
        seg = segments[-1]
        ref = seg[0]
        if (
            _angular_diff(frame.left_angle_deg, ref.left_angle_deg) <= angle_tolerance_deg
            and _angular_diff(frame.right_angle_deg, ref.right_angle_deg) <= angle_tolerance_deg
        ):
            seg.append(frame)
        else:
            segments.append([frame])

    # Uwaga: filtrujemy wylacznie po czasie trwania (>= min_hold_s), bez
    # wyjatku dla "len(seg) > 1" - taki wyjatek pozwalalby przypadkowym,
    # 2-klatkowym trafieniom w szumie (sasiednie losowe katy w obrebie
    # tolerancji) przechodzic jako "trzymane" pozycje, co sztucznie
    # zawyzaloby stabilnosc (rezonans) kontroli negatywnej.
    return [seg for seg in segments if (seg[-1].t_s - seg[0].t_s) >= min_hold_s]


def decode(
    frames: list, angle_tolerance_deg: float = 15.0, min_hold_s: float = 0.3
) -> DecodedSemaphore:
    """Dekoduje sekwencje klatek z katami flag na tekst i metadane."""
    segments = _segment_holds(frames, angle_tolerance_deg, min_hold_s)

    symbols: list[SemaphoreSymbol] = []
    for seg in segments:
        left_mean = float(np.mean([f.left_angle_deg for f in seg]))
        right_mean = float(np.mean([f.right_angle_deg for f in seg]))
        letter, error = nearest_letter(left_mean, right_mean)
        confidence = float(np.mean([f.confidence for f in seg]))
        symbols.append(
            SemaphoreSymbol(
                letter=letter,
                start_s=seg[0].t_s,
                end_s=seg[-1].t_s,
                hold_duration_s=seg[-1].t_s - seg[0].t_s,
                angle_error_deg=error,
                mean_confidence=confidence,
            )
        )

    text = "".join(s.letter for s in symbols)
    return DecodedSemaphore(text=text, symbols=symbols)
