"""Notenzeilen erkennen und Textbänder isolieren.

Kernidee: Der Strophentext steht IMMER zwischen Diskant- und Basszeile
eines Systems. Notenzeilen kommen paarweise; die Lücke im Paar ist die
Textzone. Prosastrophen und Fusszeile stehen unter der letzten Notenzeile.
"""

import numpy as np
from PIL import Image


def load_gray(path):
    return np.asarray(Image.open(path).convert("L"))


def _runs(mask, gap=2):
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    out, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - p <= gap:
            p = i
            continue
        out.append((int(s), int(p)))
        s = p = i
    out.append((int(s), int(p)))
    return out


def staff_lines(a, frac=0.55):
    """Einzelne Notenlinien: Bildzeilen, die zu >=55% Tinte sind."""
    return _runs((a < 128).mean(axis=1) >= frac, gap=2)


def staves(a):
    """Notenzeilen (je 5 Linien) als (top,bottom)."""
    lines = staff_lines(a)
    if not lines:
        return []
    gaps = [lines[i + 1][0] - lines[i][1] for i in range(len(lines) - 1)]
    med = np.median(gaps) if gaps else 0
    groups, cur = [], [lines[0]]
    for i, g in enumerate(gaps):
        if g <= max(med * 2.5, 12):
            cur.append(lines[i + 1])
        else:
            groups.append(cur)
            cur = [lines[i + 1]]
    groups.append(cur)
    return [(g[0][0], g[-1][1]) for g in groups if len(g) >= 4]


def lyric_bands(a):
    """Textzonen zwischen Diskant und Bass jedes Systems."""
    st = staves(a)
    out = []
    for i in range(0, len(st) - 1, 2):  # paarweise: Diskant, Bass
        top, bot = st[i][1] + 1, st[i + 1][0] - 1
        if bot - top >= 15:
            out.append((top, bot))
    return out


def tail_bands(a, min_h=14):
    """Bänder unter der letzten Notenzeile (Prosastrophen, Fusszeile)."""
    st = staves(a)
    if not st:
        return []
    start = st[-1][1] + 1
    ink = (a < 128).mean(axis=1)
    mask = ink > 0.004
    mask[:start] = False
    return [(s, e) for s, e in _runs(mask, gap=8) if e - s >= min_h]


def head_band(a):
    """Band oberhalb der ersten Notenzeile (Liednummer + Bibelvers)."""
    st = staves(a)
    if not st:
        return None
    ink = (a < 128).mean(axis=1)
    mask = ink > 0.004
    mask[st[0][0] :] = False
    r = _runs(mask, gap=10)
    return (r[0][0], r[-1][1]) if r else None
