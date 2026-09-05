"""Demo: Morse dzwiekowy - generowanie -> ingest -> dekodowanie ->
sygnaly TIMDR -> wizualizacja.

Uruchomienie (z katalogu glownego repo): python examples/demo_audio.py
Wynik: wydruk w konsoli + outputs/demo_audio.wav + outputs/demo_audio.png
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

from data.synthetic.gen_morse_audio import generate_morse_audio, save_wav
from src.common.signal_utils import envelope_from_waveform
from src.decode import morse_decoder
from src.ingest.audio import signal_to_keying_events
from src.timdr_signals import anomalia, defekt, rezonans, skret
from src.visualize import plot_morse_timeline

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    text = "TIMDR SYGNALIZACJA"

    # noise_std i drift_per_char symuluja realistyczne warunki (szum tla,
    # dryf tempa nadawania - sygnal 'skret').
    synth = generate_morse_audio(text, wpm=15, noise_std=0.05, drift_per_char=0.01)
    wav_path = os.path.join(OUT_DIR, "demo_audio.wav")
    save_wav(wav_path, synth.waveform, synth.sample_rate)

    events = signal_to_keying_events(synth.waveform, synth.sample_rate)
    decoded = morse_decoder.decode(events)

    print(f"Ground truth: {synth.ground_truth_text}")
    print(f"Zdekodowano:  {decoded.text}")
    print(f"WPM (est.):   {decoded.estimated_wpm:.2f} (zadane: 15)")

    a = anomalia.from_decoded_morse(decoded)
    d = defekt.from_decoded_morse(decoded)
    r = rezonans.from_decoded_morse(decoded)
    s = skret.from_decoded_morse(decoded)
    print(
        f"anomalia(score)={a.score:.3f}  defekt(score)={d.score:.3f}  "
        f"rezonans(score)={r.score:.3f}  skret(drift_rate)={s.drift_rate}"
    )

    t = np.arange(len(synth.waveform)) / synth.sample_rate
    envelope = envelope_from_waveform(synth.waveform)
    png_path = os.path.join(OUT_DIR, "demo_audio.png")
    plot_morse_timeline(decoded, t=t, level=envelope, title="Demo: Morse dzwiekowy", save_path=png_path)

    print(f"Nagranie: {wav_path}")
    print(f"Wykres:   {png_path}")


if __name__ == "__main__":
    main()
