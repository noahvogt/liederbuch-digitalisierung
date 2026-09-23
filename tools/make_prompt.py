#!/usr/bin/env python3
"""Erzeugt den Prompt für einen Batch - zum Einfügen in eine FRISCHE Sitzung.

  python3 tools/make_prompt.py BUCH [BATCHNUMMER] [--out DATEI]

Frische Sitzung je Batch, weil Bildlesung Kontext kostet: rund 5,3k Token je Lied
(gemessen). 45 Lieder belegen damit etwa 26% eines 1M-Fensters.
"""

import json, os, sys, pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config, repo_root


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = load_config(sys.argv[1])
    batch = (
        int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1
    )
    size = cfg["batch_size"]
    wl = pathlib.Path(cfg["workdir"]) / "worklist.json"
    if not wl.exists():
        sys.exit(
            "Keine Arbeitsliste. Erst: python3 tools/inventory.py " + cfg["id"]
        )
    rows = json.loads(wl.read_text(encoding="utf-8"))
    chunk = rows[(batch - 1) * size : batch * size]
    if not chunk:
        sys.exit(
            f"Batch {batch} ist leer ({(len(rows)+size-1)//size} Batches vorhanden)."
        )
    table = "\n".join(
        f"| {r['nr']} | {r['page']} | {r['precision']} | {r['title'] or '—'} |"
        for r in chunk
    )
    tpl = (repo_root() / "prompts" / "transcribe.md").read_text(
        encoding="utf-8"
    )
    text = tpl.format(
        batch=batch,
        total=(len(rows) + size - 1) // size,
        lo=chunk[0]["nr"],
        hi=chunk[-1]["nr"],
        n=len(chunk),
        table=table,
        book_title=cfg["book_title"],
        pdf=cfg["pdf"],
        outdir=os.path.join(cfg["songrepo"], "..", "new_songs"),
        dpi=cfg["render_dpi"],
        tools=str(repo_root() / "tools"),
    )
    if "--out" in sys.argv:
        p = sys.argv[sys.argv.index("--out") + 1]
        pathlib.Path(p).write_text(text, encoding="utf-8")
        print(
            f"Batch {batch}: Nr. {chunk[0]['nr']}-{chunk[-1]['nr']} ({len(chunk)} Lieder) -> {p}"
        )
    else:
        print(text)


if __name__ == "__main__":
    main()
