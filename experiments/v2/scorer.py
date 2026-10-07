"""v2 mechanical scorer (EXPERIMENT_V2.md). No LLM judge anywhere in here.

Domain A: every `SOURCE: <url> | QUOTE: "<text>" | CLAIM: ...` line is one claim.
  verified        URL fetched and the quote is on the page
  dead_url        DNS failure or 404/410 from every route
  quote_missing   page fetched (>= MIN_PAGE_CHARS of text) but the quote is not on it
  unverifiable    blocked from every route, or the page has too little text to judge
Domain B: every `ISSUE: line <n> | ...` line is one reported issue, matched by
line to the frozen answer key.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import verify_v2 as v  # noqa: E402  (fetch_full: home proxy -> direct -> curl, PDFs, GitHub README)

MIN_PAGE_CHARS = 500
NGRAM = 5
NGRAM_SHARE = 0.9

_Q = "\"“”„"
SOURCE_RE = re.compile(
    rf"SOURCE:\s*<?(?P<url>https?://[^\s|>]+)>?\s*\|\s*QUOTE:\s*[{_Q}](?P<quote>.+?)[{_Q}]\s*\|\s*CLAIM:\s*(?P<claim>.*)",
    re.I)
SOURCE_LOOSE_RE = re.compile(r"SOURCE:\s*<?(https?://[^\s|>]+)", re.I)
NOSRC_RE = re.compile(r"NO_SOURCE_FOUND\s*:?\s*(.*)", re.I)
URL_RE = re.compile(r"https?://[^\s)\]>|\"'`]+")
ISSUE_RE = re.compile(r"ISSUE:\s*lines?\s*(\d+)", re.I)
NOISSUE_RE = re.compile(r"\bNO_ISSUES_FOUND\b", re.I)

_FETCH = {}


def _strip_md(line: str) -> str:
    return re.sub(r"[*`]", "", line).strip(" -\t>")


def parse_a(text: str) -> dict:
    claims, no_source, malformed = [], [], 0
    for raw in text.splitlines():
        line = _strip_md(raw)
        m = SOURCE_RE.search(line)
        if m:
            claims.append({"url": m["url"].rstrip(".,;"), "quote": m["quote"].strip(), "claim": m["claim"].strip()})
            continue
        if SOURCE_LOOSE_RE.search(line):
            malformed += 1
            continue
        n = NOSRC_RE.search(line)
        if n:
            no_source.append(n.group(1).strip())
    cited = {c["url"] for c in claims}
    loose_urls = sorted({u.rstrip(".,;") for u in URL_RE.findall(text)} - cited)
    return {"claims": claims, "no_source": no_source, "malformed_source_lines": malformed,
            "urls_outside_format": loose_urls}


def _words(t: str) -> list:
    return re.findall(r"[a-z0-9]+", v._norm(t))


def quote_on_page(quote: str, page: str) -> bool:
    if v.fuzzy_find(page, quote) >= 0:  # exact, punctuation/case/whitespace-insensitive
        return True
    qw = _words(quote)
    if len(qw) < NGRAM:
        return False
    pw = " " + " ".join(_words(page)) + " "
    grams = [" " + " ".join(qw[i:i + NGRAM]) + " " for i in range(len(qw) - NGRAM + 1)]
    return sum(g in pw for g in grams) / len(grams) >= NGRAM_SHARE


def fetch(url: str) -> tuple:
    if url not in _FETCH:
        try:
            _FETCH[url] = v.fetch_full(url)
        except Exception as e:  # GitHub API errors etc.: could not look
            _FETCH[url] = (None, f"error: {e}"[:200])
    return _FETCH[url]


def score_a(text: str) -> dict:
    p = parse_a(text)
    for c in p["claims"]:
        ok, page = fetch(c["url"])
        if ok is False:
            c["status"], c["note"] = "dead_url", page[:120]
        elif ok is None:
            c["status"], c["note"] = "unverifiable", page[:120]
        elif len(page.strip()) < MIN_PAGE_CHARS:
            c["status"], c["note"] = "unverifiable", f"page text only {len(page.strip())} chars"
        else:
            c["status"] = "verified" if quote_on_page(c["quote"], page) else "quote_missing"
    st = [c["status"] for c in p["claims"]]
    p["counts"] = {k: st.count(k) for k in ("verified", "dead_url", "quote_missing", "unverifiable")}
    p["failed"] = p["counts"]["dead_url"] + p["counts"]["quote_missing"]
    return p


def parse_b(text: str) -> dict:
    text = re.sub(r"[*`]", "", text)
    lines = [int(m.group(1)) for m in ISSUE_RE.finditer(text)]
    return {"issue_lines": lines, "no_issues": bool(NOISSUE_RE.search(text)) and not lines}


def score_b(text: str, fixture: str, key: dict) -> dict:
    k = key[fixture]
    p = parse_b(text)
    found, issues = set(), []
    for ln in p["issue_lines"]:
        bug = next((b["id"] for b in k["bugs"] if ln in b["lines"]), None)
        if bug and bug not in found:
            found.add(bug)
            issues.append({"line": ln, "status": "planted", "bug": bug})
        elif bug:
            issues.append({"line": ln, "status": "duplicate", "bug": bug})
        else:
            adj = k.get("adjudicated", {}).get(str(ln))
            issues.append({"line": ln, "status": adj or "unknown"})
    st = [i["status"] for i in issues]
    p.update(issues=issues, planted_found=len(found), planted_total=len(k["bugs"]),
             counts={s: st.count(s) for s in ("planted", "duplicate", "real", "fabricated", "unknown")})
    return p


if __name__ == "__main__":
    print(json.dumps(score_a(open(sys.argv[1]).read()), indent=1)[:3000])
