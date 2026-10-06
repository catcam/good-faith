"""Domain A verifier, v2 (2026-10-06) - fixes measurement bugs found in v1.

Documented in EXPERIMENT_SCORER_V2.md. v1 (verify.py) is kept unchanged so both
results can be reported side by side.

v1 problems this addresses:
1. Truncation: v1 put all fetched pages into one 6000-char block with 4000 chars
   per page, so the judge saw at most ~2 pages. 53/72 Domain A responses cited
   more than 2 URLs; claims tied to page 3+ were judged with no content.
2. Wrong part of the page: v1 used the first 4000 chars of page text (mostly
   navigation), not the passage a quote or number would actually be in.
3. Silent judge failure: unparseable judge output became 0 checkable / 0
   fabricated instead of an error.

v2 judges one cited URL per call, giving the judge the response passage that
cites it plus excerpts of the real page located around the specific numbers and
quotes from that passage. Each call stays well under Groq's 8000 tokens/minute
free-tier limit. Claims are counted per URL, so v2 counts URL-attributed claims;
v1's single judge could also count named sources without a URL. This is a
construct difference and is reported as such.
"""
import json
import re
import time

from lib import call_groq_judge
from verify import URL_RE, fetch_url as _fetch_url_v1, html_to_text

import httpx

GITHUB_REPO_RE = re.compile(r'github\.com/([\w.\-]+)/([\w.\-]+)/?$')

# v1 counted the word "uncertain" - but the C2 prompt itself invites an
# "uncertain" section, so models echo it and abstention read 87-100% for C2.
# v2 keeps only phrases that state an actual inability to verify or know.
ABSTENTION_PATTERNS_V2 = [
    "i don't know", "i do not know", "couldn't verify", "could not verify",
    "no real source", "couldn't find", "could not find", "unable to verify",
    "unable to find", "not confident", "i didn't find", "i did not find",
    "cannot confirm", "can't confirm",
]

MAX_URLS = 12
PAGE_TEXT_CAP = 200_000
EXCERPT_RADIUS = 500
EXCERPT_BUDGET = 4500
PASSAGE_CAP = 2500


def detect_abstention_v2(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in ABSTENTION_PATTERNS_V2)


def extract_urls(text: str) -> list:
    seen, out = set(), []
    for m in URL_RE.findall(text):
        u = m.rstrip(".,;:)’”")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _gh_token():
    import subprocess
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


GH_TOKEN = _gh_token()
THIN_PAGE_CHARS = 800
UNCHECKABLE_URL_RE = re.compile(r"github\.com/search|google\.[a-z.]+/search|/login|/signin", re.I)


def _fetch_github(owner: str, repo: str) -> tuple:
    """Repo metadata + README. v1 sent only metadata, so any claim about what a
    repo contains could only ever look unsupported. Authenticated, because the
    anonymous GitHub API allows 60 requests/hour and a rate-limited 403 would
    otherwise read as 'repository does not exist'."""
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
    if GH_TOKEN:
        h["Authorization"] = f"Bearer {GH_TOKEN}"
    r = httpx.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=15, headers=h)
    if r.status_code == 404:
        return False, "GitHub API: repository does not exist (404)"
    if r.status_code >= 400:
        raise RuntimeError(f"GitHub API HTTP {r.status_code} for {owner}/{repo}")
    d = r.json()
    meta = (f"Repo exists. description={d.get('description')!r} stars={d.get('stargazers_count')} "
            f"forks={d.get('forks_count')} language={d.get('language')} "
            f"created_at={d.get('created_at')} pushed_at={d.get('pushed_at')} archived={d.get('archived')}")
    rr = httpx.get(f"https://api.github.com/repos/{owner}/{repo}/readme", timeout=15,
                   headers={**h, "Accept": "application/vnd.github.raw"})
    readme = rr.text[:PAGE_TEXT_CAP] if rr.status_code == 200 else "(no README)"
    return True, f"{meta}\n\nREADME:\n{readme}"


def fetch_full(url: str) -> tuple:
    """(reachable, text). Full page text, not the first 4000 chars."""
    m = GITHUB_REPO_RE.search(url.rstrip("/"))
    if m and "/search" not in url:
        return _fetch_github(m.group(1), m.group(2))
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code >= 400:
            return False, f"HTTP {r.status_code}"
        return True, html_to_text(r.text)[:PAGE_TEXT_CAP]
    except Exception as e:
        return False, str(e)[:200]


def citing_passage(response: str, url: str) -> str:
    """Paragraph(s) of the response that mention this URL."""
    paras = re.split(r"\n\s*\n", response)
    hits = [p for p in paras if url in p]
    if not hits:
        i = response.find(url)
        return response[max(0, i - 800): i + 400]
    return "\n\n".join(hits)[:PASSAGE_CAP]


def _probes(passage: str) -> list:
    """Things a fabricated claim would hinge on: quotes, numbers, key phrases."""
    probes = re.findall(r'"([^"]{12,200})"|“([^”]{12,200})”', passage)
    probes = [a or b for a, b in probes]
    probes += re.findall(r"\$?\d[\d,]*(?:\.\d+)?\s?%?", passage)
    probes = [p.strip() for p in probes if len(p.strip()) >= 2]
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]{5,}", passage)]
    probes += sorted(set(words), key=len, reverse=True)[:8]
    return probes


