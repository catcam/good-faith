import json, sys, os, re
sys.path.insert(0, "..")
import verify_v2 as v
os.makedirs("pages", exist_ok=True)
for s in json.load(open(sys.argv[1] if len(sys.argv) > 1 else "sample.json")):
    for u in s["urls"]:
        fn = "pages/" + re.sub(r"[^A-Za-z0-9]+", "_", u)[:120] + ".txt"
        if os.path.exists(fn): continue
        if v.UNCHECKABLE_URL_RE.search(u):
            ok, txt = None, "(search/login page)"
        else:
            ok, txt = v.fetch_full(u)
        open(fn, "w").write(f"URL: {u}\nREACHABLE: {ok}\n\n{txt}")
        print(ok, len(txt), u[:90])
