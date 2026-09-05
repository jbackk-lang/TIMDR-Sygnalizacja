"""Uproszczona tabela alfabetu semaforowego (flag semaphore).

UWAGA WAZNA: dokladne przypisanie par pozycji ramion do wszystkich 26
liter w oficjalnym, historycznym alfabecie semaforowym (brytyjski/
miedzynarodowy Semaphore Flag Signalling System) wymaga weryfikacji ze
zrodlem referencyjnym (np. oficjalna karta semaforowa) - nie jest tu
odtwarzane z pelna pewnoscia co do zgodnosci z historycznym standardem.

Ponizej: wewnetrznie spojny, uproszczony alfabet demonstracyjny oparty na
tej samej geometrii co prawdziwy semafor (8 pozycji ramienia co 45 stopni
wokol nadawcy, dwa ramiona -> para pozycji = znak). Wystarcza do
przetestowania calego pipeline'u (ingest -> decode -> detektory TIMDR),
ale przed uzyciem do odczytu prawdziwych, historycznych sygnalow
choragiewkowych nalezy podmienic ALPHABET na zweryfikowana, oficjalna
tabele.

Pozycje (stopnie, 0 = pion w gore, rosnąco zgodnie z ruchem wskazowek
zegara, jak na tarczy zegara widzianej przez odbiorce):
"""

from itertools import permutations

POSITION_NAMES = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
POSITION_DEGREES = {name: i * 45 for i, name in enumerate(POSITION_NAMES)}

_ALPHABET_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Generujemy deterministyczna, wewnetrznie spojna liste par pozycji
# (left, right) rozna dla kazdej litery, z wylaczeniem par gdzie oba
# ramiona sa w tej samej pozycji (nieczytelne / zarezerwowane).
_valid_pairs = [
    (a, b) for a in POSITION_NAMES for b in POSITION_NAMES if a != b
]

ALPHABET: dict[str, tuple[str, str]] = {
    letter: pair for letter, pair in zip(_ALPHABET_LETTERS, _valid_pairs)
}

LETTER_BY_PAIR: dict[tuple[str, str], str] = {
    pair: letter for letter, pair in ALPHABET.items()
}


def letter_to_angles(letter: str) -> tuple[int, int]:
    """Zwraca (kat_lewy_deg, kat_prawy_deg) dla danej litery."""
    left, right = ALPHABET[letter.upper()]
    return POSITION_DEGREES[left], POSITION_DEGREES[right]


def nearest_letter(left_angle_deg: float, right_angle_deg: float) -> tuple[str, float]:
    """Znajduje litere o najblizszej parze katow (najmniejszy sumaryczny
    blad katowy). Zwraca (litera, blad_w_stopniach).
    """
    best_letter = None
    best_error = float("inf")
    for letter, (left_name, right_name) in ALPHABET.items():
        l_deg = POSITION_DEGREES[left_name]
        r_deg = POSITION_DEGREES[right_name]
        err = _angular_diff(left_angle_deg, l_deg) + _angular_diff(right_angle_deg, r_deg)
        if err < best_error:
            best_error = err
            best_letter = letter
    return best_letter, best_error


def _angular_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)
