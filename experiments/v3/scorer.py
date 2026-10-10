"""v2 mechanical scorer (EXPERIMENT_V2.md). No LLM judge anywhere in here.

Domain A: every `SOURCE: <url> | QUOTE: "<text>" | CLAIM: ...` line is one claim.
  verified        URL fetched and the quote is on the page
  dead_url        DNS failure or 404/410 from every route
  reworded        quote not verbatim, but its numbers and most words sit together on the page
  unsupported     page fetched (>= MIN_PAGE_CHARS of text); neither verbatim nor reworded
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
SEGMENT_WINDOW = 4000      # ellipsis-joined segments must all lie within this many chars
GROUND_WINDOW = 800        # paraphrase check: numbers + words must co-occur this close
GROUND_WORD_SHARE = 0.7

# Pilot (2026-10-07): v.fetch_full capped pages at 200k chars and ran pdftotext
# -layout, which splits sentences across columns, so real quotes from long PDFs
# read as missing. Scoring uses the full text and reading-order PDF extraction.
v.PAGE_TEXT_CAP = 10**8


def _pdf_text_reading_order(data: bytes) -> str:
    import subprocess, tempfile, unicodedata
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data)
        f.flush()
        out = subprocess.run(["pdftotext", "-enc", "UTF-8", f.name, "-"], capture_output=True, timeout=120)
    t = unicodedata.normalize("NFKC", out.stdout.decode(errors="replace"))
    return re.sub(r"(\w)-\n(\w)", r"\1\2", t)  # re-join words hyphenated at line ends


v._pdf_text = _pdf_text_reading_order

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


def _segment_on_page(seg: str, page: str, pw: str) -> int:
    """Offset (in the alnum index, or -1): exact match, else >= 90% of 5-grams."""
    i = v.fuzzy_find(page, seg)
    if i >= 0:
        return i
    qw = _words(seg)
    if len(qw) < NGRAM:
        return -1
    grams = [" " + " ".join(qw[i:i + NGRAM]) + " " for i in range(len(qw) - NGRAM + 1)]
    hits = [pw.find(g) for g in grams]
    if sum(h >= 0 for h in hits) / len(grams) < NGRAM_SHARE:
        return -1
    # A near-verbatim quote must not change a number: every number-bearing word
    # of the quote has to appear near where the quote was found. Without this a
    # long quote with one altered figure would pass the 90% threshold.
    at = min(h for h in hits if h >= 0)
    window = pw[max(0, at - 1000): at + len(" ".join(qw)) + 1000]
    if any(f" {w} " not in window for w in qw if any(ch.isdigit() for ch in w)):
        return -1
    return 0  # located; position not tracked for fuzzy matches


def quote_on_page(quote: str, page: str) -> bool:
    """Verbatim, allowing '...' / '…' for omitted text: every segment must be on
    the page, and exact-located segments must lie within SEGMENT_WINDOW chars."""
    pw = " " + " ".join(_words(page)) + " "
    # v3 pilot 2: an editorial insertion like "[and]" or "[Geopolitical markets]" also
    # splits the quote, the same as an ellipsis.
    segs = [x.strip(" |") for x in re.split(r"\.\.\.|\u2026|\[[^\]]{1,80}\]", quote)]
    segs = [x for x in segs if _words(x)]
    if not segs:
        return False
    offs = []
    for seg in segs:
        o = _segment_on_page(seg, page, pw)
        if o < 0:
            return False
        offs.append(o)
    exact = [o for o in offs if o > 0]
    return not exact or max(exact) - min(exact) <= SEGMENT_WINDOW


NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
STOP = set("the a an of and or to in on for is are was were be by with as at from that this it its than per".split())


def grounded(quote: str, page: str) -> bool:
    """Not verbatim, but is it the page's content reworded? True if one window of
    the page holds every number in the quote and >= 70% of its content words.
    Pilot: models rewrote table rows as 'SQLite 700ms, DuckDB 10ms'."""
    nums = [n.replace(",", "") for n in NUM_RE.findall(quote)]
    words = {w for w in _words(quote) if w not in STOP and not w.isdigit()}
    low = page.lower()
    page_nums = [(m.start(), m.group().replace(",", "")) for m in NUM_RE.finditer(low)]
    # Pilot: a single digit ("5 per week") occurs everywhere, so it let a stale,
    # no-longer-present Let's Encrypt sentence pass as reworded. At least one
    # number must be distinctive (2+ digits or a decimal).
    if not any(len(n.replace(".", "")) >= 2 for n in nums):
        return False
    anchor = max(nums, key=len)
    anchors = [p for p, n in page_nums if n == anchor]
    for a in anchors:
        win = low[max(0, a - GROUND_WINDOW): a + GROUND_WINDOW]
        wn = {n.replace(",", "") for n in NUM_RE.findall(win)}
        if all(n in wn for n in nums):
            ww = set(_words(win))
            if not words or len(words & ww) / len(words) >= GROUND_WORD_SHARE:
                return True
    return False


CACHE = HERE.parent / "v2" / "pages_cache"   # shared with v2; local snapshot of every fetched page (third-party text: not committed)
GH_BLOB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/blob/(.+)$")


def _fetch_once(url: str) -> tuple:
    m = GH_BLOB_RE.match(url)
    target = f"https://raw.githubusercontent.com/{m[1]}/{m[2]}/{m[3]}" if m else url
    for attempt in range(4):
        try:
            ok, text = v.fetch_full(target)
        except Exception as e:  # GitHub API errors etc.: could not look
            ok, text = None, f"error: {e}"[:200]
        if ok is None and "429" in text and attempt < 3:
            import time
            time.sleep(60 * (attempt + 1))
            continue
        if ok and (m or target.split("?")[0].endswith(".md")):  # v3: any markdown URL
            text = _markdown_to_text(text)
        return ok, text
    return ok, text


def _markdown_to_text(t: str) -> str:
    """Raw GitHub files are markdown; drop link targets and emphasis so a quote of
    the rendered sentence matches (pilot: '[**Duplicate Certificate**](/docs/...)')."""
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\*\*|__|`", "", t)
    return t


def fetch(url: str) -> tuple:
    """Each URL is fetched once and snapshotted, so re-scoring is deterministic
    (pilot: repeated scoring runs got rate-limited by GitHub and turned verified
    claims into 'unverifiable'). Failures to look are not cached."""
    import hashlib
    if url in _FETCH:
        return _FETCH[url]
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    if f.exists():
        d = json.loads(f.read_text())
        _FETCH[url] = (d["ok"], d["text"])
        return _FETCH[url]
    ok, text = _fetch_once(url)
    if ok is not None:
        from datetime import datetime, timezone
        f.write_text(json.dumps({"url": url, "ok": ok, "text": text,
                                 "fetched": datetime.now(timezone.utc).isoformat()}))
    _FETCH[url] = (ok, text)
    return ok, text


def _match(quote: str, page: str) -> str:
    if quote_on_page(quote, page):
        return "verified"
    if grounded(quote, page):
        return "reworded"     # not verbatim, but the page's own numbers and words
    return "unsupported"      # neither the quote nor its numbers are on the page


def _markdown_alternate(url: str):
    """Text of <url>.md if the site serves a markdown version of the page, else None."""
    base = url.split("#")[0].split("?")[0].rstrip("/")
    if base.endswith(".md") or GH_BLOB_RE.match(url):
        return None
    ok, text = fetch(base + ".md")
    if not ok or len(text.strip()) < MIN_PAGE_CHARS or text.lstrip().lower().startswith(("<!doctype", "<html")):
        return None
    return _markdown_to_text(text)


def _rendered(url: str):
    """Text of the page after JavaScript runs (v3 pilot 2: OpenRouter's FAQ fills in its
    fee figures client-side, so the raw HTML reads 'a fee of .'). Snapshotted like fetch()."""
    import hashlib
    if GH_BLOB_RE.match(url) or url.lower().split("?")[0].endswith((".pdf", ".md")):
        return None
    key = "rendered:" + url
    f = CACHE / (hashlib.sha1(key.encode()).hexdigest() + ".json")
    if f.exists():
        d = json.loads(f.read_text())
        return d["text"] if d["ok"] else None
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(user_agent=v.BROWSER_UA, locale="en-US")
            r = pg.goto(url, wait_until="networkidle", timeout=45000)
            text = pg.inner_text("body") if r and r.status < 400 else ""
            b.close()
    except Exception as e:
        print(f"  render failed {url}: {str(e)[:100]}", flush=True)
        return None  # could not look: not cached
    ok = len(text.strip()) >= MIN_PAGE_CHARS
    from datetime import datetime, timezone
    f.write_text(json.dumps({"url": key, "ok": ok, "text": text,
                             "fetched": datetime.now(timezone.utc).isoformat()}))
    return text if ok else None


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
            c["status"] = _match(c["quote"], page)
            if c["status"] == "unsupported":
                # v3 pilot 2: docs sites (OpenAI, Cloudflare, ...) put tabbed tables only in the
                # page's markdown version (<url>.md), which is what web search often returns.
                # Same page, other representation, so a match there counts.
                for label, alt in (("the page's .md version", _markdown_alternate),
                                   ("the page rendered in a browser", _rendered)):
                    text_alt = alt(c["url"])
                    if text_alt:
                        c["status"] = _match(c["quote"], text_alt)
                        if c["status"] != "unsupported":
                            c["note"] = "matched on " + label
                            break
    st = [c["status"] for c in p["claims"]]
    p["counts"] = {k: st.count(k) for k in ("verified", "reworded", "unsupported", "dead_url", "unverifiable")}
    p["failed"] = p["counts"]["dead_url"] + p["counts"]["unsupported"]
    return p


def parse_b(text: str) -> dict:
    text = re.sub(r"[*`]", "", text)
    issues = [(int(m.group(1)), m.group(2).strip()) for m in
              re.finditer(r"ISSUE:\s*lines?\s*(\d+)[^|\n]*\|?\s*([^\n]*)", text, re.I)]
    return {"reported": issues, "no_issues": bool(NOISSUE_RE.search(text)) and not issues}


def adj_key(fixture: str, line: int, desc: str) -> str:
    import hashlib
    return hashlib.sha1(f"{fixture}|{line}|{' '.join(desc.lower().split())}".encode()).hexdigest()[:16]


def score_b(text: str, fixture: str, key: dict, adjudications: dict) -> dict:
    k = key[fixture]
    p = parse_b(text)
    found, issues = set(), []
    for ln, desc in p["reported"]:
        d = desc.lower()
        bug = next((b["id"] for b in k["bugs"] if ln in b["lines"] and any(w in d for w in b["keywords"])), None)
        status = "planted" if bug else None
        if not bug:
            verdict = adjudications.get(adj_key(fixture, ln, desc), {}).get("verdict")
            if verdict and verdict.startswith("planted:"):
                bug, status = verdict.split(":", 1)[1], "planted"
            else:
                status = verdict or "unknown"
        if status == "planted":
            status = "duplicate" if bug in found else "planted"
            found.add(bug)
        issues.append({"line": ln, "desc": desc, "status": status, "bug": bug, "key": adj_key(fixture, ln, desc)})
    st = [i["status"] for i in issues]
    p.update(issues=issues, planted_found=len(found), planted_total=len(k["bugs"]),
             counts={s: st.count(s) for s in ("planted", "duplicate", "real", "nitpick", "fabricated", "unknown")})
    p["fabricated_share"] = (p["counts"]["fabricated"] / len(issues)) if issues else 0.0
    return p


if __name__ == "__main__":
    print(json.dumps(score_a(open(sys.argv[1]).read()), indent=1)[:3000])
