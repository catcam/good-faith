"""Run the v2 judge on calibration passages (output not printed, so hand
labels stay blind). Uses verify_v2.judge_passage - the same code path as the
real re-scoring."""
import json, sys, time
sys.path.insert(0, "..")
import verify_v2 as v

out = []
for s in json.load(open(sys.argv[1] if len(sys.argv) > 1 else "sample.json")):
    t0 = time.time()
    claims = v.judge_passage(s["passage"], s["urls"] + v.extract_urls(s["passage"]))
    print(f"{s['trial_id']}: {len(claims)} claims in {time.time()-t0:.0f}s", flush=True)
    out.append({"trial_id": s["trial_id"], "claims": claims})
    time.sleep(55)  # Groq counts prompt + max_tokens against 8000 tokens/minute
json.dump(out, open(sys.argv[2] if len(sys.argv) > 2 else "judge_claims.json", "w"), indent=1)
print("judge done:", len(out), "passages")
