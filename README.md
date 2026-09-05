# TIMDR-Sygnalizacja

Repo studium przypadku z rodziny TIMDR: testowanie formalizmu sygnałów (anomalia / defekt / rezonans / skręt) na trzech historycznych metodach sygnalizacji — kod Morse'a (dźwiękowy), sygnały świetlne (Morse świetlny / lampa Aldisa) i sygnały chorągiewkowe (semafor flagowy).

Pełna propozycja repo (cel, mapowanie sygnałów, pipeline, protokół walidacji, kamienie milowe): patrz `docs/PROPOSAL.md`.

## Status

Zaimplementowane: dekodery (Morse audio/light, semafor), 4 detektory TIMDR, generatory syntetyczne (kontrole pozytywne/negatywne), testy statystyczne (Mann-Whitney + effect size), wizualizacje, pliki demo, oraz API + panel web z obsługą mikrofonu/głośnika i kamery/ekranu.

Uwaga: alfabet semaforowy w `src/common/semaphore_table.py` jest uproszczonym mapowaniem demonstracyjnym (patrz komentarz w pliku) — do realnego odczytu historycznego semaforu wymaga podmiany na zweryfikowaną, oficjalną tabelę.

## Szybki start (Windows)

1. Uruchom `run.bat` — utworzy virtualenv, zainstaluje `requirements.txt`, uruchomi serwer i otworzy przeglądarkę na `http://127.0.0.1:5000`.
2. W panelu web: sekcja Audio pozwala odtworzyć/nagrać Morse'a przez głośnik/mikrofon; sekcja Sygnał świetlny pozwala migać ekranem (nadawanie) lub przechwycić z kamery.
3. Funkcje mikrofonu/głośnika/kamery wymagają realnego sprzętu — nie da się ich zweryfikować w izolowanym środowisku (patrz `src/io_live/`).

## Demo bez przeglądarki

```
python examples/demo_audio.py
python examples/demo_light.py
python examples/demo_semaphore.py
```

Każdy generuje syntetyczny sygnał, dekoduje go, liczy 4 sygnały TIMDR i zapisuje wykres do `outputs/`.

## Testy

```
pytest tests/ -v
```

## Struktura

```
data/              - dane surowe (audio/light/semaphore) i generatory syntetyczne (kontrole)
src/ingest/        - wczytywanie sygnału per modalność (pliki + na żywo przez src/io_live/)
src/decode/        - dekodery (Morse timing, semafor pozycyjny)
src/timdr_signals/ - detektory anomalia/defekt/rezonans/skręt
src/io_live/       - mikrofon/głośnik (sounddevice), kamera (OpenCV)
src/api/           - serwer Flask (obsługuje panel web)
src/visualize.py   - wykresy matplotlib
www/               - panel testowy (HTML/JS), serwowany przez src/api/server.py
examples/          - pliki demo (generuj → dekoduj → wizualizuj)
protocol/          - pre-rejestracja progów i hipotez
tests/             - kontrole pozytywne/negatywne, testy statystyczne
run.bat            - uruchomienie na Windows (venv + serwer)
```
