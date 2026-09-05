"""Ingest: sygnaly swietlne (Morse swietlny / lampa Aldisa).

Operuje na szeregu czasowym jasnosci (i opcjonalnie barwy) punktu
swietlnego. Ekstrakcja jasnosci z realnego wideo wymaga biblioteki do
przetwarzania obrazu (opcjonalny import OpenCV ponizej) - jesli
niedostepna, uzyj `load_brightness_log` z juz wyekstrahowanym szeregiem
czasowym (CSV: t,brightness[,hue]).
"""

import csv
from dataclasses import dataclass

import numpy as np

from src.common.signal_utils import merge_short_runs, moving_average, threshold_crossing_events

try:
    import cv2  # type: ignore

    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


@dataclass
class FlashEvent:
    start_s: float
    end_s: float
    state: bool  # True = blysk obecny, False = ciemno
    mean_intensity: float | None = None
    mean_hue: float | None = None


def brightness_to_flash_events(
    t: np.ndarray,
    brightness: np.ndarray,
    threshold: float | None = None,
    min_duration_s: float = 0.02,
    smooth_window: int = 3,
) -> list[FlashEvent]:
    """Zamienia szereg czasowy jasnosci na liste zdarzen blyskow.

    Reuzywalne przez generatory syntetyczne i testy - dziala bezposrednio
    na tablicach numpy.
    """
    smoothed = moving_average(brightness, smooth_window)
    raw_events = threshold_crossing_events(t, smoothed, threshold)
    clean_events = merge_short_runs(raw_events, min_duration_s)

    events: list[FlashEvent] = []
    for start, end, state in clean_events:
        mask = (t >= start) & (t < end)
        mean_intensity = float(brightness[mask].mean()) if mask.any() else None
        events.append(FlashEvent(start, end, state, mean_intensity=mean_intensity))
    return events


def load_brightness_log(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Wczytuje CSV (t,brightness[,hue]) z juz wyekstrahowanym sygnalem
    jasnosci - typowy sposob dostarczenia danych, gdy ekstrakcja z wideo
    jest wykonywana zewnetrznym narzedziem.
    """
    ts, vals, hues = [], [], []
    has_hue = False
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        has_hue = reader.fieldnames is not None and "hue" in reader.fieldnames
        for row in reader:
            ts.append(float(row["t"]))
            vals.append(float(row["brightness"]))
            if has_hue:
                hues.append(float(row["hue"]))
    return (
        np.array(ts),
        np.array(vals),
        np.array(hues) if has_hue else None,
    )


def extract_brightness_from_video(
    path: str, roi: tuple[int, int, int, int] | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Ekstrahuje sredni jasnosci (i czas) klatka po klatce z pliku wideo
    w regionie zainteresowania `roi` (x, y, w, h). Wymaga OpenCV.

    To jest implementacja referencyjna - do dzialania na prawdziwych
    nagraniach zwykle potrzebna jest kalibracja ROI (lokalizacja zrodla
    swiatla) per nagranie.
    """
    if not _HAS_CV2:
        raise ImportError(
            "extract_brightness_from_video wymaga opencv-python. "
            "Alternatywnie uzyj load_brightness_log() z juz wyekstrahowanym "
            "szeregiem jasnosci."
        )

    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    ts, vals = [], []
    frame_idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if roi is not None:
                x, y, w, h = roi
                gray = gray[y : y + h, x : x + w]
            vals.append(float(gray.mean()))
            ts.append(frame_idx / fps)
            frame_idx += 1
    finally:
        cap.release()

    return np.array(ts), np.array(vals)
