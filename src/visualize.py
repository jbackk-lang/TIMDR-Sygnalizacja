"""Wizualizacje (matplotlib) dla wynikow ingest/decode/detektorow TIMDR.

Uzywane przez pliki demo w examples/ - kazda funkcja zapisuje wykres do
pliku PNG (backend 'Agg', bez wymogu wyswietlacza).
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_morse_timeline(decoded, t=None, level=None, title: str = "", save_path: str | None = None) -> None:
    """Rysuje: (gora) sygnal poziomu (obwiednia/jasnosc) w czasie z
    zaznaczonymi elementami kropka/kreska; (dol) unit_ratio kazdego
    elementu z zaznaczonymi anomaliami (patrz src/timdr_signals/anomalia.py).
    """
    from src.timdr_signals import anomalia as anomalia_mod

    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=False)

    ax0 = axes[0]
    if t is not None and level is not None:
        ax0.plot(t, level, color="#5eb0ef", linewidth=0.8)
    for e in decoded.elements:
        color = "#4caf7d" if e.kind == "dot" else "#e0a13a"
        ax0.axvspan(e.start_s, e.end_s, color=color, alpha=0.4)
    ax0.set_title(title or "Sygnal i elementy Morse'a (zielony=kropka, pomaranczowy=kreska)")
    ax0.set_xlabel("czas [s]")
    ax0.set_ylabel("poziom")

    ax1 = axes[1]
    if decoded.elements:
        starts = [e.start_s for e in decoded.elements]
        ratios = [e.unit_ratio for e in decoded.elements]
        result = anomalia_mod.from_decoded_morse(decoded)
        colors = ["#e0616b" if i in result.flagged_indices else "#9198a9" for i in range(len(ratios))]
        ax1.scatter(starts, ratios, c=colors, s=18)
        ax1.axhline(1.0, color="#4caf7d", linestyle="--", linewidth=0.8, label="oczekiwane: kropka")
        ax1.axhline(3.0, color="#e0a13a", linestyle="--", linewidth=0.8, label="oczekiwane: kreska")
        ax1.legend(fontsize=8)
    ax1.set_title("unit_ratio per element (czerwone = anomalia)")
    ax1.set_xlabel("czas [s]")
    ax1.set_ylabel("dlugosc / jednostka")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=130)
    plt.close(fig)


def plot_semaphore_timeline(decoded, title: str = "", save_path: str | None = None) -> None:
    """Rysuje: (gora) blad katowy dopasowania kazdego znaku w czasie z
    zaznaczonymi anomaliami; (dol) czas trzymania kazdego znaku (miara
    rezonansu/stabilnosci rytmu)."""
    from src.timdr_signals import anomalia as anomalia_mod

    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=False)

    starts = [s.start_s for s in decoded.symbols]
    errors = decoded.angle_deviations_deg
    holds = decoded.hold_durations_s
    letters = [s.letter for s in decoded.symbols]

    ax0 = axes[0]
    if starts:
        result = anomalia_mod.from_decoded_semaphore(decoded)
        colors = ["#e0616b" if i in result.flagged_indices else "#5eb0ef" for i in range(len(errors))]
        ax0.bar(range(len(errors)), errors, color=colors)
        ax0.set_xticks(range(len(letters)))
        ax0.set_xticklabels(letters)
    ax0.set_title(title or "Blad katowy dopasowania per znak (czerwone = anomalia)")
    ax0.set_ylabel("blad [deg]")

    ax1 = axes[1]
    if starts:
        ax1.plot(range(len(holds)), holds, marker="o", color="#4caf7d")
        ax1.set_xticks(range(len(letters)))
        ax1.set_xticklabels(letters)
    ax1.set_title("Czas trzymania pozycji per znak (stabilnosc = rezonans)")
    ax1.set_ylabel("czas [s]")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=130)
    plt.close(fig)


def plot_signal_summary(scores: dict, title: str = "", save_path: str | None = None) -> None:
    """Prosty wykres slupkowy 4 sygnalow TIMDR - do szybkiego porownania
    (np. kontrola pozytywna vs. negatywna, albo miedzy modalnosciami).
    """
    names = list(scores.keys())
    values = [scores[k] for k in names]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(names, values, color=["#5eb0ef", "#e0616b", "#4caf7d", "#e0a13a"][: len(names)])
    ax.set_title(title or "Sygnaly TIMDR")
    ax.set_ylabel("score")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=130)
    plt.close(fig)
