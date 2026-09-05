"""Detektor sygnalu TIMDR: skret.

Rdzen: regresja liniowa (najmniejsze kwadraty) wartosci wzgledem czasu -
nachylenie (slope) = tempo dryfu. Uzywa scipy.stats.linregress, co daje
tez wspolczynnik korelacji r i wartosc p (przydatne w protokole
walidacji, docs/PROPOSAL.md sekcja 7). Adaptery per modalnosc:
- Morse: dryf dlugosci elementow 'kropka' w czasie (dryf "reki"/tempa
  nadawcy lub czestotliwosci/fazy przy kanale swietlnym).
- Semafor: dryf bledu katowego dopasowania w czasie (systematyczne
  przesuniecie ustawienia ramion).
"""

from dataclasses import dataclass

from scipy.stats import linregress


@dataclass
class SkretResult:
    score: float  # |nachylenie|, jednostki wartosci/s
    drift_rate: float | None = None  # nachylenie ze znakiem
    r_value: float | None = None
    p_value: float | None = None


def detect(timestamps: list[float], values: list[float]) -> SkretResult:
    """Regresja liniowa values ~ timestamps, zwraca nachylenie jako miare
    dryfu ('skret').
    """
    if len(values) < 3 or len(timestamps) != len(values):
        return SkretResult(score=0.0)

    result = linregress(timestamps, values)
    return SkretResult(
        score=abs(result.slope),
        drift_rate=result.slope,
        r_value=result.rvalue,
        p_value=result.pvalue,
    )


def from_decoded_morse(decoded) -> SkretResult:
    """Adapter: dryf dlugosci elementow 'kropka' w czasie."""
    dots = [(e.start_s, e.duration_s) for e in decoded.elements if e.kind == "dot"]
    if not dots:
        return SkretResult(score=0.0)
    timestamps, values = zip(*dots)
    return detect(list(timestamps), list(values))


def from_decoded_semaphore(decoded) -> SkretResult:
    """Adapter: dryf bledu katowego w czasie."""
    timestamps = [s.start_s for s in decoded.symbols]
    values = decoded.angle_deviations_deg
    return detect(timestamps, values)
