"""Miedzynarodowa tabela kodu Morse'a (standard ITU).

Uzywana przez src/decode/morse_decoder.py do mapowania sekwencji
kropek/kresek na znaki i odwrotnie (do generatorow syntetycznych).
"""

LETTER_TO_MORSE: dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}

MORSE_TO_LETTER: dict[str, str] = {v: k for k, v in LETTER_TO_MORSE.items()}

# Standardowe proporcje czasowe (jednostki = dlugosc kropki):
UNIT_DOT = 1
UNIT_DASH = 3
UNIT_INTRA_CHAR_GAP = 1   # przerwa miedzy elementami tego samego znaku
UNIT_INTER_CHAR_GAP = 3   # przerwa miedzy znakami
UNIT_INTER_WORD_GAP = 7   # przerwa miedzy slowami


def text_to_morse(text: str) -> str:
    """Zamienia tekst (A-Z, 0-9, spacje) na ciag Morse'a rozdzielony '/'
    dla znakow i '   ' (3 spacje) dla slow - format czytelny dla ludzi.
    """
    words = text.upper().split(" ")
    encoded_words = []
    for word in words:
        letters = [LETTER_TO_MORSE[c] for c in word if c in LETTER_TO_MORSE]
        encoded_words.append(" ".join(letters))
    return "   ".join(encoded_words)
