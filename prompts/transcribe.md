Du hilfst mir, unser Gemeinde-Liederbuch zu digitalisieren. Wir besitzen das Buch,
haben es selbst gescannt und sind als Gemeinde für die Liedrechte lizenziert. Die
Textdateien landen in unserem privaten Repository und steuern die Liedfolien für
unseren Gottesdienst-Livestream. Das Buch ist die verbindliche Fassung — nicht
Lizenzdatenbanken wie CCLI, dort weichen Strophenzahl und -reihenfolge ab.

# Aufgabe

Batch {batch} von {total}: die Lieder Nr. {lo} bis {hi} ({n} Stück) aus dem Scan
lesen und als Textdateien anlegen.

Buch:   {book_title}
Quelle: {pdf}
Ziel:   {outdir}/   (anlegen, falls nicht vorhanden)

| Lied-Nr | PDF-Seite | Genauigkeit | Titel laut Register |
|---------|-----------|-------------|---------------------|
{table}

"geschätzt" heisst: die Seitenzahl ist interpoliert und kann um 1-2 danebenliegen.

# Vorgehen

Für jedes Lied:

1. Seite als Bild rendern, NICHT den OCR-Textlayer lesen:

       pdftoppm -f SEITE -l SEITE -r {dpi} -png "{pdf}" /tmp/seite

   Eingebettete OCR-Textlayer sind für die Strophen unter den Noten unbrauchbar:
   der Text steht dort silbenweise getrennt und mit Notenglyphen verschränkt, und
   die Erkennung liefert Dinge wie "Wo! - len", "dunk-iem", "mel-nes". Lies IMMER
   das gerenderte Bild mit dem Read-Tool.

2. Liednummer IM BILD prüfen. Sie steht gross am oberen Rand, auf ungeraden Seiten
   rechts, auf geraden links. Daneben steht kleiner die BUCHSEITENZAHL — verwechsle
   die beiden nicht. Stimmt die Nummer nicht, eine Seite vor oder zurück.

3. IMMER auch die Folgeseite rendern und ansehen, ausnahmslos, auch wenn das Lied
   abgeschlossen aussieht. Zwei Fälle gehen sonst verloren:
   a) Die Strophen laufen mitten im Satz weiter.
   b) Der REFRAIN steht auf der Folgeseite und trägt dort KEINE eigene Liednummer,
      nur die Beschriftung "Refrain" über dem System. Wer nur die erste Seite
      liest, hält das Lied fälschlich für refrainlos und schreibt ein falsches
      `structure`. Erkennungsmerkmal: gleiche Tonart, keine Liednummer, "Refrain".
   Verlässliches Zeichen für das Liedende ist die FUSSZEILE mit den Urheberangaben.

4. Datei im unten beschriebenen Format anlegen.

# Dateiformat

Genau fünf Metadatenzeilen, dann eine Leerzeile, dann der Textkörper:

    title: <Titel, mit echten Umlauten>
    book: {book_title} Nr. <Nummer>
    text: <Textdichter, knapp>
    melody: <Melodie/Satz, knapp>
    structure: <z.B. 1,2,3 oder 1,R,2,R,3,R>

    [1]
    <Versszeile>
    <Versszeile>

    [R]
    <Versszeile>

Harte Regeln:
- GENAU diese fünf Felder, keine weiteren. Ein Zusatzfeld bricht den Parser.
- Ein Metadatenfeld darf NIE leer sein. Unbekanntes wird "unbekannt", nicht nichts.
- Blockmarker stehen ALLEIN auf ihrer Zeile. `[1] Erste Zeile...` wird nicht
  erkannt, weder vom Parser noch von den Prüfwerkzeugen, und das Lied fällt
  zur Laufzeit aus.
- Metadatenwert höchstens 100 Zeichen, Textzeile höchstens 85 Zeichen.
- Jedes Element aus `structure` braucht einen `[..]`-Block und umgekehrt.
- Dateiname: Titel mit transliterierten Umlauten (ae/oe/ue/ss), Endung .txt.
  Also "Fuer alle.txt", aber im `title:` steht "Für alle".
  Doppelpunkte im Titel werden im Dateinamen zu `_`.
- Keine Kommentarzeilen in fertigen Dateien.

# Wie man die Strophen richtig liest

Der Text steht an zwei Orten, die sich unterschiedlich verhalten.

**Unter den Notenzeilen** stehen die ersten Strophen, silbenweise getrennt und
untereinander pro Strophennummer. Die Trennstriche gehören zur Notensetzung,
nicht zum Wort:

    "1. Lass  du mich stil - le  wer - den"   ->   "Lass du mich stille werden"

Die Zeilenumbrüche der Notensysteme sind NICHT die Versgrenzen. Setze die
Versgrenzen nach dem Versmass — im Zweifel so, wie es die Prosastrophen desselben
Liedes vormachen.

**Unterhalb der Notenzeilen** stehen die restlichen Strophen als Fliesstext, und
dort markiert ein Schrägstrich die Versgrenze:

    "4. Erste Zeile, / zweite Zeile, / dritte Zeile."

