"""Prawdziwe wejscie sygnalu swietlnego: przechwytywanie jasnosci na
zywo z kamery internetowej, przez OpenCV.

Wyjscie sygnalu swietlnego (nadawanie) jest realizowane po stronie
przegladarki (patrz www/index.html) - miganie ekranem urzadzenia
odbiorcy sluzy tu jako "nadajnik swietlny", sterowany precyzyjnym
timingiem z src/common/morse_timing.py. Nie wymaga to dodatkowego
sprzetu ani serwera.

Wymaga biblioteki `opencv-python` i dzialajacej kamery. Nie da sie tego
przetestowac w odizolowanym srodowisku bez dostepu do sprzetu - uruchom
lokalnie (np. przez run.bat).
"""

import time

import numpy as np

try:
    import cv2  # type: ignore

    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


def _require_cv2() -> None:
    if not _HAS_CV2:
        raise RuntimeError(
            "Modul 'opencv-python' jest niedostepny. Zainstaluj: "
            "pip install opencv-python, i uruchom na maszynie z kamera."
        )


def capture_brightness_from_webcam(
    duration_s: float,
    camera_index: int = 0,
    roi: tuple[int, int, int, int] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Przechwytuje obraz z kamery przez `duration_s` sekund i zwraca
    (t, brightness) - sredni poziom jasnosci klatka po klatce w regionie
    `roi` (x, y, w, h), z prawdziwym czasem "zegarowym" per klatka
    (rzeczywisty czas przechwycenia, nie zalozony FPS - kamery USB czesto
    maja nierowny odstep miedzy klatkami).
    """
    _require_cv2()

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Nie mozna otworzyc kamery o indeksie {camera_index}.")

    ts: list[float] = []
    vals: list[float] = []
    start = time.monotonic()
    try:
        while True:
            now = time.monotonic() - start
            if now >= duration_s:
                break
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if roi is not None:
                x, y, w, h = roi
                gray = gray[y : y + h, x : x + w]
            vals.append(float(gray.mean()) / 255.0)
            ts.append(now)
    finally:
        cap.release()

    return np.array(ts), np.array(vals)
