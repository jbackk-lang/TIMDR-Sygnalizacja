# Propozycja repo: TIMDR-Sygnalizacja

## 1. Cel

Nowe repozytorium studium przypadku z rodziny TIMDR, testujące formalizm sygnałów (anomalia / defekt / rezonans / skręt) na rzeczywistych, historycznych metodach sygnalizacji: kod Morse'a (dźwiękowy), sygnały świetlne (Morse świetlny / lampa Aldisa) oraz sygnały chorągiewkowe (semafor flagowy). Repo jest domenowym case-study — nie modyfikuje rdzenia aksjomatów GIA-TIMDR, tylko go stosuje i testuje na trzech różnych kanałach nośnych tej samej klasy zjawiska (transmisja komunikatu przez dyskretne stany sygnału).

## 2. Nazwa repo

`TIMDR-Sygnalizacja` (spójna z konwencją pozostałych repo domenowych: TIMDR-Seismic, TIMDR-Radar itd.)

## 3. Modalności i dane wejściowe

### 3.1 Morse dźwiękowy
Ciąg kluczowań (on/off) tonu o ustalonej częstotliwości nośnej, proporcje czasowe kropka:kreska:przerwy ≈ 1:3:1:3:7. Wejście: nagranie audio (mikrofon/radio) lub log czasów kluczowania.

### 3.2 Sygnały świetlne (Morse świetlny / lampa Aldisa)
Strukturalnie tożsame z Morse'em dźwiękowym (te same proporcje czasowe), ale nośnikiem jest błysk światła zamiast tonu — kanał optyczny. Wejście: nagranie wideo/klatki jasności punktu świetlnego, lub log czasów błysków. Dodatkowy wymiar względem audio: intensywność i (opcjonalnie) barwa światła jako dodatkowa oś danych.

### 3.3 Sygnały chorągiewkowe (semafor flagowy)
Kodowanie pozycyjne, nie czasowo-tonowe: znak określony przez kąty ustawienia dwóch flag/ramion względem ciała nadawcy, odczytywany klatka po klatce z sekwencji obrazów. Wejście: nagranie wideo lub log par kątów (lewa flaga, prawa flaga) w czasie. Struktura czasowa (jak długo trwa dany znak, przerwy między znakami) jest tu drugorzędna względem poprawności samej pozycji.

## 4. Mapowanie sygnałów TIMDR

| Sygnał TIMDR | Morse dźwiękowy | Sygnały świetlne | Chorągiewkowe |
|---|---|---|---|
| **Anomalia** | Odchylenie czasu trwania elementu od oczekiwanego rytmu (WPM), niepasujące do wzorca „ręki" nadawcy | Błysk o nietypowym czasie trwania lub nietypowej intensywności względem wzorca | Kąt ustawienia flagi niezgodny z żadnym zdefiniowanym symbolem semaforowym |
| **Defekt** | Zerwany ton, sklejone znaki, brak przerwy międzyznakowej | Utracony/zasłonięty błysk, refleksy/zaświetlenie uniemożliwiające odczyt | Zgubiona klatka, okluzja, rozmycie uniemożliwiające odczyt pozycji |
| **Rezonans** | Stabilna zgodność rytmu kluczowania z oczekiwaną periodycznością danej prędkości nadawania | Stabilna periodyczność błysków zgodna z tempem transmisji | Powtarzalność tempa zmiany pozycji zgodna z oczekiwanym rytmem nadawania znaków |
| **Skręt** | Dryf fazy/częstotliwości tonu lub dryf timingu charakterystyczny dla „ręki" nadawcy | Dryf częstotliwości błysków lub (jeśli dotyczy) barwy światła w czasie | Systematyczny dryf kąta ustawienia ramion charakterystyczny dla danego nadawcy |

