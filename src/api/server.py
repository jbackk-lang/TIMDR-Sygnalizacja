"""API HTTP (Flask) dla TIMDR-Sygnalizacja: mikrofon/glosnik (audio) i
kamera/ekran (sygnal swietlny), obsluguje frontend w www/.

Uruchomienie: `python -m src.api.server` (lub przez run.bat w katalogu
glownym repo). Serwer dziala lokalnie (127.0.0.1:5000) i wymaga
rzeczywistego sprzetu (mikrofon/glosnik/kamera) do funkcji audio/light -
patrz src/io_live/*.py.
"""

import os

from flask import Flask, jsonify, request, send_from_directory

from data.synthetic.gen_morse_audio import generate_morse_audio
from src.common.morse_timing import message_to_segments, wpm_to_unit_s
from src.decode import morse_decoder
from src.ingest.audio import signal_to_keying_events
from src.ingest.light import brightness_to_flash_events
from src.timdr_signals import anomalia, defekt, rezonans, skret

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WWW_DIR = os.path.join(REPO_ROOT, "www")

app = Flask(__name__, static_folder=None)


def _decoded_report(decoded) -> dict:
    return {
        "text": decoded.text,
        "estimated_wpm": round(decoded.estimated_wpm, 2) if decoded.estimated_wpm else None,
        "n_elements": len(decoded.elements),
        "unmapped_patterns": decoded.unmapped_patterns,
        "signals": {
            "anomalia": vars(anomalia.from_decoded_morse(decoded)),
            "defekt": vars(defekt.from_decoded_morse(decoded)),
            "rezonans": vars(rezonans.from_decoded_morse(decoded)),
            "skret": vars(skret.from_decoded_morse(decoded)),
        },
    }


@app.route("/")
def index():
    return send_from_directory(WWW_DIR, "index.html")


@app.route("/www/<path:filename>")
def www_files(filename):
    return send_from_directory(WWW_DIR, filename)


@app.route("/api/audio/play", methods=["POST"])
def audio_play():
    from src.io_live.audio_io import play_waveform

    data = request.get_json(force=True) or {}
    text = data.get("text", "SOS")
    wpm = float(data.get("wpm", 15))
    tone_freq_hz = float(data.get("tone_freq_hz", 600))

    synth = generate_morse_audio(text, wpm=wpm, tone_freq_hz=tone_freq_hz)
    try:
        play_waveform(synth.waveform, synth.sample_rate)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    return jsonify(
        {
            "status": "played",
            "text": synth.ground_truth_text,
            "duration_s": round(len(synth.waveform) / synth.sample_rate, 3),
        }
    )


@app.route("/api/audio/record", methods=["POST"])
def audio_record():
    from src.io_live.audio_io import record_audio

    data = request.get_json(force=True) or {}
    duration_s = float(data.get("duration_s", 5.0))
    sample_rate = int(data.get("sample_rate", 8000))

    try:
        waveform = record_audio(duration_s, sample_rate)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    events = signal_to_keying_events(waveform, sample_rate)
    decoded = morse_decoder.decode(events)
    return jsonify(_decoded_report(decoded))


@app.route("/api/light/capture", methods=["POST"])
def light_capture():
    from src.io_live.light_io import capture_brightness_from_webcam

    data = request.get_json(force=True) or {}
    duration_s = float(data.get("duration_s", 5.0))
    camera_index = int(data.get("camera_index", 0))

    try:
        t, brightness = capture_brightness_from_webcam(duration_s, camera_index)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    events = brightness_to_flash_events(t, brightness)
    decoded = morse_decoder.decode(events)
    return jsonify(_decoded_report(decoded))


@app.route("/api/light/segments", methods=["POST"])
def light_segments():
    """Zwraca liste segmentow (czas_trwania_s, czy_wlaczony) dla zadanego
    tekstu/WPM - przegladarka uzywa tego do migania ekranem w dokladnym
    timingu Morse'a (nadajnik swietlny realizowany po stronie klienta).
    """
    data = request.get_json(force=True) or {}
    text = data.get("text", "SOS")
    wpm = float(data.get("wpm", 15))
    unit_s = wpm_to_unit_s(wpm)
    segments = message_to_segments(text, unit_s)
    return jsonify(
        {
            "segments": [{"duration_s": d, "is_on": s} for d, s in segments],
            "unit_s": unit_s,
        }
    )


def main():
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
