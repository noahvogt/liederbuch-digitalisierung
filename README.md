# Liederbuch-Digitalisierung

Werkzeuge und Prompts, um ein gescanntes Liederbuch in slidegen-Textdateien zu
überführen — Lied für Lied, mit Bildlesung statt OCR.

Entstanden beim Digitalisieren des Gesangbuchs der Mennoniten (576 Lieder). Die
Regeln im Prompt sind keine Theorie, sondern das, was dabei schiefgegangen ist.

## Warum Bildlesung und nicht OCR

Gemessen an handgeprüfter Referenz:

| Verfahren                  | Wortgenauigkeit |
|----------------------------|-----------------|
| Bildlesung durch das Modell| ~98-100 %       |
| OCR-Pipeline (`ocr/`)      | ~87 %           |
| PDF-Textlayer direkt       | unbrauchbar     |

Der Textlayer scheitert an den Strophen **unter** den Noten: dort steht der Text
silbenweise getrennt und mit Notenglyphen verschränkt. Für Navigation und
Fusszeilen ist er brauchbar, für Liedtext nicht. Die Pipeline in `ocr/` bleibt
als Zweitmeinung liegen, nicht als Hauptweg.

## Scannen

Gilt für ein noch nicht eingescanntes Buch. Die Hinweise stammen aus der Arbeit
mit dem Mennoniten-Scan (400 dpi, bitonal) — sie beschreiben, was dort gut lief
und was gestört hat.

**Flachbett, nicht Handykamera.** Bei Noten entscheiden Kleinigkeiten über die
`structure`: Wiederholungszeichen, Volta-Klammern, das kursive kleine "Refrain"
über dem System. Handyfotos bringen perspektivische Verzerrung, wechselndes
Licht und schwankenden Fokus; über mehrere hundert Seiten summiert sich das.
Schwachpunkt des Flachbetts bei gebundenen Büchern ist der Bund — Schattenkante
und gekrümmte Zeilen nahe der Falz. Dagegen hilft nur festes Andrücken.

**Graustufen, nicht Schwarzweiß.** Bitonal trifft die Hell-Dunkel-Entscheidung
beim Scannen und unwiderruflich: dünne Notenlinien brechen weg, und Durchschein
lässt sich nachträglich nicht mehr wegrechnen. Graustufen lässt Spielraum.

**300 dpi reichen.** Der vorhandene Scan hat 400 dpi; zum Lesen wird ohnehin auf
160 dpi heruntergerechnet, und dabei war alles klar erkennbar. 600 dpi bläht nur
die Datei auf.

**Schwarzes Papier hinter die aufgeschlagene Seite legen.** Das ist der wirksamste
Handgriff. Im Mennoniten-Scan scheint die Rückseite durch, auf manchen Seiten so
deutlich, dass "Durchschein ignorieren" ausdrücklich im Prompt steht. Ein
schwarzes Blatt unterdrückt das fast vollständig und kostet nichts.

**OCR-Textebene erzeugen.** SimpleScan liefert keine mit. Ohne sie funktioniert
`tools/build_index.py` nicht, denn es liest den Textlayer, um Liednummern den
Seiten zuzuordnen:

```sh
ocrmypdf --language deu --output-type pdf scan.pdf buch.pdf
```

Für Liedtexte ist diese Ebene unbrauchbar (siehe oben), für Navigation
unverzichtbar.

**Seitenzahlen auf Lücken prüfen.** Im Mennoniten-Scan fehlt Buchseite 756
vollständig; aufgefallen ist das erst spät und zufällig. Nach dem Scannen
einmal die Abfolge durchsehen:

```sh
python3 tools/build_index.py <id> --show-sections
```

## Einrichtung

Vorausgesetzt: `python3`, `poppler-utils` (`pdftotext`, `pdftoppm`), `rclone`.
Für die OCR-Zweitmeinung zusätzlich `tesseract`, `tesseract-data-deu`,
`hunspell`, `hunspell-de`, `python-pillow`, `python-numpy`.

```sh
git clone <forgejo-url>/liederbuch-digitalisierung
cd liederbuch-digitalisierung
```

### rclone-Remote anlegen

Einmalig, interaktiv:

```sh
rclone config
# n) New remote -> Name z.B. nextcloud_lieder
# Storage: webdav
# url: https://<eure-nextcloud>/remote.php/dav/files/<benutzer>/
# vendor: nextcloud
# user / pass: App-Passwort aus den Nextcloud-Einstellungen, NICHT das Hauptpasswort
rclone lsd nextcloud_lieder:        # Test
```

### Liederordner holen

```sh
mkdir -p ~/liedrepo && cd ~/liedrepo
rclone sync "nextcloud_lieder:Pfad/Zu/Liedtexten" songs --progress
```

### Buch konfigurieren

Die Konfiguration hat zwei Ebenen, und die Trennung ist Absicht:

- **`books/<id>.json`** — Buchwissen: Titel, Nummernbereich, `match`-Regex.
  Gilt auf jedem Rechner, gehört ins Repo, ist für jedes Buch einmal zu erarbeiten.
