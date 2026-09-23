#!/usr/bin/env python3
"""Vergleicht den Liederordner mit dem Buch und schreibt die Arbeitsliste.

python3 tools/inventory.py BUCH            Arbeitsliste erzeugen
python3 tools/inventory.py BUCH --explain  zeigen, welche book:-Zeilen erkannt
                                           werden - IMMER zuerst ausführen
"""

import bisect, glob, json, os, re, sys, pathlib, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config, read_text, book_number


def scan(cfg):
    found, odd, dupes = {}, [], collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(cfg["songrepo"], "*.txt"))):
        t = read_text(f)
        n = book_number(t, cfg)
        if n is None:
            continue
        if n == "ohne_nummer":
            odd.append(os.path.basename(f))
            continue
        dupes[n].append(os.path.basename(f))
        found[n] = os.path.basename(f)
    return found, odd, {k: v for k, v in dupes.items() if len(v) > 1}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = load_config(sys.argv[1])
    found, odd, dupes = scan(cfg)
    lo, hi = cfg["song_range"]

    if "--explain" in sys.argv:
        print(f"match-Muster: {cfg['match']!r}\n")
        print(f"{len(found)} Dateien diesem Buch zugeordnet, mit Nummer")
        if odd:
            print(f"\n{len(odd)} Datei(en) nennen das Buch, aber OHNE Nummer:")
            for o in odd:
                print(f"   {o}")
            print(
                "   -> Diese Lieder gelten als FEHLEND und werden doppelt erfasst!"
            )
            print(
                "      Trage die Nummer nach oder korrigiere die book:-Zeile."
            )
        if dupes:
            print(f"\n{len(dupes)} Nummer(n) mehrfach belegt:")
            for n, fs in sorted(dupes.items()):
                print(f"   Nr. {n}: {fs}")
            print(
                "   -> Zwei Sprachfassungen sind in Ordnung, alles andere prüfen."
            )
        other = collections.Counter()
        for f in glob.glob(os.path.join(cfg["songrepo"], "*.txt")):
            m = re.search(r"^book: (.+)$", read_text(f), re.M)
            if m and book_number(read_text(f), cfg) is None:
                other[m.group(1).strip()] += 1
        if other:
            print(
                f"\nNICHT zugeordnete book:-Zeilen (Auszug) - prüfe auf Schreibvarianten:"
            )
            for k, v in other.most_common(12):
                print(f"   {v:4}x  {k}")
        return

    idx_path = pathlib.Path(cfg["workdir"]) / "num2page.json"
    if not idx_path.exists():
        sys.exit("Kein Index. Erst: python3 tools/build_index.py " + cfg["id"])
    idx = {
        int(k): v
        for k, v in json.loads(idx_path.read_text()).items()
        if k != "_verified"
    }
    reg_path = pathlib.Path(cfg["workdir"]) / "register.json"
    reg = (
        {int(k): v for k, v in json.loads(reg_path.read_text()).items()}
        if reg_path.exists()
        else {}
    )

    ks = sorted(idx)

    def page(n):
        if n in idx:
            return idx[n], "exakt"
        if not ks:
            return 0, "unbekannt"
        i = bisect.bisect_left(ks, n)
        a, b = ks[max(0, i - 1)], ks[min(len(ks) - 1, i)]
        if a == b:
            return idx[a], "geschätzt"
        return (
            round(idx[a] + (idx[b] - idx[a]) * (n - a) / (b - a)),
            "geschätzt",
        )

    missing = [n for n in range(lo, hi + 1) if n not in found]
    rows = [
        dict(nr=n, page=page(n)[0], precision=page(n)[1], title=reg.get(n, ""))
        for n in missing
    ]
    out = pathlib.Path(cfg["workdir"]) / "worklist.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(f"Buch {cfg['id']}: Lieder {lo}-{hi}")
    print(f"  vorhanden: {len(found)}")
    print(f"  FEHLEND:   {len(rows)}  -> {out}")
    if odd:
        print(f"\n  WARNUNG: {len(odd)} Datei(en) nennen das Buch ohne Nummer.")
        print(
            f"  Sie zählen als fehlend und werden doppelt erfasst. --explain zeigt sie."
        )
    print(
        f"\n  Batches a {cfg['batch_size']}: {(len(rows)+cfg['batch_size']-1)//cfg['batch_size']}"
    )


if __name__ == "__main__":
    main()
