"""Dekoder Morse'a - wspolny dla kanalu audio i swietlnego.

Wejscie: sekwencja zdarzen on/off z czasami trwania (obiekty z polami
start_s, end_s, state - pasuja zarowno KeyingEvent z src/ingest/audio.py
jak i FlashEvent z src/ingest/light.py).

Algorytm:
1. Wyodrebnij zdarzenia 'on' (elementy: kropka/kreska) i przerwy 'off'
   miedzy nimi (przerwa miedzyelementowa / miedzyznakowa / miedzyslowna).
2. Oszacuj jednostke czasowa (dlugosc kropki) na podstawie rozkladu
   dlugosci elementow 'on' (proste progowanie + jedna iteracja
   dopracowania na podstawie sredniej dlugosci elementow ponizej progu).
3. Sklasyfikuj kazdy element jako kropke lub kreske, kazda przerwe jako
   miedzyelementowa / miedzyznakowa / miedzyslowna, wzgledem jednostki.
4. Zbuduj wzorce znakow (ciagi '.'/'-') i zmapuj je na litery przez
   src/common/morse_table.py. Nierozpoznany wzorzec -> '?' (flagowane
   jako defekt przez src/timdr_signals/defekt.py).

Zwraca DecodedMorse z pelnymi metadanymi elementow/przerw potrzebnymi
detektorom TIMDR (anomalia, defekt, rezonans, skret).
"""

from dataclasses import dataclass, field

from src.common.morse_table import MORSE_TO_LETTER


@dataclass
class MorseElement:
    start_s: float
    end_s: float
    duration_s: float
    kind: str  # "dot" | "dash"
    unit_ratio: float  # duration_s / estimated_unit_s


@dataclass
class MorseGap:
    start_s: float
    end_s: float
    duration_s: float
    kind: str  # "intra_char" | "inter_char" | "inter_word"


@dataclass
class DecodedMorse:
    text: str
    elements: list[MorseElement] = field(default_factory=list)
    gaps: list[MorseGap] = field(default_factory=list)
    estimated_unit_s: float = 0.0
    estimated_wpm: float = 0.0
    unmapped_patterns: list[str] = field(default_factory=list)

    @property
    def element_durations_s(self) -> list[float]:
        return [e.duration_s for e in self.elements]

    @property
    def unit_ratios(self) -> list[float]:
        return [e.unit_ratio for e in self.elements]


def _estimate_unit(on_durations: list[float]) -> float:
    """Szacuje dlugosc jednostki (kropki) z rozkladu dlugosci elementow.

    Podejscie dwuetapowe: wstepny prog = geometryczna srednia
    min/max dlugosci; nastepnie unit = srednia dlugosci elementow
    ponizej progu (przyblizone 'kropki'). Jesli wszystkie elementy maja
    podobna dlugosc (brak kresek w probce), unit = mediana wszystkich.
    """
    if not on_durations:
        return 0.0
    lo, hi = min(on_durations), max(on_durations)
    if hi <= 0:
        return 0.0
    if hi / max(lo, 1e-9) < 1.8:
        # brak wyraznego rozroznienia kropka/kreska w probce
        sorted_d = sorted(on_durations)
        return sorted_d[len(sorted_d) // 2]
    threshold = (lo * hi) ** 0.5
    dots = [d for d in on_durations if d < threshold]
    if not dots:
        return lo
    return sum(dots) / len(dots)


def decode(events) -> DecodedMorse:
    """Dekoduje sekwencje zdarzen on/off na tekst i metadane timingu."""
    on_events = [e for e in events if e.state]
    if not on_events:
        return DecodedMorse(text="")

    on_durations = [e.end_s - e.start_s for e in on_events]
    unit = _estimate_unit(on_durations)
    if unit <= 0:
        return DecodedMorse(text="")

    elements: list[MorseElement] = []
    for e in on_events:
        dur = e.end_s - e.start_s
        kind = "dot" if dur < 2 * unit else "dash"
        elements.append(MorseElement(e.start_s, e.end_s, dur, kind, dur / unit))

    gaps: list[MorseGap] = []
    for prev, nxt in zip(on_events, on_events[1:]):
        gap_dur = nxt.start_s - prev.end_s
        if gap_dur < 2 * unit:
            kind = "intra_char"
        elif gap_dur < 5 * unit:
            kind = "inter_char"
        else:
            kind = "inter_word"
        gaps.append(MorseGap(prev.end_s, nxt.start_s, gap_dur, kind))

    # Budowa tekstu: grupuj elementy w znaki wg przerw miedzyznakowych/slownych.
    text_parts: list[str] = []
    unmapped: list[str] = []
    current_pattern = "." if elements[0].kind == "dot" else "-"

    def flush(pattern: str) -> str:
        letter = MORSE_TO_LETTER.get(pattern)
        if letter is None:
            unmapped.append(pattern)
            return "?"
        return letter

    for gap, elem in zip(gaps, elements[1:]):
        symbol = "." if elem.kind == "dot" else "-"
        if gap.kind == "intra_char":
            current_pattern += symbol
        elif gap.kind == "inter_char":
            text_parts.append(flush(current_pattern))
            current_pattern = symbol
        else:  # inter_word
            text_parts.append(flush(current_pattern))
            text_parts.append(" ")
            current_pattern = symbol
    text_parts.append(flush(current_pattern))

    wpm = 1.2 / unit if unit > 0 else 0.0

    return DecodedMorse(
        text="".join(text_parts),
        elements=elements,
        gaps=gaps,
        estimated_unit_s=unit,
        estimated_wpm=wpm,
        unmapped_patterns=unmapped,
    )
