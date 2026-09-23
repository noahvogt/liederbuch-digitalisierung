import re, sys, glob, os

META = ("title", "book", "text", "melody", "structure")
RX = r"^(?!structure)\S+: .+|^structure: ([0-9]+|R)(,([0-9]+|R))*$"
VAL_LIMIT = 100
LINE_LIMIT = 85


def check(path):
    errs = []
    content = open(path, encoding="utf-8-sig").readlines()
    valid = list(META)
    meta = {}
    body_start = None
    for i, line in enumerate(content):
        if not valid:
            body_start = i
            break
        if not re.match(RX, line):
            errs.append(
                f"Zeile {i+1}: Metadaten-Syntax ungültig -> {line.rstrip()!r}"
            )
            return errs
        key = line[: line.index(":")]
        if key in valid:
            meta[key] = line[line.index(": ") + 2 : -1]
            valid.remove(key)
            continue
        errs.append(f"Zeile {i+1}: unbekannter Metadaten-String {key!r}")
        return errs
    if valid:
        errs.append(f"fehlende Metadaten: {valid}")
        return errs
    for k, v in meta.items():
        if len(v) > VAL_LIMIT:
            errs.append(f"{k}: Wert {len(v)} Zeichen > {VAL_LIMIT}")
    body = content[body_start:]
    for i, l in enumerate(body):
        if len(l.rstrip("\n")) > LINE_LIMIT:
            errs.append(
                f"Textzeile {len(l.rstrip())} Zeichen > {LINE_LIMIT}: {l.strip()[:50]}"
            )
    # jedes structure-Element muss einen [X]-Block haben
    elems = list(dict.fromkeys(meta["structure"].replace(" ", "").split(",")))
    present = [
        l.strip()[1:-1].strip()
        for l in body
        if l.strip().startswith("[") and l.strip().endswith("]")
    ]
    for e in elems:
        if e not in present:
            errs.append(f"structure-Element [{e}] fehlt im Textkörper")
    for p in present:
        if p not in elems:
            errs.append(f"Block [{p}] steht nicht in structure")
    return errs


ok = 0
todo = sorted(glob.glob(sys.argv[1] + "/*.txt.todo"))
for f in sorted(glob.glob(sys.argv[1] + "/*.txt")):
    e = check(f)
    print(("  OK   " if not e else "  FEHL ") + os.path.basename(f))
    for x in e:
        print("         -", x)
    ok += not e
print(f"\n{ok}/{len(glob.glob(sys.argv[1]+'/*.txt'))} Dateien parserkonform")
if todo:
    print(f"{len(todo)} unfertig (.txt.todo), brauchen Entscheidung:")
    for t in todo:
        print("   -", os.path.basename(t))
