#!/usr/bin/env python3
"""Baut den Index Liednummer -> PDF-Seite aus dem OCR-Textlayer des Scans.

Der Textlayer taugt nicht für Liedtexte, aber gut genug für Navigation: die
Liednummer steht in der Zeile mit dem Bibelvers, am Zeilenanfang. Falsche Treffer
(Buchseitenzahlen) werden über die längste monoton steigende Teilfolge verworfen,
denn Liednummern wachsen über die Seiten hinweg streng monoton.

  python3 tools/build_index.py BUCH [--show-sections]
"""

import bisect, json, os, re, subprocess, sys, pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config


def pdf_pages(pdf, workdir):
    cache = pathlib.Path(workdir) / "textlayer.txt"
    if not cache.exists():
        subprocess.run(["pdftotext", "-layout", pdf, str(cache)], check=True)
    return cache.read_text(encoding="utf-8", errors="replace").split("\f")


def candidates(pages, top):
    out = []
    for i, p in enumerate(pages, 1):
        for line in p.split("\n")[1:12]:  # Kopfzeile überspringen
            m = re.match(r"\s{0,30}(\d{1,3})\s{2,}\S", line)
            if m and 1 <= int(m.group(1)) <= top:
                out.append((i, int(m.group(1))))
    return out


def longest_increasing(cands):
    vals = [n for _, n in cands]
    tails, idx, par = [], [], [None] * len(vals)
    for k, v in enumerate(vals):
        j = bisect.bisect_right(tails, v)
        if j == len(tails):
            tails.append(v)
            idx.append(k)
        else:
            tails[j] = v
            idx[j] = k
        par[k] = idx[j - 1] if j > 0 else None
    if not idx:
        return []
    k, chain = idx[-1], []
    while k is not None:
        chain.append(cands[k])
        k = par[k]
    return list(reversed(chain))


def show_sections(pages):
    print("Rubrikzeilen je Seite - hier siehst du, wo der Liedteil aufhört")
    print(
        "(typisch folgen danach 'LESUNGEN UND GEBETE', 'PSALMEN', 'ANHANG', Register)\n"
    )
    last = None
    for i, p in enumerate(pages, 1):
        head = p.split("\n")[0].strip()
        head = re.sub(r"\s*\d+\s*$", "", head).strip()
        if head and not head.isdigit() and head != last:
            print(f"  PDF {i:4}  {head[:60]}")
            last = head


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = load_config(sys.argv[1])
    pages = pdf_pages(cfg["pdf"], cfg["workdir"])
    if "--show-sections" in sys.argv:
        show_sections(pages)
        return
    top = cfg["song_range"][1]
    chain = longest_increasing(candidates(pages, top))
    index = {}
    for pg, n in chain:
        index.setdefault(str(n), pg)
    out = pathlib.Path(cfg["workdir"]) / "num2page.json"
    # bereits verifizierte Korrekturen nicht überschreiben
    if out.exists():
        fixed = json.loads(out.read_text()).get("_verified", {})
        index.update(fixed)
        index["_verified"] = fixed
    out.write_text(json.dumps(index, ensure_ascii=False, indent=1))
    n_anchor = len([k for k in index if k != "_verified"])
    print(f"{len(pages)} PDF-Seiten gelesen")
    print(f"{n_anchor} Liednummern lokalisiert von {top} -> {out}")
    print(f"\nPruefe Stichproben, bevor du darauf baust:")
    for k in list(sorted((k for k in index if k != "_verified"), key=int))[:3]:
        print(f"   Nr. {k} soll auf PDF-Seite {index[k]} stehen")


if __name__ == "__main__":
    main()
