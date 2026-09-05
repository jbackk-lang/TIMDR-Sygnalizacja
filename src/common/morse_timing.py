"""Wspolna logika budowy segmentow czasowych on/off dla wiadomosci
Morse'a - uzywana przez generatory syntetyczne audio i light (unika
duplikacji logiki timingu miedzy kanalami).
"""

from src.common.morse_table import LETTER_TO_MORSE


def wpm_to_unit_s(wpm: float) -> float:
    """Standardowy wzor PARIS: dlugosc kropki [s] = 1.2 / WPM."""
    return 1.2 / wpm


def message_to_segments(
    text: str, unit_s: float, drift_per_char: float = 0.0
) -> list[tuple[float, bool]]:
    """Zamienia tekst na liste segmentow (czas_trwania_s, czy_wlaczony).

    `drift_per_char` pozwala symulowac sygnal 'skret': jednostka czasowa
    rosnie liniowo o ten ulamek na kazdy kolejny znak wiadomosci
    (np. 0.01 = +1% dlugosci jednostki na kazdy znak - narastajace
    spowolnienie/przyspieszenie tempa nadawania w czasie).
    """
    segments: list[tuple[float, bool]] = []
    words = text.upper().split(" ")
    char_counter = 0

    for w_idx, word in enumerate(words):
        letters = [c for c in word if c in LETTER_TO_MORSE]
        for c_idx, ch in enumerate(letters):
            pattern = LETTER_TO_MORSE[ch]
            local_unit = unit_s * (1.0 + drift_per_char * char_counter)
            for i, sym in enumerate(pattern):
                dur = local_unit * (1.0 if sym == "." else 3.0)
                segments.append((dur, True))
                if i < len(pattern) - 1:
                    segments.append((local_unit * 1.0, False))
            if c_idx < len(letters) - 1:
                segments.append((local_unit * 3.0, False))
            char_counter += 1
        if w_idx < len(words) - 1 and letters:
            segments.append((unit_s * (1.0 + drift_per_char * char_counter) * 7.0, False))

    return segments


def segments_to_ground_truth_events(segments: list[tuple[float, bool]]):
    """Zamienia segmenty (czas_trwania, stan) na zdarzenia (start, koniec,
    stan) z globalnym czasem, uzyteczne jako 'ground truth' do
    porownania z wynikiem dekodera.
    """
    events = []
    t = 0.0
    for dur, state in segments:
        events.append((t, t + dur, state))
        t += dur
    return events
