"""Silbentrennung auflösen und OCR-Schrott aus Notenbändern entfernen."""

import re

# Zeichen, die Tesseract aus Notenglyphen halluziniert
NOISE = "|}{~^*«»●■▪…"


def strip_noise(s):
    s = "".join(ch for ch in s if ch not in NOISE)
    s = s.replace("‚", ",").replace("’", "'").replace("‘", "'")
    s = re.sub(r"_+", " ", s)  # Haltestriche der Melodie
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def join_syllables(s):
    """'Chris - ti  Blut' -> 'Christi Blut'. Trennstrich mit Spaces = Silbenfuge."""
    s = re.sub(r"(\w)\s*[-‐–]\s*(\w)", r"\1\2", s)  # Silbenfuge schliessen
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def drop_stray(s):
    """Einzelne Streuzeichen am Zeilenrand entfernen."""
    s = re.sub(
        r"^\s*[A-Za-z]\s+(?=[A-ZÄÖÜ])", "", s
    )  # führender Einzelbuchstabe
    s = re.sub(r"\s+[A-Za-z]\s*$", "", s)  # nachgestellter Einzelbuchstabe
    return s.strip()


def verse_lines(raw):
    """OCR eines Strophenbandes -> {strophennr: textfragment}."""
    out = {}
    for line in raw.split("\n"):
        line = strip_noise(line)
        if not line:
            continue
        m = re.match(r"^(\d{1,2})\s*[.)]\s*(.+)$", line)
        if not m:
            continue
        out[int(m.group(1))] = join_syllables(m.group(2))
    return out


def prose_verse(raw):
    """Prosastrophe -> (nr, [zeilen]) anhand der '/'-Versgrenzen."""
    t = strip_noise(" ".join(raw.split("\n")))
    m = re.match(r"^(\d{1,2})\s*[.)]\s*(.+)$", t)
    if not m:
        return None
    nr, body = int(m.group(1)), m.group(2)
    body = re.sub(r"\s*(Refrain|Kehrvers)\s*$", "", body, flags=re.I)
    lines = [x.strip() for x in body.split("/") if x.strip()]
    return nr, lines


def join_across(lines):
    """Silbenfuge über Zeilengrenze: ['... ge -', 'storben ...'] -> zusammen."""
    out = []
    for ln in lines:
        if out and re.search(r"[-‐–]\s*$", out[-1]):
            out[-1] = re.sub(r"\s*[-‐–]\s*$", "", out[-1]) + ln.lstrip()
        else:
            out.append(ln)
    return out


def fix_spacing(s):
    """Verschlucktes Leerzeichen nach Satzzeichen und vor Grossbuchstabe."""
    s = re.sub(r"([,;:!?])(?=[A-Za-zÄÖÜäöüß])", r"\1 ", s)
    return s
