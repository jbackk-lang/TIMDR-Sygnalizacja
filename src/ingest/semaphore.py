"""Ingest: sygnaly choragiewkowe (semafor flagowy).

Operuje na szeregu czasowym par katow (lewa flaga, prawa flaga) wzgledem
nadawcy. Ekstrakcja katow z realnego wideo wymaga sledzenia znacznikow
kolorystycznych flag (opcjonalny import OpenCV ponizej) - jesli
niedostepna lub kalibracja nie jest gotowa, uzyj `load_angle_log` z juz
wyekstrahowanym szeregiem katow (CSV: t,left_angle,right_angle[,confidence]).
"""

import csv
import math
from dataclasses import dataclass

import numpy as np

try:
    import cv2  # type: ignore

    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


@dataclass
class SemaphoreFrame:
    t_s: float
    left_angle_deg: float
    right_angle_deg: float
    confidence: float = 1.0


def load_angle_log(path: str) -> list[SemaphoreFrame]:
    """Wczytuje CSV (t,left_angle,right_angle[,confidence]) z juz
    wyekstrahowanym szeregiem katow flag.
    """
    frames: list[SemaphoreFrame] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        has_conf = reader.fieldnames is not None and "confidence" in reader.fieldnames
        for row in reader:
            conf = float(row["confidence"]) if has_conf else 1.0
            frames.append(
                SemaphoreFrame(
                    float(row["t"]),
                    float(row["left_angle"]),
                    float(row["right_angle"]),
                    conf,
                )
            )
    return frames


def _angle_from_centroid(cx: float, cy: float, body_x: float, body_y: float) -> float:
    """Kat (0-360, 0 = w gore, rosnaco zgodnie z ruchem wskazowek zegara)
    znacznika wzgledem punktu centralnego ciala nadawcy.
    """
    dx = cx - body_x
    dy = body_y - cy  # os Y obrazu rosnie w dol, odwracamy
    angle = math.degrees(math.atan2(dx, dy))
    return angle % 360


def extract_angles_from_video(
    path: str,
    body_center: tuple[float, float],
    left_hsv_range: tuple[tuple[int, int, int], tuple[int, int, int]],
    right_hsv_range: tuple[tuple[int, int, int], tuple[int, int, int]],
) -> list[SemaphoreFrame]:
    """Sledzi dwa kolorowe znaczniki (koncowki flag) metoda progowania
    HSV i zwraca sekwencje katow wzgledem `body_center`. Wymaga OpenCV.

    Implementacja referencyjna - wymaga kalibracji zakresow HSV per
    nagranie/oswietlenie oraz recznego ustalenia body_center (piksele).
    Klatki, w ktorych znacznik nie zostal znaleziony, dostaja
    confidence=0.0 (do wykorzystania jako sygnal 'defekt').
    """
    if not _HAS_CV2:
        raise ImportError(
            "extract_angles_from_video wymaga opencv-python. "
            "Alternatywnie uzyj load_angle_log() z juz wyekstrahowanym "
            "szeregiem katow."
        )

    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    bx, by = body_center
    frames: list[SemaphoreFrame] = []
    idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            t = idx / fps

            left_angle, left_conf = _find_marker_angle(hsv, left_hsv_range, bx, by)
            right_angle, right_conf = _find_marker_angle(hsv, right_hsv_range, bx, by)
            confidence = min(left_conf, right_conf)

            frames.append(SemaphoreFrame(t, left_angle, right_angle, confidence))
            idx += 1
    finally:
        cap.release()

    return frames


def _find_marker_angle(hsv_frame, hsv_range, body_x, body_y) -> tuple[float, float]:
    lo, hi = hsv_range
    mask = cv2.inRange(hsv_frame, np.array(lo), np.array(hi))
    moments = cv2.moments(mask)
    if moments["m00"] == 0:
        return 0.0, 0.0
    cx = moments["m10"] / moments["m00"]
    cy = moments["m01"] / moments["m00"]
    return _angle_from_centroid(cx, cy, body_x, body_y), 1.0
