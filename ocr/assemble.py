"""Seitenbild -> strukturiertes Lied (Nummer, Metadaten, Strophen, Refrain)."""

import re, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bands import load_gray, staves, lyric_bands, tail_bands, head_band
from ocr import ocr_band
from clean import strip_noise, join_syllables

FOOT_RX = re.compile(
    r"^(Text|Melodie|Satz|Originaltitel|©|\(c\)|Alle Rechte|Deutsch|Melodiefassung)",
    re.I,
)
REFR_RX = re.compile(r"^\s*(Refrain|Kehrvers)\b", re.I)
WORD_RX = re.compile(r"[A-Za-zÄÖÜäöüß]{3,}")


def wordlike(t, need=2):
    """Echter Text, nicht Notenschrott: mind. `need` Wörter mit Vokal."""
    ws = [w for w in WORD_RX.findall(t) if re.search(r"[aeiouäöüAEIOUÄÖÜ]", w)]
    return len(ws) >= need


def read_lyric_band(png, top, bot):
    """Strophenband -> {nr: fragment} bzw. {'R': fragment} für Refrain."""
    raw = ocr_band(png, top, bot, psm=6)
    out, refrain, orphan = {}, [], []
    for line in raw.split("\n"):
        t = strip_noise(line)
        if not t:
            continue
        m = re.search(r"(?:^|\s)(\d{1,2})\s*[.)]\s*(.+)$", t)
        if m:
            out[int(m.group(1))] = join_syllables(m.group(2))
        elif REFR_RX.match(t):
            refrain.append(join_syllables(REFR_RX.sub("", t, count=1)))
        elif wordlike(t):
            orphan.append(join_syllables(t))  # Text ohne erkennbare Zuordnung
    return out, [r for r in refrain if r], orphan


def read_tail(png, bands):
    """Schwanzbänder -> (prosastrophen, fusszeilen)."""
    verses, foot = {}, []
    for top, bot in bands:
        raw = ocr_band(png, top, bot, psm=6)
        t = strip_noise(" ".join(raw.split("\n")))
        if not t:
            continue
        if FOOT_RX.match(t):
            foot.append(t)
            continue
        m = re.match(r"^(\d{1,2})\s*[.)]\s*(.+)$", t)
        if m:
            body = re.sub(
                r"\s*(Refrain|Kehrvers)\s*$", "", m.group(2), flags=re.I
            )
            verses[int(m.group(1))] = [
                x.strip() for x in body.split("/") if x.strip()
            ]
    return verses, foot


def read_head(png, band):
    if not band:
        return None, ""
    raw = ocr_band(png, band[0], band[1], psm=6)
    t = strip_noise(" ".join(raw.split("\n")))
    m = re.search(r"\b(\d{1,3})\b", t)
    return (int(m.group(1)) if m else None), t


def read_song(pngs, expect_nr=None):
    """Mehrere Seiten eines Liedes einlesen und zusammenführen."""
    verses, refrain, foot, nr = {}, [], [], None
    problems, nbands, prose_keys = [], 0, set()
    for i, png in enumerate(pngs):
        a = load_gray(png)
        if i == 0:
            ocr_nr, _ = read_head(png, head_band(a))
            nr = expect_nr if expect_nr is not None else ocr_nr
        for bi, (top, bot) in enumerate(lyric_bands(a)):
            v, r, orph = read_lyric_band(png, top, bot)
            nbands += 1
            for k, frag in v.items():
                verses.setdefault(k, []).append(
                    frag
                )  # 1 Systemzeile = 1 Versszeile
            if r:
                refrain.append(" ".join(r))
            for o in orph:
                problems.append(
                    f"Seite {i+1}, Band {bi+1}: Text ohne Strophenzuordnung: {o[:60]!r}"
                )
        tv, tf = read_tail(png, tail_bands(a))
        for k, lines in tv.items():
            verses.setdefault(k, []).extend(lines)
            prose_keys.add(k)
        foot.extend(tf)
    # Vollständigkeitsprüfung: jede Strophe braucht ein Fragment je Notenband
    sung = {k: v for k, v in verses.items() if k not in prose_keys}
    if sung and nbands:
        for k, v in sorted(sung.items()):
            if len(v) < nbands:
                problems.append(
                    f"Strophe {k}: {len(v)} von {nbands} Notenbändern zugeordnet - UNVOLLSTÄNDIG"
                )
    return dict(
        nr=nr, verses=verses, refrain=refrain, footer=foot, problems=problems
    )