- **`local.json`** — Pfade zum Scan, zum Liederordner und das rclone-Remote.
  Maschinenspezifisch, **nicht eingecheckt** (steht in `.gitignore`).

Also `books/VORLAGE.json` kopieren, ausfüllen, unter `books/<id>.json` speichern,
dann `local.json.example` nach `local.json` kopieren und die Pfade eintragen.

Zwei Felder brauchen Sorgfalt:

- **`song_range`** — die letzte LIEDnummer, nicht die letzte Nummer im Buch.
  Hinter den Liedern folgen oft Lesungen, Gebete oder Register. Finde die Grenze
  mit `python3 tools/build_index.py <id> --show-sections`.
- **`match`** — Regex, der eine `book:`-Zeile diesem Buch zuordnet. Gewachsene
  Sammlungen enthalten Schreibvarianten desselben Buchnamens. Ein zu enges Muster
  lässt vorhandene Lieder als fehlend erscheinen und erzeugt Dubletten.

## Ablauf

```sh
python3 tools/build_index.py  <id>              # Liednummer -> PDF-Seite
python3 tools/inventory.py    <id> --explain    # ZUERST: was wird erkannt?
python3 tools/inventory.py    <id>              # Arbeitsliste erzeugen
python3 tools/make_prompt.py  <id> 1 --out batch01.txt
```

`batch01.txt` in eine **frische** Claude-Sitzung einfügen. Danach:

```sh
python3 tools/validate.py ~/liedrepo/new_songs  # Parserkonformität
```

Ergebnis durchsehen, Dateien nach `songs/` verschieben, nächster Batch.
Zum Schluss:

```sh
python3 tools/sync.py <id>        # nur Dry-Run
python3 tools/sync.py <id> --go   # Dry-Run, Sync, Gegenprobe
```

### Ordnerstruktur

```
~/liedrepo/
  songs/       fertige, geprüfte Dateien - das wird gespiegelt
  new_songs/   frisch erfasst, noch ungeprüft
```

Nie direkt in `songs/` erfassen. `rclone sync` spiegelt, und was lokal fehlt,
wird im Remote gelöscht — `tools/sync.py` erzwingt deshalb immer erst einen
Dry-Run.

## Was die Werkzeuge tun

| Datei | Zweck |
|---|---|
| `tools/build_index.py` | Liednummer -> PDF-Seite aus dem Textlayer, über die längste monotone Teilfolge gegen Fehltreffer abgesichert. `--show-sections` zeigt die Rubriken. |
| `tools/inventory.py` | Vergleicht Liederordner und Buch. `--explain` zeigt Dubletten, Dateien ohne Nummer und nicht zugeordnete `book:`-Zeilen. |
| `tools/make_prompt.py` | Setzt aus `prompts/transcribe.md` und der Arbeitsliste den Batch-Prompt zusammen. |
| `tools/validate.py` | Prüft Parserkonformität genau so, wie slidegen die Datei liest. |
| `tools/sync.py` | rclone-Sync mit erzwungenem Dry-Run und Gegenprobe. |
| `ocr/` | OCR-Pipeline als Zweitmeinung, ~87 % Wortgenauigkeit. |

## Erfahrungswerte

- **5,3k Token je Lied** (gemessen). 45 Lieder ~ 26 % eines 1M-Fensters.
- Größere Batches sind günstiger je Lied: $0,146 bei 10, $0,098 bei 25.
- 45 Lieder dauern rund 100 Minuten.
- Nicht alles in eine Sitzung: bei einem Fehlschlag ist sonst alles verloren.

## Was schiefgehen kann

Aus der ersten Digitalisierung, alles real passiert:

- **Folgeseite nicht angesehen.** Der Refrain steht oft auf der nächsten Seite,
  ohne eigene Liednummer. Das Lied sieht refrainlos aus, `structure` wird falsch.
- **Buchseitenzahl mit Liednummer verwechselt.** Beide stehen oben auf der Seite.
- **Dateien mit abweichender `book:`-Schreibweise** galten als fehlend und wurden
  ein zweites Mal erfasst. Darum `--explain` vor dem ersten Batch.
- **Latin-1-kodierte Altdatei** liess die Bestandsanalyse still eine Datei
  überspringen; das Lied galt als fehlend. `read_text()` fängt das ab.
- **Blockmarker mit Text auf derselben Zeile** (`[1] Erste Zeile...`) werden
  weder vom Parser noch vom Validator erkannt. Das Lied fällt zur Laufzeit aus.
- **Gemeinsamer `[R]`-Block bei wechselndem Refrain** verschluckt die Unterschiede.
- **Blinde Rechtschreibkorrektur** ist gefährlich: ein früherer Versuch
  produzierte 177 Falschvorschläge, weil alte Sprachformen wie "Gnad'" oder
  "ew'ger" als Tippfehler galten. `ocr/verify.py` markiert nur, ersetzt nicht.