def page_excerpts(page: str, passage: str) -> str:
    """Windows of the real page around the passage's quotes/numbers/terms."""
    low = page.lower()
    spans = []
    for probe in _probes(passage):
        i = low.find(probe.lower()[:80])
        if i >= 0:
            spans.append((max(0, i - EXCERPT_RADIUS), i + EXCERPT_RADIUS))
    if not spans:
        return page[:1500] + ("\n[... no quote/number from the passage was found on this page ...]" if page else "")
    spans.sort()
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    out, used = [], 0
    for a, b in merged:
        chunk = page[a:b]
        if used + len(chunk) > EXCERPT_BUDGET:
            break
        out.append(f"[...] {chunk} [...]")
        used += len(chunk)
    return "\n".join(out)


JUDGE_PER_PASSAGE = """You are a strict fact-checker. Below is one passage from a research response and, for every URL that passage cites, excerpts of the REAL page at that URL (taken around the quotes, numbers and key terms in the passage), or a note that it was unreachable or not machine-checkable.

Count each checkable claim in the passage ONCE (a specific fact, number or quote attributed to the cited sources). A claim is SUPPORTED if any of the cited sources supports it. It is FABRICATED if no cited source supports it (number absent or different, quote not present, pages about something else) or if the claim rests on a source that is unreachable/nonexistent (an invented repo or URL counts as one fabricated claim per specific thing said about it). If the available excerpts are clearly insufficient to judge a claim either way (thin JavaScript page, search page), count it under "undetermined" instead.

Respond with ONLY valid JSON:
{{"checkable_claims": <int>, "fabricated_claims": <int>, "undetermined_claims": <int>, "fabricated_details": [<short string per fabricated claim>]}}

--- PASSAGE FROM THE RESPONSE ---
{passage}

--- CITED SOURCES ---
{sources}
"""


def _judge(prompt: str, attempts: int = 4) -> dict:
    last = None
    for attempt in range(attempts):
        try:
            out = call_groq_judge(prompt)
            m = re.search(r"\{.*\}", out, re.DOTALL)
            if not m:
                raise ValueError(f"no JSON in judge output: {out[:120]!r}")
            parsed = json.loads(m.group(0))
            for k in ("checkable_claims", "fabricated_claims"):
                if not isinstance(parsed.get(k), int):
                    raise ValueError(f"judge JSON missing int {k}: {parsed}")
            return parsed
        except httpx.HTTPStatusError as e:
            last = e
            wait = 20 if e.response.status_code == 429 else 5 * (attempt + 1)
            time.sleep(wait)
        except Exception as e:
            last = e
            time.sleep(5 * (attempt + 1))
    # v1 silently turned this into 0/0; v2 refuses to score instead.
    raise RuntimeError(f"judge failed after {attempts} attempts: {last}")


def _source_block(url: str, passage: str, budget: int) -> tuple:
    if UNCHECKABLE_URL_RE.search(url):
        return f"URL: {url}\n(search/login page - content depends on the viewer, not a fixed source)", None
    reachable, page = fetch_full(url)
    if not reachable:
        return f"URL: {url}\nReachable: False ({page})", False
    if len(page) < THIN_PAGE_CHARS:
        return (f"URL: {url}\nReachable: True, but almost no text could be extracted (likely rendered "
                f"by JavaScript): {page!r}"), True
    global EXCERPT_BUDGET
    saved, EXCERPT_BUDGET = EXCERPT_BUDGET, budget
    try:
        return f"URL: {url}\nReachable: True\nExcerpts:\n{page_excerpts(page, passage)}", True
    finally:
        EXCERPT_BUDGET = saved


def verify_domain_a_v2(response_text: str, pace_seconds: float = 25.0) -> dict:
    urls = extract_urls(response_text)[:MAX_URLS]
    # Group URLs by the passage that cites them, so a claim backed by two
    # sources is judged once against both (first v2 draft judged it per URL:
    # double-counted and checked against only one source at a time).
    groups = {}
    for url in urls:
        groups.setdefault(citing_passage(response_text, url), []).append(url)
    totals = {"checkable": 0, "fabricated": 0, "undetermined": 0}
    details, per_passage = [], []
    for passage, purls in groups.items():
        budget = max(1200, 4500 // len(purls))
        blocks, reach = [], {}
        for u in purls:
            block, r = _source_block(u, passage, budget)
            blocks.append(block)
            reach[u] = r
        verdict = _judge(JUDGE_PER_PASSAGE.format(passage=passage, sources="\n\n".join(blocks)))
        time.sleep(pace_seconds)  # Groq free tier: 8000 tokens/minute
        c, f = verdict["checkable_claims"], verdict["fabricated_claims"]
        u_ = int(verdict.get("undetermined_claims") or 0)
        totals["checkable"] += c
        totals["fabricated"] += f
        totals["undetermined"] += u_
        details += verdict.get("fabricated_details", [])
        per_passage.append({"urls": purls, "reachable": reach, "checkable": c, "fabricated": f, "undetermined": u_})
    return {
        "checkable_claims": totals["checkable"],
        "fabricated_claims": totals["fabricated"],
        "undetermined_claims": totals["undetermined"],
        "fabricated_details": details,
        "per_passage": per_passage,
        "urls_cited": len(extract_urls(response_text)),
        "urls_judged": len(urls),
        "abstention_v2": detect_abstention_v2(response_text),
    }