Diese Schrägstriche übernimmst du als Zeilenumbrüche — mit einer Ausnahme:
Erzeugt ein Schrägstrich eine Zeile aus nur zwei bis drei Wörtern, die mitten
im Satz abbricht ("Hinauf bis", "verwirrt der"), dann zieh sie mit der Folgezeile
zusammen. Solche Fetzen sehen auf der Folie falsch aus. Behandle gleichartige
Zeilen in ALLEN Strophen gleich, sonst beginnen die Strophen unterschiedlich.

Steht am Ende einer Prosastrophe kursiv "Refrain", folgt der Refrain — das gehört
in `structure`, nicht in den Text.

**Geschweifte Klammer mit zwei Zeilen pro Strophennummer** (Barform): Das System
wird mit zweitem Text wiederholt. Beide Zeilen gehören nacheinander in dieselbe
Strophe, das ist KEIN eigener Strukturteil.

# Wie man `structure` ableitet

Das richtet sich nach dem Buch, nicht nach Gemeindepraxis.

**Ein [R]-Block nur, wenn der Refrain in JEDER Strophe WORTWÖRTLICH gleich ist.**
Das ist die wichtigste Regel hier. Prüfe den Refraintext Strophe für Strophe.
Ändert sich auch nur ein Wort — häufig wechselt die letzte Refrainzeile —, dann
gibt es KEINEN [R]-Block. Stattdessen schreibst du den Refrain in jeder Strophe
voll aus und nimmst `structure: 1,2,3,...`. Ein gemeinsamer Block würde die
Unterschiede verschlucken, und auf der Folie stünde der falsche Text.

Sonst:
- Nur nummerierte Strophen, kein Refrain-System  ->  `1,2,3,...`
- Refrain-System NACH den nummerierten Strophen  ->  `1,R,2,R,3,R,...`
- Refrain-System VOR den nummerierten Strophen   ->  `R,1,R,2,R,3,R,...`

Das Refrain-System ist als "Refrain" oder "Kehrvers" beschriftet und hat keine
Strophennummern. Achte zusätzlich auf Wiederholungszeichen, Volta-Klammern
(1./2.), "(Schluss)", "D.C.", "D.S." und "nur bei Wiederholung".

**Durchkomponiert** (weder nummerierte Strophen noch Refrain-System, auch Kanons):
`structure: R` und der gesamte Text in einen einzigen `[R]`-Block. Die Folien-
umbrüche macht die Software selbst. Nicht künstlich in [1]/[R] aufteilen.

Nur wenn die Notation darüber hinaus mehrdeutig bleibt: Datei als `.txt.todo`
speichern und darunter in Zeilen mit führendem `#` beschreiben, was du gesehen
hast. Lieber melden als raten.

# Metadaten aus der Fusszeile

Unten auf der Seite steht etwa:

    Text: <Person> <Jahre> · Melodie: <Person> <Jahre> · Satz: <Person>
    © <Jahr> <Verlag>

Daraus `text:` und `melody:` füllen, knapp gehalten (100-Zeichen-Grenze). Steht
"Deutsch: <Person>", hänge das an `text:` an. Den ©-Vermerk NICHT in die Datei
schreiben (nur fünf Felder erlaubt), sondern am Ende gesammelt ausgeben — er wird
für die Lizenzmeldung gebraucht.

# Fallstricke

- **Durchscheinende Rückseite**: Der Scan ist beidseitig, schwache Geisterschrift
  der Rückseite ist sichtbar. Ignoriere sie.
- **Mehrere Lieder pro Seite**: Nimm nur die Fusszeile, die zu DEINEM Lied gehört.
- **Alte Sprachformen bewahren**: "Gnad'", "ew'ger", "unschuldge", "bleibet",
  "getrostem" sind Absicht, keine Tippfehler. Nichts modernisieren.
- **Eingeklammerte Auftakte** wie "(Manchmal)" am Strophenanfang sind Notation:
  der Auftakt wird nur in dieser Strophe gesungen. Klammern weglassen, Wort behalten.
- **Mehrstimmigkeit**: Singen Ober- und Unterstimme verschiedenen Text, nimm die
  Melodiestimme. Echo-Rufe der Nebenstimmen weglassen.
- **Sängerhinweise** wie "einer:", "einzelne:", "alle:" NICHT übernehmen.
- **Wiederholungsangaben** wie "(3x)" im Prosatext: ausschreiben, damit jede
  Strophe gleich lang ist.
- **Zwei Sprachfassungen**: Druckt das Buch denselben Titel in zwei Sprachen, leg
  zwei Dateien an, eine je Sprache.
- **Apostrophe** uneinheitlich im Buch; verwende einheitlich das gerade '.
- **Anführungszeichen**: einheitlich deutsch, also "..." (unten/oben).
- **Register ist nicht massgeblich**: Registertitel enthalten Lesefehler. Weicht
  das Register vom Buch ab, gilt das Buch.

# Zum Schluss

1. Prüfe jede Datei mit dem Validator:

       python3 {tools}/validate.py {outdir}

2. Gib eine Tabelle aus: Lied-Nr | Dateiname | Strophenzahl | structure | ©-Vermerk

3. Nenne ausdrücklich:
   - jede Stelle, bei der du unsicher warst
   - jedes Lied, das du als `.txt.todo` abgelegt hast
   - jede Seitenzahl, die von der Liste abwich (wird in den Index zurückgespielt)
   - jede Nummer, die gar kein Lied ist (Lesung, Gebet, Register)

Arbeite die Liste der Reihe nach ab und lege die Dateien wirklich an.
