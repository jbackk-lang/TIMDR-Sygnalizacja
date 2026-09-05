"""Detektor sygnalu TIMDR: defekt.

Rdzen: udzial probek uznanych za nieczytelne/wadliwe w calosci probki.
Adaptery per modalnosc (patrz docs/PROPOSAL.md, sekcja 4):
- Morse: udzial znakow, ktorych wzorca kropek/kresek nie dalo sie
  zmapowac na litere (niepoprawna struktura czasowa).
- Semafor: udzial znakow o niskiej sredniej pewnosci odczytu klatek
  (okluzja / rozmycie w trakcie sledzenia flag).
"""

from dataclasses import dataclass, field


@dataclass
class DefektResult:
    score: float  # udzial wadliwych probek w [0, 1]
    flagged_indices: list[int] = field(default_factory=list)
    total: int = 0


def detect(is_defective: list[bool]) -> DefektResult:
    """Wykrywa defekty na podstawie listy flag wadliwosci per probka."""
    total = len(is_defective)
    if total == 0:
        return DefektResult(score=0.0, total=0)
    flagged = [i for i, bad in enumerate(is_defective) if bad]
    return DefektResult(score=len(flagged) / total, flagged_indices=flagged, total=total)


def from_decoded_morse(decoded) -> DefektResult:
    """Adapter: znaki nierozpoznane ('?' w tekscie) jako defekt."""
    letters = [c for c in decoded.text if c != " "]
    is_defective = [c == "?" for c in letters]
    return detect(is_defective)


def from_decoded_semaphore(decoded, confidence_threshold: float = 0.5) -> DefektResult:
    """Adapter: znaki o niskiej sredniej pewnosci odczytu jako defekt."""
    is_defective = [c < confidence_threshold for c in decoded.confidences]
    return detect(is_defective)
