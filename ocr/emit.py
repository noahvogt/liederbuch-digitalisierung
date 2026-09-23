"""Strukturiertes Lied -> slidegen-Textdatei."""

import re, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify import autofix
from clean import join_across, fix_spacing

LINE_LIMIT, VAL_LIMIT = 85, 100
TRANS = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }
)


def filename(title):
    return re.sub(r'[/\\:*?"<>|]', "", title.translate(TRANS)).strip() + ".txt"


def wrap(text, limit=LINE_LIMIT):
    """Auf Satzzeichen umbrechen, damit Slidezeilen lesbar bleiben."""
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for chunk in re.split(r"(?<=[,;:!?.])\s+", text):
        if not cur:
            cur = chunk
        elif len(cur) + 1 + len(chunk) <= limit:
            cur += " " + chunk
        else:
            parts.append(cur)
            cur = chunk
    if cur:
        parts.append(cur)
    out = []
    for p in parts:
        while len(p) > limit:
            cut = p.rfind(" ", 0, limit)
            if cut <= 0:
                cut = limit
            out.append(p[:cut])
            p = p[cut:].strip()
        if p:
            out.append(p)
    return out


def parse_footer(foot):
    """Fusszeilen -> text:/melody:/rights."""
    blob = " ".join(foot)

    def grab(pat):
        m = re.search(pat, blob)
        return m.group(1).strip(" ·-–;,") if m else ""

    text = grab(r"Text[:;]\s*(.+?)(?=(?:Melodie|Satz|©|\(c\)|Alle Rechte)|$)")
    melody = grab(
        r"Melodie(?:fassung)?(?:\s+und\s+Satz)?[:;]\s*(.+?)(?=(?:Satz|©|\(c\)|Alle Rechte|Text)|$)"
    )
    rights = grab(r"((?:©|\(c\)|Alle Rechte).+)$")
    deutsch = grab(r"Deutsch[:;]\s*(.+?)(?=(?:Melodie|Satz|©)|$)")
    if deutsch:
        text = (text + ", Deutsch: " + deutsch).strip(", ")
    return text[:VAL_LIMIT], melody[:VAL_LIMIT], rights


def build(song, title, structure):
    text, melody, rights = parse_footer(song["footer"])
    head = [
        f"title: {title}",
        f"book: Gesangbuch «Gesangbuch der Mennoniten» Nr. {song['nr']}",
        f"text: {text or 'unbekannt'}",
        f"melody: {melody or 'unbekannt'}",
        f"structure: {structure}",
    ]
    body, flags = [], []
    elems = list(dict.fromkeys(structure.split(",")))
    for e in elems:
        src = song["refrain"] if e == "R" else song["verses"].get(int(e), [])
        if isinstance(src, str):
            src = [src]
        body.append(f"[{e}]")
        for line in join_across(src):
            line = fix_spacing(line)
            fixed, applied, flagged = autofix(line)
            flags.extend([(e, w, sg) for w, sg in flagged])
            body.extend(wrap(fixed))  # greift nur bei >85 Zeichen
        body.append("")
    return (
        "\n".join(head) + "\n\n" + "\n".join(body).rstrip() + "\n",
        flags,
        rights,
    )
