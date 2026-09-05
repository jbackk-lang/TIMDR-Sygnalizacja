"""Demo: sygnaly swietlne (Morse swietlny) - generowanie -> ingest ->
dekodowanie -> sygnaly TIMDR -> wizualizacja.

Uruchomienie (z katalogu glownego repo): python examples/demo_light.py
Wynik: wydruk w konsoli + outputs/demo_light.csv + outputs/demo_light.png
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.synthetic.gen_light_flashes import generate_light_flashes, save_csv
from src.decode import morse_decoder
from src.ingest.light import brightness_to_flash_events
from src.timdr_signals import anomalia, defekt, rezonans, skret
from src.visualize import plot_morse_timeline

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    text = "TIMDR SYGNALIZACJA"

    # hue_drift_per_s symuluje dryf barwy swiatla w czasie - alternatywny
    # kanal sygnalu 'skret' specyficzny dla modalnosci swietlnej.
    synth = generate_light_flashes(text, wpm=15, noise_std=0.03, hue_drift_per_s=2.0)
    csv_path = os.path.join(OUT_DIR, "demo_light.csv")
    save_csv(csv_path, synth.t, synth.brightness, synth.hue)

    events = brightness_to_flash_events(synth.t, synth.brightness)
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

    png_path = os.path.join(OUT_DIR, "demo_light.png")
    plot_morse_timeline(decoded, t=synth.t, level=synth.brightness, title="Demo: sygnaly swietlne", save_path=png_path)

    print(f"Dane: {csv_path}")
    print(f"Wykres: {png_path}")


if __name__ == "__main__":
    main()
