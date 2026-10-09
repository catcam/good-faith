"""Batch version of `adjudicate.py set`: reads lines 'key verdict note...' from stdin."""
import json, sys
from pathlib import Path
ADJ = Path(__file__).resolve().parent / "adjudications.json"
a = json.loads(ADJ.read_text()) if ADJ.exists() else {}
n = 0
for line in sys.stdin:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    k, v, *note = line.split(" ", 2)
    assert v in ("real", "nitpick", "fabricated") or v.startswith("planted:"), v
    a[k] = {"verdict": v, "note": note[0] if note else "", "by": "Claude (Opus 5.5), blind to condition and model"}
    n += 1
ADJ.write_text(json.dumps(a, indent=1, sort_keys=True))
print(n, "labels written")
