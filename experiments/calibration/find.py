import sys, re, glob
def norm(t): return re.sub(r"\s+", " ", t.replace("’","'").replace("“",'"').replace("”",'"').replace("‘","'")).lower()
page = norm(open(glob.glob("pages/" + sys.argv[1] + "*")[0]).read())
for probe in sys.argv[2:]:
    i = page.find(norm(probe))
    print(("FOUND   " if i >= 0 else "MISSING ") + probe + ("" if i < 0 else "   …" + page[max(0,i-60):i+len(probe)+60] + "…"))
