"""Testy statystyczne zgodne z protokolem TIMDR (docs/PROPOSAL.md,
sekcja 7): kontrole pozytywne vs. negatywne, test Manna-Whitneya +
effect size r, niezaleznosc sygnalow, powtarzalnosc, spojnosc
miedzymodalnosciowa.

Uruchomienie: pytest tests/stats/test_validation_protocol.py -v
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import numpy as np
import pytest
from scipy.stats import pearsonr

from data.synthetic.gen_light_flashes import generate_light_flashes
from data.synthetic.gen_morse_audio import generate_morse_audio
from data.synthetic.gen_noise import generate_noise_audio, generate_noise_light, generate_noise_semaphore
from data.synthetic.gen_semaphore_sequence import generate_semaphore_sequence
from src.decode import morse_decoder, semaphore_decoder
from src.ingest.audio import signal_to_keying_events
from src.ingest.light import brightness_to_flash_events
from src.timdr_signals import anomalia, defekt, rezonans, skret
from tests.stats.stats_utils import mannwhitney_with_effect_size

N_REPS = 15
MESSAGE = "TIMDR TEST"
ALPHA = 0.05
MIN_EFFECT_SIZE_R = 0.3  # umiarkowany efekt wg konwencji (Cohen)


def _audio_rezonans_score(seed: int, positive: bool) -> float:
    rng_state = np.random.get_state()
    np.random.seed(seed)
    try:
        if positive:
            synth = generate_morse_audio(MESSAGE, wpm=18, noise_std=0.05)
            events = signal_to_keying_events(synth.waveform, synth.sample_rate)
        else:
            waveform = generate_noise_audio(duration_s=3.0, sample_rate=8000, noise_std=0.3)
            events = signal_to_keying_events(waveform, 8000)
        decoded = morse_decoder.decode(events)
        return rezonans.from_decoded_morse(decoded).score
    finally:
        np.random.set_state(rng_state)


def _light_rezonans_score(seed: int, positive: bool) -> float:
    rng_state = np.random.get_state()
    np.random.seed(seed)
    try:
        if positive:
            synth = generate_light_flashes(MESSAGE, wpm=18, noise_std=0.03)
            events = brightness_to_flash_events(synth.t, synth.brightness)
        else:
            t, brightness = generate_noise_light(duration_s=3.0)
            events = brightness_to_flash_events(t, brightness)
        decoded = morse_decoder.decode(events)
        return rezonans.from_decoded_morse(decoded).score
    finally:
        np.random.set_state(rng_state)


def _semaphore_rezonans_score(seed: int, positive: bool) -> float:
    rng_state = np.random.get_state()
    np.random.seed(seed)
    try:
        if positive:
            frames = generate_semaphore_sequence(MESSAGE, hold_s=0.6, angle_noise_std=3.0)
        else:
            frames = generate_noise_semaphore(duration_s=6.0)
        decoded = semaphore_decoder.decode(frames)
        return rezonans.from_decoded_semaphore(decoded).score
    finally:
        np.random.set_state(rng_state)


@pytest.mark.parametrize(
    "score_fn",
    [_audio_rezonans_score, _light_rezonans_score, _semaphore_rezonans_score],
    ids=["audio", "light", "semaphore"],
)
def test_rezonans_positive_vs_negative_control(score_fn):
    """H: kontrole pozytywne (czysty, syntetyczny sygnal) daja wyzszy
    score rezonansu niz kontrole negatywne (szum) - test Manna-Whitneya,
    jednostronny, z effect size r.
    """
    positive_scores = [score_fn(seed, True) for seed in range(N_REPS)]
    negative_scores = [score_fn(seed + 1000, False) for seed in range(N_REPS)]

    result = mannwhitney_with_effect_size(positive_scores, negative_scores, alternative="greater")

    assert result.p_value < ALPHA, (
        f"Oczekiwano istotnej roznicy (p<{ALPHA}), otrzymano p={result.p_value:.4f} "
        f"(pozytywne: {positive_scores}, negatywne: {negative_scores})"
    )
    assert abs(result.effect_size_r) >= MIN_EFFECT_SIZE_R, (
        f"Oczekiwano effect size r>={MIN_EFFECT_SIZE_R}, otrzymano r={result.effect_size_r:.3f}"
    )


def test_signal_independence_audio():
    """Sygnaly TIMDR nie powinny byc trywialnie kolinearne (nie moga byc
    artefaktem tej samej metryki) - sprawdzamy korelacje Pearsona miedzy
    anomalia.score i |skret.drift_rate| na wielu powtorzeniach kontroli
    pozytywnej z roznym poziomem szumu.
    """
    anomalia_scores, skret_scores = [], []
    for seed in range(N_REPS):
        np.random.seed(seed)
        noise = 0.02 + 0.01 * (seed % 5)
        synth = generate_morse_audio(MESSAGE, wpm=18, noise_std=noise, drift_per_char=0.005 * (seed % 3))
        events = signal_to_keying_events(synth.waveform, synth.sample_rate)
        decoded = morse_decoder.decode(events)
        anomalia_scores.append(anomalia.from_decoded_morse(decoded).score)
        skret_scores.append(abs(skret.from_decoded_morse(decoded).score))

    corr, _ = pearsonr(anomalia_scores, skret_scores)
    assert abs(corr) < 0.9, f"Sygnaly anomalia i skret wygladaja na kolinearne (r={corr:.3f})"


def test_reproducibility_audio():
    """Te same dane wejsciowe (ten sam seed) -> te same wyniki dekodera
    i detektorow przy wielokrotnym uruchomieniu (powtarzalnosc)."""

    def run_once():
        np.random.seed(42)
        synth = generate_morse_audio(MESSAGE, wpm=18, noise_std=0.05)
        events = signal_to_keying_events(synth.waveform, synth.sample_rate)
        decoded = morse_decoder.decode(events)
        return decoded.text, rezonans.from_decoded_morse(decoded).score

    text_a, score_a = run_once()
    text_b, score_b = run_once()

    assert text_a == text_b
    assert score_a == pytest.approx(score_b)


def test_cross_modality_consistency_audio_light():
    """Ten sam komunikat, nadany dwoma roznymi kanalami o niskim szumie
    (audio i swietlny), powinien zdekodowac sie do tego samego tekstu."""
    np.random.seed(7)
    audio = generate_morse_audio(MESSAGE, wpm=18, noise_std=0.01)
    audio_events = signal_to_keying_events(audio.waveform, audio.sample_rate)
    audio_decoded = morse_decoder.decode(audio_events)

    np.random.seed(7)
    light = generate_light_flashes(MESSAGE, wpm=18, noise_std=0.005)
    light_events = brightness_to_flash_events(light.t, light.brightness)
    light_decoded = morse_decoder.decode(light_events)

    assert audio_decoded.text == audio.ground_truth_text.replace(" ", " ")
    assert light_decoded.text == light.ground_truth_text.replace(" ", " ")
    assert audio_decoded.text == light_decoded.text
