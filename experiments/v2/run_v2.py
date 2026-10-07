"""v2 trial runner (EXPERIMENT_V2.md).

  python run_v2.py matrix pilot|main [reps]   write matrix_<phase>.json (shuffled, seeded)
  python run_v2.py run pilot|main [limit]     run pending trials, resumable
  python run_v2.py score pilot|main           (re)score every raw trial mechanically

Model call settings are v1's (max_tokens 4000, reasoning off, OpenRouter web
plugin for Domain A), plus usage accounting so the real cost per trial is known.
"""
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import lib  # noqa: E402
import prompts  # noqa: E402
import scorer  # noqa: E402

MODELS = ["moonshotai/kimi-k3", "z-ai/glm-5.1", "qwen/qwen3.6-plus", "deepseek/deepseek-chat-v3.1"]
STOP_BALANCE = 5.0
RAW = HERE / "raw"
FIX = HERE / "fixtures"


def call(model: str, prompt: str, web: bool) -> dict:
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": 4000, "reasoning": {"enabled": False}, "usage": {"include": True}}
    if web:
        payload["plugins"] = [{"id": "web"}]
    r = httpx.post("https://openrouter.ai/api/v1/chat/completions",
                   headers={"Authorization": f"Bearer {lib.OPENROUTER_KEY}"}, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    msg = data["choices"][0]["message"]
    return {"content": msg.get("content") or "", "usage": data.get("usage", {}),
            "provider": data.get("provider"), "id": data.get("id")}


def make_matrix(phase: str, reps: int = 1) -> list:
    tasks = json.loads((HERE / "tasks_a.json").read_text())[phase]
    fixtures = sorted(f.name for f in FIX.glob(("p" if phase == "pilot" else "m") + "*.py"))
    a_conds = ["c0", "c2"] if phase == "pilot" else ["c0", "c1", "c2"]
    rows = []
    for rep in range(reps):
        for m in MODELS:
            rows += [{"domain": "a", "task": t["id"], "model": m, "condition": c, "rep": rep} for t in tasks for c in a_conds]
            rows += [{"domain": "b", "task": f, "model": m, "condition": c, "rep": rep}
                     for f in fixtures for c in ("c0", "c1", "c2")]
    random.Random(f"good-faith-v2-{phase}").shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["trial_id"] = f"{phase[0]}{i:04d}"
    (HERE / f"matrix_{phase}.json").write_text(json.dumps(rows, indent=1))
    return rows


def task_text(row: dict) -> str:
    if row["domain"] == "a":
        t = next(t for ph in json.loads((HERE / "tasks_a.json").read_text()).values() for t in ph if t["id"] == row["task"])
        return t["prompt"]
    return prompts.fixture_task_text((FIX / row["task"]).read_text())


def run(phase: str, limit: int = 10**9) -> None:
    rows = json.loads((HERE / f"matrix_{phase}.json").read_text())
    RAW.mkdir(exist_ok=True)
    done = 0
    for row in rows:
        out = RAW / f"{row['trial_id']}.json"
        if out.exists() or done >= limit:
            continue
        bal = lib.openrouter_balance()
        if bal < STOP_BALANCE:
            print(f"STOP: balance ${bal:.2f} < ${STOP_BALANCE}", flush=True)
            return
        prompt = prompts.build_prompt(task_text(row), row["condition"], row["domain"])
        for attempt in range(4):
            try:
                resp = call(row["model"], prompt, web=row["domain"] == "a")
                if resp["content"].strip():
                    break
                raise RuntimeError("empty content")
            except Exception as e:
                print(f"  {row['trial_id']} attempt {attempt + 1}: {str(e)[:150]}", flush=True)
                time.sleep(20 * (attempt + 1))
        else:
            continue
        out.write_text(json.dumps({**row, "prompt": prompt, "response": resp,
                                   "ts": datetime.now(timezone.utc).isoformat()}, indent=1))
        done += 1
        print(f"{row['trial_id']} {row['domain']} {row['condition']} {row['model']} "
              f"cost={resp['usage'].get('cost')} chars={len(resp['content'])}", flush=True)


def score(phase: str) -> None:
    key = json.loads((HERE / "answer_key.json").read_text())
    rows = json.loads((HERE / f"matrix_{phase}.json").read_text())
    scored = []
    for row in rows:
        f = RAW / f"{row['trial_id']}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        text = d["response"]["content"]
        s = scorer.score_a(text) if row["domain"] == "a" else scorer.score_b(text, row["task"], key)
        scored.append({**row, "cost": d["response"]["usage"].get("cost"), "score": s})
        print(row["trial_id"], row["domain"], row["condition"], s["counts"], flush=True)
    (HERE / f"scored_{phase}.json").write_text(json.dumps(scored, indent=1))


if __name__ == "__main__":
    cmd, phase = sys.argv[1], sys.argv[2]
    if cmd == "matrix":
        print(len(make_matrix(phase, int(sys.argv[3]) if len(sys.argv) > 3 else 1)), "trials")
    elif cmd == "run":
        run(phase, int(sys.argv[3]) if len(sys.argv) > 3 else 10**9)
    elif cmd == "score":
        score(phase)
