"""v4 trial runner (EXPERIMENT_V4.md): like v3, but with NO web search, so every citation
comes from the model's memory. Scorer is v3's (v2 + the pilot-2 fixes).

  python run_v3.py matrix pilot|main     write matrix_<phase>.json (shuffled, seeded)
  python run_v3.py run pilot|main        run pending trials, resumable
  python run_v3.py score pilot|main      (re)score every raw trial mechanically
"""
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "v2"))
sys.path.insert(0, str(HERE.parent / "v3"))  # v3/scorer.py wins over v2/scorer.py
import lib  # noqa: E402
import prompts  # noqa: E402
import scorer  # noqa: E402
from run_v2 import MODELS, STOP_BALANCE, call  # noqa: E402

RAW = HERE / "raw"
TASKS = json.loads((HERE / "tasks_v4.json").read_text())


def make_matrix(phase: str) -> list:
    conds, reps = (["c0"], 1) if phase == "pilot" else (["c0", "c2"], 5)
    ids = [t["id"] for t in TASKS]
    rows = [{"domain": "a", "task": t, "model": m, "condition": c, "rep": r}
            for m in MODELS for t in ids for c in conds for r in range(reps)]
    random.Random(f"good-faith-v4-{phase}").shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["trial_id"] = f"{phase[0]}{i:04d}"
    (HERE / f"matrix_{phase}.json").write_text(json.dumps(rows, indent=1))
    return rows


def run(phase: str) -> None:
    RAW.mkdir(exist_ok=True)
    for row in json.loads((HERE / f"matrix_{phase}.json").read_text()):
        out = RAW / f"{row['trial_id']}.json"
        if out.exists():
            continue
        bal = lib.openrouter_balance()
        if bal < STOP_BALANCE:
            print(f"STOP: balance ${bal:.2f} < ${STOP_BALANCE}", flush=True)
            return
        task = next(t for t in TASKS if t["id"] == row["task"])
        prompt = prompts.build_prompt(task["prompt"], row["condition"], "a")
        for attempt in range(4):
            try:
                resp = call(row["model"], prompt, web=False)
                if resp["content"].strip():
                    break
                raise RuntimeError("empty content")
            except Exception as e:
                print(f"  {row['trial_id']} attempt {attempt + 1}: {str(e)[:150]}", flush=True)
                import time
                time.sleep(20 * (attempt + 1))
        else:
            continue
        out.write_text(json.dumps({**row, "prompt": prompt, "response": resp,
                                   "ts": datetime.now(timezone.utc).isoformat()}, indent=1))
        print(f"{row['trial_id']} {row['condition']} {row['model']} {row['task']} "
              f"cost={resp['usage'].get('cost')} chars={len(resp['content'])}", flush=True)


def score(phase: str) -> None:
    scored = []
    for row in json.loads((HERE / f"matrix_{phase}.json").read_text()):
        f = RAW / f"{row['trial_id']}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        s = scorer.score_a(d["response"]["content"])
        scored.append({**row, "cost": d["response"]["usage"].get("cost"), "score": s})
        print(row["trial_id"], row["task"], row["model"], s["counts"], flush=True)
    (HERE / f"scored_{phase}.json").write_text(json.dumps(scored, indent=1))


if __name__ == "__main__":
    cmd, phase = sys.argv[1], sys.argv[2]
    if cmd == "matrix":
        print(len(make_matrix(phase)), "trials")
    elif cmd == "run":
        run(phase)
    elif cmd == "score":
        score(phase)
