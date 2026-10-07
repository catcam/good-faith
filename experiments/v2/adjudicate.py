"""Blind adjudication helper: lists issues the scorer could not classify, without
model or condition, shuffled. Labels go into adjudications.json by key.
  python adjudicate.py list <phase>
  python adjudicate.py set <key> <verdict> [note]   verdict: real|nitpick|fabricated|planted:<id>"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADJ = HERE / "adjudications.json"


def load():
    return json.loads(ADJ.read_text()) if ADJ.exists() else {}


if sys.argv[1] == "list":
    S = json.loads((HERE / f"scored_{sys.argv[2]}.json").read_text())
    items = {}
    for s in S:
        if s["domain"] != "b":
            continue
        for i in s["score"]["issues"]:
            if i["status"] == "unknown":
                items[i["key"]] = (s["task"], i["line"], i["desc"])
    keys = sorted(items)
    random.Random(0).shuffle(keys)
    for k in keys:
        f, ln, d = items[k]
        src = (HERE / "fixtures" / f).read_text().splitlines()
        print(f"[{k}] {f}:{ln}  `{src[ln - 1].strip() if 0 < ln <= len(src) else '?'}`\n    {d}")
    print(len(keys), "unknown")
elif sys.argv[1] == "set":
    a = load()
    a[sys.argv[2]] = {"verdict": sys.argv[3], "note": " ".join(sys.argv[4:]), "by": "Claude (Opus 5.5), blind to condition and model"}
    ADJ.write_text(json.dumps(a, indent=1, sort_keys=True))
