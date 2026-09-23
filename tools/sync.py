#!/usr/bin/env python3
"""rclone-Sync mit erzwungenem Dry-Run.

  python3 tools/sync.py BUCH           nur Dry-Run, ändert nichts
  python3 tools/sync.py BUCH --go      Dry-Run zeigen, dann wirklich syncen

`rclone sync` spiegelt: was lokal fehlt, wird im Remote GELÖSCHT. Darum sieht
man hier immer erst, was passieren würde.
"""

import os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_config


def run(cfg, dry):
    cmd = ["rclone", "sync", cfg["songrepo"], cfg["remote"], "-v"]
    if dry:
        cmd.append("--dry-run")
    print("$ " + " ".join(cmd) + "\n")
    return subprocess.run(cmd).returncode


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = load_config(sys.argv[1])
    if not cfg.get("remote"):
        sys.exit("Kein remote in der Konfiguration.")
    print("=== DRY-RUN ===")
    if run(cfg, True) != 0:
        sys.exit("Dry-Run fehlgeschlagen.")
    if "--go" not in sys.argv:
        print("\nNichts geändert. Mit --go wirklich ausführen.")
        return
    print("\n=== SYNC ===")
    if run(cfg, False) != 0:
        sys.exit("Sync fehlgeschlagen.")
    print("\n=== GEGENPROBE ===")
    subprocess.run(["rclone", "check", cfg["songrepo"], cfg["remote"]])


if __name__ == "__main__":
    main()
