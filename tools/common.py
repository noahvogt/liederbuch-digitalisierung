"""Gemeinsame Helfer: Konfiguration, robustes Dateilesen, Arbeitsverzeichnis."""

import json, os, pathlib, re, sys


def repo_root():
    return pathlib.Path(__file__).resolve().parent.parent


def load_config(name_or_path):
    p = pathlib.Path(name_or_path).expanduser()
    if not p.exists():
        p = repo_root() / "books" / f"{name_or_path}.json"
    if not p.exists():
        sys.exit(f"Konfiguration nicht gefunden: {name_or_path}")
    cfg = json.loads(p.read_text(encoding="utf-8"))

    # Pfade und Remote kommen aus local.json - die ist maschinenspezifisch und
    # wird nicht eingecheckt. So bleibt im Repo nur Buchwissen, das ueberall gilt.
    lp = repo_root() / "local.json"
    if lp.exists():
        cfg.update(json.loads(lp.read_text(encoding="utf-8")).get(cfg["id"], {}))
    fehlt = [k for k in ("pdf", "songrepo") if not cfg.get(k)]
    if fehlt:
        sys.exit(f"In local.json fehlt für '{cfg['id']}': {', '.join(fehlt)}\n"
                 f"Vorlage: {repo_root()/'local.json.example'}")

    for key in ("pdf", "songrepo"):
        if cfg.get(key):
            cfg[key] = str(pathlib.Path(cfg[key]).expanduser())
    cfg["_path"] = str(p)
    cfg["workdir"] = str(repo_root() / "work" / cfg["id"])
    os.makedirs(cfg["workdir"], exist_ok=True)
    return cfg


def read_text(path):
    """Liest auch Latin-1-Altbestand, ohne zu stolpern."""
    raw = pathlib.Path(path).read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def book_number(text, cfg):
    """Liednummer aus der book:-Zeile.

    Welche book:-Zeilen zu diesem Buch gehören, sagt cfg["match"] - ein regulärer
    Ausdruck. Das ist Absicht und nicht automatisierbar: gewachsene Liedersammlungen
    enthalten Schreibvarianten und Tippfehler desselben Buchnamens, und nur ihr
    wisst, welche gemeint sind. Ein zu enges Muster lässt Lieder als "fehlend"
    erscheinen, die längst da sind - und erzeugt Dubletten.

    Rückgabe: int (Nummer), "ohne_nummer" (Buch erkannt, Nummer fehlt) oder None.
    """
    m = re.search(r"^book: (.+)$", text, re.M)
    if not m:
        return None
    line = m.group(1)
    if not re.search(cfg["match"], line, re.I):
        return None
    n = re.search(r"Nr\.?\s*(\d+)", line)
    return int(n.group(1)) if n else "ohne_nummer"
