import json, sys
def cmp(sample, hand, judge, label, verbose=True):
    H = json.load(open(hand)); J = {x["trial_id"]: x["claims"] for x in json.load(open(judge))}
    S = json.load(open(sample)); th = [0, 0, 0]; tj = [0, 0, 0]; agree = 0; fp = fn = tp = 0; any_agree = 0
    print(f"--- {label}")
    for s in S:
        t = s["trial_id"]; h = H[t]; j = J[t]
        jc = [sum(c["verdict"] == v for c in j) for v in ("supported", "fabricated", "undetermined")]
        hc = [h["supported"], h["fabricated"], h["undetermined"]]
        for i in range(3): th[i] += hc[i]; tj[i] += jc[i]
        agree += hc[1] == jc[1]; any_agree += (hc[1] > 0) == (jc[1] > 0)
        tp += min(hc[1], jc[1]); fp += max(0, jc[1] - hc[1]); fn += max(0, hc[1] - jc[1])
        diff = (hc[1] > 0) != (jc[1] > 0)
        if verbose and (diff or hc[1] != jc[1]):
            print(f"  {t} {s['condition']} hand {hc} judge {jc}{'  <-- passage-level DISAGREE' if diff else ''}")
            for c in j:
                if c["verdict"] == "fabricated": print("     judge FAB:", c.get("claim", "")[:95], "|", c.get("why", "")[:85])
    print(f"  totals hand {th} judge {tj} | passages agree on 'any fabrication': {any_agree}/{len(S)} | exact fab count {agree}/{len(S)} | claim-level TP {tp} FP {fp} FN {fn}")
    return tp, fp, fn, any_agree, len(S)

r = [cmp("sample.json", "hand_labels.json", "judge_claims_v2d_s1.json", "sample 1 (tuned on)"),
     cmp("sample2.json", "hand_labels2.json", "judge_claims_v2d_s2.json", "sample 2 (tuned on)"),
     cmp("sample3.json", "hand_labels3.json", "judge_claims_v2d_s3.json", "sample 3 (tuned on in round 3)"),
     cmp("sample4.json", "hand_labels4.json", "judge_claims_v2d_s4.json", "sample 4 (HELD OUT - drawn after all changes)")]
