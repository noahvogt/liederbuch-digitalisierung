"""Nur hochsichere OCR-Artefakte reparieren, alles andere markieren."""

import subprocess, re, functools


@functools.lru_cache(maxsize=1)
def _dict_words():
    return None


def hunspell_unknown(text):
    """Wörter, die das deutsche Wörterbuch nicht kennt."""
    r = subprocess.run(
        ["hunspell", "-d", "de_DE", "-l"],
        input=text,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        r = subprocess.run(
            ["hunspell", "-l"], input=text, capture_output=True, text=True
        )
    return set(w for w in r.stdout.split() if w)


def hunspell_suggest(word):
    r = subprocess.run(
        ["hunspell", "-d", "de_DE", "-a"],
        input=word,
        capture_output=True,
        text=True,
    )
    for line in r.stdout.split("\n"):
        if line.startswith("&"):
            return [s.strip() for s in line.split(":", 1)[1].split(",")][:4]
    return []


# Muster, die eindeutig OCR-Schrott sind (keine echte Sprachform)
DIGIT_IN_WORD = re.compile(
    r"\b[A-Za-zÄÖÜäöüß]+\d+[A-Za-zÄÖÜäöüß]*\b|\b[A-Za-zÄÖÜäöüß]*\d+[A-Za-zÄÖÜäöüß]+\b"
)
DOUBLED_CAP = re.compile(r"\b([A-ZÄÖÜ])([a-zäöüß])([a-zäöüß]{2,})\b")
# OCR verwechselt Ziffern mit Buchstaben
DIGIT_ALT = {
    "5": "gs",
    "0": "oO",
    "1": "li",
    "8": "B",
    "6": "b",
    "9": "g",
    "3": "e",
    "4": "A",
    "7": "t",
    "2": "z",
}


def autofix(text):
    """Gibt (text, [angewandte fixes], [offene verdachtsfälle]) zurück."""
    applied, flagged = [], []

    # 1) verdoppelter Grossbuchstabe am Wortanfang: Ssein -> sein
    def _dc(m):
        if m.group(1).lower() != m.group(2):  # nur echte Verdopplung Ss/Dd/...
            return m.group(0)
        cand = m.group(2) + m.group(3)
        if hunspell_unknown(cand):
            return m.group(0)
        applied.append((m.group(0), cand))
        return cand

    text = DOUBLED_CAP.sub(_dc, text)
    # 2) Ziffer im Wort -> Wörterbuchvorschlag, nur wenn genau einer plausibel ist
    for m in list(DIGIT_IN_WORD.finditer(text)):
        w = m.group(0)
        cands = set()
        for d, alts in DIGIT_ALT.items():
            if d in w:
                for a in alts:
                    cands.add(w.replace(d, a))
        good = [c for c in sorted(cands) if not hunspell_unknown(c)]
        if len(good) == 1:
            text = text.replace(w, good[0])
            applied.append((w, good[0]))
            continue
        flagged.append((w, good or hunspell_suggest(re.sub(r"\d", "", w))))
    # 3) Restliche unbekannte Wörter nur MARKIEREN
    for w in sorted(hunspell_unknown(text)):
        if any(w == a[1] for a in applied):
            continue
        flagged.append((w, hunspell_suggest(w)))
    return text, applied, flagged
