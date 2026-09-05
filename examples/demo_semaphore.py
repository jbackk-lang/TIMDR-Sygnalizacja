"""Demo: sygnaly choragiewkowe (semafor) - generowanie -> dekodowanie ->
sygnaly TIMDR -> wizualizacja.

UWAGA: alfabet semaforowy w src/common/semaphore_table.py jest
uproszczonym, demonstracyjnym mapowaniem geometrii pozycji na litery
(patrz komentarz w tym module) - ten demo pokazuje poprawnosc calego
pipeline'u (ingest -> decode -> detektory), nie odwzorowuje w 100%
historycznego, oficjalnego alfabetu semaforowego.

Uruchomienie (z katalogu glownego repo): python examples/demo_semaphore.py
Wynik: wydruk w konsoli + outputs/demo_semaphore.csv + outputs/demo_semaphore.png
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.synthetic.gen_semaphore_sequence import generate_semaphore_sequence, save_csv
from src.decode import semaphore_decoder
from src.timdr_signals import anomalia, defekt, rezonans, skret
from src.visualize import plot_semaphore_timeline

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    text = "TIMDR"

    # drift_deg_per_s symuluje systematyczny dryf ustawienia ramion
    # (sygnal 'skret'); defect_probability symuluje okazjonalna okluzje
    # (sygnal 'defekt').
    frames = generate_semaphore_sequence(
        text, hold_s=0.8, angle_noise_std=3.0, drift_deg_per_s=0.5, defect_probability=0.05
    )
    csv_path = os.path.join(OUT_DIR, "demo_semaphore.csv")
    save_csv(csv_path, frames)

    decoded = semaphore_decoder.decode(frames)

    print(f"Ground truth: {text}")
    print(f"Zdekodowano:  {decoded.text}")

    a = anomalia.from_decoded_semaphore(decoded)
    d = defekt.from_decoded_semaphore(decoded)
    r = rezonans.from_decoded_semaphore(decoded)
    s = skret.from_decoded_semaphore(decoded)
    print(
        f"anomalia(score)={a.score:.3f}  defekt(score)={d.score:.3f}  "
        f"rezonans(score)={r.score:.3f}  skret(drift_rate)={s.drift_rate}"
    )

    png_path = os.path.join(OUT_DIR, "demo_semaphore.png")
    plot_semaphore_timeline(decoded, title="Demo: sygnaly choragiewkowe", save_path=png_path)

    print(f"Dane: {csv_path}")
    print(f"Wykres: {png_path}")


if __name__ == "__main__":
    main()
