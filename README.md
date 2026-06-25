# Amateurfunk Prüfungsvorbereitung

Eine Desktop-Anwendung zum Lernen für die deutsche Amateurfunkprüfung. Basiert auf dem offiziellen Fragenkatalog der Bundesnetzagentur (3. Auflage, März 2024).

## Features

- **Alle drei Klassen**: Klasse N (Einsteiger), Klasse E (Fortgeschrittene), Klasse A (Experte)
- **Spaced Repetition**: Integrierter Lernalgorithmus — jede Frage wird so lange wiederholt, bis sie sicher sitzt (Score 0→5)
- **Antwort-Bilder**: Viele Fragen enthalten Schaltpläne und Diagramme als SVG — sowohl in der Frage als auch in den Antwortmöglichkeiten
- **Zufällige Reihenfolge**: Die vier Antwortmöglichkeiten werden bei jeder Frage neu gemischt
- **Fortschrittsanzeige**: Übersichtlicher Fortschrittsbalken mit Prozent- und Textanzeige
- **Dark Mode**: Augenschonendes dunkles Farbschema (Schieferblau/Dunkelgrau)
- **LaTeX-Formeln**: Mathematische Formeln werden mittels KaTeX dargestellt
- **Lokale Speicherung**: Der Lernfortschritt wird automatisch in `fortschritt.json` gespeichert

## Datenquelle

Die Prüfungsfragen werden von der **Bundesnetzagentur für Elektrizität, Gas, Telekommunikation, Post und Eisenbahnen** unter der Datenlizenz **DL-DE-BY-2.0** bereitgestellt.

- Amtliche Quelle: [www.bundesnetzagentur.de/amateurfunk](https://www.bundesnetzagentur.de/amateurfunk)
- Datenlizenz: [www.govdata.de/dl-de/by-2-0](https://www.govdata.de/dl-de/by-2-0)

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- Windows 10/11 (für andere Plattformen muss pywebview ggf. anders konfiguriert werden)

### Schnellstart

```bash
# Abhängigkeiten installieren
pip install pywebview

# App starten
python app.py
```

Die Dateien `PruefungsfragenZIP/` müssen im selben Ordner wie `app.py` liegen.

### Alternativ: Fertige .exe (Windows)

Lade die neueste `AmateurfunkTrainer.exe` aus dem [Releases](https://github.com/Cosyfluf/Lizenz-leichtgemacht/releases)-Bereich herunter. Keine Installation erforderlich – die .exe enthält bereits alle Fragen, SVGs und Erklärungen.

### Alternativ: Fertige .exe (Windows)

Lade die neueste `AmateurfunkTrainer.exe` aus dem [Releases](https://github.com/Cosyfluf/Lizenz-leichtgemacht/releases)-Bereich herunter. Keine Python-Installation erforderlich.

## Projektstruktur

```
.
├── app.py                   # Hauptanwendung (Python + HTML/CSS/JS)
├── explanations.json        # Erklärungen zu den Fragen (416 Stück)
├── generate_explanations.py # Generator für explanations.json
├── fortschritt.json         # Lernfortschritt (wird automatisch erstellt)
├── README.md
├── LICENSE
└── PruefungsfragenZIP/
    ├── fragenkatalog3b.json # Offizieller Fragenkatalog (JSON)
    ├── svgs/                # SVG-Bilddateien zu den Fragen
    └── README.txt           # Originaldokumentation der BNetzA
```

## Verwendung

1. Wähle oben die **Klasse** aus dem Dropdown-Menü (N / E / A)
2. Lies die Frage und ggf. das angezeigte Bild
3. Klicke auf eine der vier **Antwortmöglichkeiten**
4. Die richtige Antwort wird **grün**, deine Auswahl ggf. **rot** markiert
5. Mit **"Nächste Frage"** geht es weiter
6. Der **Fortschrittsbalken** zeigt jederzeit, wie viele Fragen bereits gelernt wurden

### Scoresystem

| Aktion | Score-Änderung |
|--------|---------------|
| Richtige Antwort | +1 |
| Falsche Antwort | -1 (mindestens 0) |
| Frage gilt als gelernt | Score ≥ 1 |

### Erklärungen

Zu über 400 Fragen (insb. mathematische und technische) werden nach der Antwort automatisch Erklärungen mit Formeln und Rechenwegen eingeblendet. Die Erklärungen können in `explanations.json` erweitert werden.

## Für Entwickler: Eigene .exe bauen

Mit PyInstaller kann eine eigenständige Windows-Exe erstellt werden:

```bash
pip install pyinstaller
python generate_explanations.py        # Erklärungen generieren
pyinstaller --onefile --windowed --name "AmateurfunkTrainer" ^
  --add-data "PruefungsfragenZIP;PruefungsfragenZIP" ^
  --add-data "explanations.json;." app.py
```

Die fertige `.exe` liegt dann im `dist/`-Ordner.

**Hinweis:** Die `.exe` enthält bereits alle Fragen, SVGs und Erklärungen. Es wird kein zusätzlicher Ordner neben der .exe benötigt.

## Lizenz

### Anwendungscode

Copyright (c) 2026 **Cosyfluf**

MIT License — siehe [LICENSE](LICENSE).

### Prüfungsfragen (Daten)

Die Prüfungsfragen und SVG-Bilder unterliegen der **Datenlizenz Deutschland – Namensnennung – Version 2.0 (DL-DE-BY-2.0)**:

> "Prüfungsfragen zum Erwerb von Amateurfunkprüfungsbescheinigungen, Bundesnetzagentur, 3. Auflage, März 2024, (www.bundesnetzagentur.de/amateurfunk), Datenlizenz Deutschland – Namensnennung – Version 2.0 (www.govdata.de/dl-de/by-2-0)"

Veränderungen an den Daten werden im Quellenvermerk mit dem Hinweis versehen, dass die Daten geändert wurden.