Naturalne powiązanie z rdzeniem: kanały tonowe/optyczne (częstotliwość, faza) odpowiadają gałęzi Axioms_K (modal/phase-sync); struktura czasowa kluczowania — gałęzi Axioms_S (sygnał); kodowanie pozycyjne semafora domaga się dodatkowo elementu geometrycznego z Axioms_G (kąt, konfiguracja przestrzenna). Chronoproces Ξ=(T,x,Γ,φ) mapuje się jako: T = oś czasu, x = stan (kropka/kreska/cisza dla Morse'a, para kątów dla semafora), Γ = zgodność (kongruencja) rytmu/pozycji z wzorcem, φ = faza tonu/błysku (dla semafora: opcjonalnie faza cyklu ruchu ramion).

## 5. Struktura repo

```
TIMDR-Sygnalizacja/
├── README.md
├── docs/
│   └── PROPOSAL.md                    # ten dokument
├── data/
│   ├── raw/
│   │   ├── audio/                     # nagrania Morse'a dźwiękowego
│   │   ├── light/                     # nagrania/klatki sygnałów świetlnych
│   │   └── semaphore/                 # nagrania/klatki sygnałów chorągiewkowych
│   └── synthetic/                     # generatory syntetyczne dla wszystkich trzech modalności (kontrole)
├── src/
│   ├── ingest/
│   │   ├── audio.py                   # detekcja obwiedni tonu
│   │   ├── light.py                   # detekcja błysków z wideo/klatek
│   │   └── semaphore.py               # ekstrakcja kątów flag z wideo/klatek
│   ├── decode/
│   │   ├── morse_decoder.py           # wspólny dekoder timingu (audio + light)
│   │   └── semaphore_decoder.py       # dekoder pozycyjny (kąty → znak)
│   └── timdr_signals/
│       ├── anomalia.py                # parametryzowane per modalność
│       ├── defekt.py
│       ├── rezonans.py
│       └── skret.py
├── protocol/
│   └── preregistration.md             # progi detekcji, hipotezy, osobno per modalność
├── tests/
│   ├── positive_controls/             # czyste syntetyczne sygnały, znane parametry
│   ├── negative_controls/             # szum bez sygnału / losowe pozycje flag
│   └── stats/                         # testy Manna-Whitneya, effect size r, moc testu
└── notebooks/                          # eksploracja, wizualizacje per modalność
```

## 6. Pipeline

1. Wczytanie sygnału właściwym modułem `ingest` (audio / wideo świetlne / wideo semaforowe).
2. Ekstrakcja reprezentacji pośredniej: elementy czasowe (Morse audio/light) lub sekwencja par kątów (semafor).
3. Baseline dekoder (weryfikacja poprawności ekstrakcji względem znanego komunikatu).
4. Detektory czterech sygnałów TIMDR — wspólny interfejs, logika dostosowana do modalności (patrz tabela w sekcji 4).
5. Walidacja statystyczna wg protokołu (patrz niżej), raportowana osobno per modalność i łącznie.

## 7. Protokół walidacji (zgodnie z metodologią TIMDR)

- Pre-rejestracja progów i hipotez osobno dla każdej z trzech modalności, przed testami na danych realnych.
- Kontrola pozytywna: czysty syntetyczny sygnał o znanych parametrach (WPM dla Morse'a, znane kąty dla semafora) — detektory powinny dawać zerowy/niski poziom anomalii/defektu.
- Kontrola negatywna: czysty szum (audio) / losowe klatki bez błysku (light) / losowe pozycje flag (semafor) — detektory nie powinny fałszywie wykrywać rezonansu.
- Test Manna-Whitneya do porównania rozkładów sygnał vs. szum, raportowanie effect size r i mocy testu — per modalność.
- Baseline niezależności między czterema sygnałami (czy detekcje nie są artefaktem tej samej metryki).
- Powtarzalność: te same nagrania → te same wyniki przy wielokrotnym uruchomieniu.
- Test spójności między modalnościami: czy ten sam komunikat nadany trzema kanałami daje zgodne profile sygnałów TIMDR.

## 8. Kamienie milowe

1. Ingest + baseline dekoder dla Morse'a dźwiękowego (na danych syntetycznych).
2. Implementacja czterech detektorów TIMDR na timingu (Morse audio).
3. Rozszerzenie o kanał świetlny — reużycie dekodera timingu, nowy moduł ingest.
4. Rozszerzenie o kanał chorągiewkowy — nowy dekoder pozycyjny, adaptacja detektorów do domeny kątowej/geometrycznej.
5. Pełny protokół walidacji z kontrolami i testami statystycznymi dla wszystkich trzech modalności.
6. Test spójności międzymodalnościowej i test na realnych nagraniach (różni nadawcy, różne warunki szumowe/oświetleniowe).

## 9. Powiązanie z rdzeniem GIA-TIMDR

Repo nie zmienia aksjomatów rdzenia — jest zewnętrznym testem formalizmu na trzech pokrewnych domenach, analogicznie do innych repo TIMDR-family (sejsmologia, radar, bezpieczeństwo, EV/baterie). Wyniki (potwierdzenie lub odrzucenie hipotez o obecności sygnałów TIMDR oraz ich spójności między kanałami audio/optycznym/pozycyjnym) mogą zasilić dyskusję o uniwersalności formalizmu, w tym o roli gałęzi Axioms_G przy sygnałach o charakterze czysto geometrycznym (semafor), ale nie wymagają zmian w Axioms_S/G/K.
