# Generatory syntetyczne (kontrole)

Miejsce na generatory czystych, syntetycznych sygnalow uzywanych jako
kontrole pozytywne i negatywne w protokole walidacji (docs/PROPOSAL.md,
sekcja 7):

- `gen_morse_audio.py` (zaimplementowany) - syntetyczny ton Morse'a o znanym WPM
- `gen_light_flashes.py` (zaimplementowany) - syntetyczne blyski o znanym timingu
- `gen_semaphore_sequence.py` (zaimplementowany) - syntetyczna sekwencja katow flag
  odpowiadajaca znanemu komunikatowi
- `gen_noise.py` (zaimplementowany) - kontrole negatywne: szum audio / losowe klatki /
  losowe pozycje flag
