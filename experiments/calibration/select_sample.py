"""Calibration sample for the Domain A judge (EXPERIMENT_SCORER_V2.md).
Fixed seed, chosen before looking at any v2 verdicts: 4 responses per
condition (c0/c1/c2) among those citing at least one URL, spread over models,
one citing passage per response."""
import csv, json, random, sys
sys.path.insert(0, "..")
from verify_v2 import extract_urls, citing_passage

random.seed(20261006)
meta = {r["trial_id"]: r for r in csv.DictReader(open("../results/scored.csv"))}
sample = []
for cond in ("c0", "c1", "c2"):
    pool = [t for t, m in sorted(meta.items()) if m["domain"] == "a" and m["condition"] == cond
            and extract_urls(json.load(open(f"../raw/{t}.json"))["response"])]
    random.shuffle(pool)
    models_used, picked = set(), []
    for t in pool:
        if meta[t]["model"] in models_used and len(models_used) < 4:
            continue
        models_used.add(meta[t]["model"]); picked.append(t)
        if len(picked) == 4:
            break
    for t in picked:
        resp = json.load(open(f"../raw/{t}.json"))["response"]
        groups = {}
        for u in extract_urls(resp)[:12]:
            groups.setdefault(citing_passage(resp, u), []).append(u)
        passage = random.choice(sorted(groups))
        sample.append({"trial_id": t, "condition": cond, "model": meta[t]["model"],
                       "task_id": meta[t]["task_id"], "passage": passage, "urls": groups[passage]})
json.dump(sample, open("sample.json", "w"), indent=1)
for s in sample: print(s["trial_id"], s["condition"], s["model"].split("/")[1], len(s["urls"]), "URLs |", s["passage"][:90].replace("\n", " "))
