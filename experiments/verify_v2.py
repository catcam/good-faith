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

import os

from lib import GROQ_KEY, OPENROUTER_KEY

# JUDGE_BACKEND=openrouter sends the same model and settings through OpenRouter,
# pinned to Groq as the provider (no fallback), so the judge is the same
# inference engine. Added 2026-10-07 after the Groq free tier hit its daily
# token cap mid-calibration.
JUDGE_BACKEND = os.environ.get("JUDGE_BACKEND", "groq")


def call_groq_judge(prompt: str) -> str:
    if JUDGE_BACKEND == "openrouter":
        r = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 2500, "temperature": 0, "reasoning": {"effort": "low"},
                  "provider": {"order": ["Groq"], "allow_fallbacks": False}},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    # Same judge model and settings as lib.call_groq_judge (v1), but a larger
    # completion budget: v2 returns one entry per claim, which can exceed v1's
    # 1500 tokens for claim-dense passages.
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 2500, "temperature": 0, "reasoning_effort": "low"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
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
EXCERPT_BUDGET = 5000
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
HOME_PROXY = "socks5://127.0.0.1:1080"
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/129.0 Safari/537.36")


def _pdf_text(data: bytes) -> str:
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data)
        f.flush()
        out = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, timeout=60)
    return out.stdout.decode(errors="replace")
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
    # Fetch through the residential home proxy first: from the datacenter IP,
    # reddit/substack and others answer 403 (verified 2026-10-06), which v1
    # scored as "unreachable" = fabricated even though the source is real.
    last = None
    for proxy in (HOME_PROXY, None):
        try:
            with httpx.Client(proxy=proxy, timeout=25, follow_redirects=True,
                              headers={"User-Agent": BROWSER_UA}) as c:
                r = c.get(url)
            if r.status_code in (404, 410):
                return False, f"HTTP {r.status_code}"
            if r.status_code >= 400:
                last = f"HTTP {r.status_code}"
                continue
            ctype = r.headers.get("content-type", "")
            if "pdf" in ctype or url.lower().split("?")[0].endswith(".pdf"):
                return True, _pdf_text(r.content)[:PAGE_TEXT_CAP]
            return True, html_to_text(r.text)[:PAGE_TEXT_CAP]
        except Exception as e:
            last = str(e)[:200]
    # Bot protection (Cloudflare) fingerprints the Python client: substack and
    # skemman.is answer httpx with 403 but curl through the same proxy with 200
    # (verified 2026-10-06). Last try with curl before giving up.
    curl_ok, curl_text = _curl_fetch(url)
    if curl_ok:
        return True, curl_text
    # Blocked or erroring from every route: we could not look, which is not the
    # same as the source not existing.
    return None, f"could not fetch ({last}; curl: {curl_text})"


def _curl_fetch(url: str) -> tuple:
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile() as f:
        r = subprocess.run(["curl", "-s", "-L", "-m", "40", "--proxy", "socks5h://127.0.0.1:1080",
                            "-A", BROWSER_UA, "-o", f.name, "-w", "%{http_code} %{content_type}", url],
                           capture_output=True, text=True, timeout=60)
        code, _, ctype = r.stdout.partition(" ")
        if not code.startswith("2"):
            return False, f"HTTP {code}"
        data = open(f.name, "rb").read()
    if "pdf" in ctype or data[:5] == b"%PDF-":
        return True, _pdf_text(data)[:PAGE_TEXT_CAP]
    return True, html_to_text(data.decode(errors="replace"))[:PAGE_TEXT_CAP]


def citing_passage(response: str, url: str) -> str:
    """Paragraph(s) of the response that mention this URL."""
    paras = re.split(r"\n\s*\n", response)
    hits = [p for p in paras if url in p]
    if not hits:
        i = response.find(url)
        return response[max(0, i - 800): i + 400]
    return "\n\n".join(hits)[:PASSAGE_CAP]


def _norm(t: str) -> str:
    t = (t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
          .replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " "))
    return re.sub(r"\s+", " ", t).lower()


def _alnum_index(text: str):
    """Lower-cased letters+digits only, with a map back to original offsets.
    Calibration (2026-10-06): '@Tutaaa91, who' vs page '@tutaaa91 , who' and
    curly vs spaced straight quotes made verbatim quotes look absent."""
    chars, pos = [], []
    for i, ch in enumerate(text):
        if ch.isalnum():
            chars.append(ch.lower())
            pos.append(i)
    return "".join(chars), pos


def fuzzy_find(page: str, probe: str, _cache={}):
    key = id(page)
    if key not in _cache or _cache[key][0] is not page:
        _cache.clear()
        _cache[key] = (page, _alnum_index(page))
    hay, pos = _cache[key][1]
    needle = _alnum_index(probe)[0]
    if not needle:
        return -1
    if len(needle) < 6:
        # Short tokens ("30", "4,049", "$11.09M", "0.24%"): the alphanumeric-only
        # haystack loses word boundaries ("30" would match inside "2030"), so
        # search the token in its ORIGINAL form (keeping its comma/dot) as a
        # whole token. A first version searched the stripped form ("4049") in
        # the raw page and reported numbers like 4,049 as absent.
        tok = probe.lower().strip().lstrip("$").strip()
        # Units may follow ("$11.09m", "30x", "0.24%"); a continuation of the
        # number may not ("11.095", "4,0490").
        m = re.search(rf"(?<![0-9a-z.,]){re.escape(tok)}(?![0-9]|[.,][0-9])", page.lower())
        return m.start() if m else -1
    i = hay.find(needle)
    return pos[i] if i >= 0 else -1


QUOTE_RE = re.compile(r'["\u201c\u201d\u201e]([^"\u201c\u201d\u201e]{25,400})["\u201c\u201d\u201e]')
NUMBER_RE = re.compile(r"\$?\d[\d,]*\.\d+|\$?\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?\s?%|\$\d+(?:\.\d+)?[kmb]?|\b\d{2,}\b", re.I)


def evidence_check(passage: str, pages: dict) -> str:
    """Programmatic check of every quote and specific number in the passage
    against the FULL text of each cited page (the pre-registered method:
    'substring-match the quoted text', 'check the number appears'). The judge
    gets the result, so a verdict no longer depends on which excerpt windows
    happened to be shown."""
    lines = []
    for q in dict.fromkeys(m.strip() for m in QUOTE_RE.findall(passage)):
        parts = [x for x in re.split(r"\s*(?:\.\.\.|\u2026)\s*", q) if len(_alnum_index(x)[0]) >= 12]
        where = []
        for url, text in pages.items():
            if text and parts and all(fuzzy_find(text, x) >= 0 for x in parts):
                where.append(url)
        lines.append(f'QUOTE "{q[:160]}" -> ' + (f"FOUND verbatim on {', '.join(where)}" if where else "NOT FOUND on any fetched cited page"))
    for n in dict.fromkeys(NUMBER_RE.findall(passage)):
        n = n.strip()
        if len(_alnum_index(n)[0]) < 2:
            continue
        where = [u for u, t in pages.items() if t and fuzzy_find(t, n) >= 0]
        lines.append(f"NUMBER {n} -> " + (f"found on {', '.join(where)}" if where else "not found on any fetched cited page"))
    if not lines:
        return "(no quotes or specific numbers in the passage)"
    if not pages:
        return "(no cited page could be fetched - nothing was checked)\n" + "\n".join(lines)
    return "\n".join(lines)


def _probes(passage: str) -> list:
    """(priority, probe): quotes and numbers first - a fabricated claim hinges on
    those - then distinctive words. Calibration (2026-10-06) showed word windows
    from the top of a long page used up the excerpt budget before the window
    holding the quoted number was added (t0107: two true arXiv quotes judged
    fabricated)."""
    p = _norm(passage)
    out = []
    for q in re.findall(r'"([^"]{12,300})"', p):
        out += [(0, q[:80]), (0, q[-80:])]
    out += [(1, n) for n in re.findall(r"\$?\d[\d,]*\.\d+|\$?\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?%|\$\d+", p)]
    words = sorted(set(re.findall(r"[a-z][a-z\-]{6,}", p)), key=len, reverse=True)[:8]
    out += [(2, w) for w in words]
    return out


def page_excerpts(page: str, passage: str) -> str:
    """Windows of the real page around the passage's quotes/numbers/terms,
    filled in priority order (quotes, numbers, words), shown in page order."""
    low = _norm(page)
    if len(low) <= EXCERPT_BUDGET:
        return low  # short page: show all of it
    chosen, used = [], 0
    for prio, probe in sorted(_probes(passage), key=lambda x: x[0]):
        i = fuzzy_find(low, probe)
        if i < 0:
            continue
        a, b = max(0, i - EXCERPT_RADIUS), i + len(probe) + EXCERPT_RADIUS
        if any(x <= i and i + len(probe) <= y for x, y in chosen):
            continue  # this probe is already visible in a chosen window
        # Overlapping windows are merged, not skipped: calibration showed a
        # number 600 chars past a quote's window was dropped because its own
        # window overlapped the quote's (t0047 $28,990,000, t0056 $62,701.75).
        merged_a, merged_b, rest = a, b, []
        for x, y in chosen:
            if x < merged_b and y > merged_a:
                merged_a, merged_b = min(x, merged_a), max(y, merged_b)
            else:
                rest.append((x, y))
        new_used = sum(y - x for x, y in rest) + (merged_b - merged_a)
        if new_used > EXCERPT_BUDGET:
            if prio == 2:
                continue
            break
        chosen = rest + [(merged_a, merged_b)]
        used = new_used
    if not chosen:
        return low[:1500] + "\n[... no quote/number/term from the passage was found on this page ...]"
    return "\n".join(f"[...] {low[a:b]} [...]" for a, b in sorted(chosen))


# Operational definition (EXPERIMENT_SCORER_V2.md, 2026-10-06), written before
# calibration: an ATTRIBUTED claim is a sentence/bullet that states a specific
# fact, number or quote AND presents it as coming from a cited source (inline
# link on it, "according to X", a "Source:" line covering it, a quote marked as
# the source's words, or a description of what the linked repo/page itself
# contains). The model's own analysis, opinion, hedging or general background
# not presented as coming from the source is NOT an attributed claim, even if
# it sits in the same paragraph as a link. v2's first draft counted those, which
# biased against responses that add honest analysis next to their citations.
JUDGE_PER_PASSAGE = """You are a strict fact-checker. Below is one passage from a research response and, for every URL that passage cites, excerpts of the REAL page at that URL (taken around the quotes, numbers and key terms in the passage), or a note that it was unreachable or not machine-checkable.

STEP 1 - find ATTRIBUTED claims only. An attributed claim states a specific fact, number or quote AND presents it as coming from a cited source: a link placed on that statement, "according to X", a "Source:" line covering it, text marked as the source's own words, or a description of what the linked repo/page itself contains or says. A link covers only the sentence or bullet it is placed on (or the block a "Source:" line explicitly labels); following sentences without their own link are NOT attributed to it. Do NOT count the response's own analysis, opinions, hedges, recommendations or general background that is not presented as coming from the source - even if it is in the same paragraph as a link.

STEP 2 - give each attributed claim one verdict:
- "supported": at least one cited source supports it.
- "fabricated": no cited source supports it (number absent or different, quote not present, page about something else), or it describes a source that is unreachable/nonexistent (an invented repo or URL).
- "undetermined": the excerpts are clearly insufficient to judge either way (thin JavaScript page, search page, excerpt obviously missing the relevant part).

Respond with ONLY valid JSON:
{{"claims": [{{"claim": "<short paraphrase>", "url": "<the cited URL it relies on>", "verdict": "supported|fabricated|undetermined", "why": "<short reason>"}}]}}

--- PASSAGE FROM THE RESPONSE ---
{passage}

--- PROGRAMMATIC CHECK OF QUOTES AND NUMBERS AGAINST THE FULL PAGE TEXT ---
(This check searched each cited page's ENTIRE text, punctuation-insensitive. Trust it over the excerpts: a quote marked NOT FOUND is not on the page; a number marked found is on the page even if no excerpt shows it.)
{evidence}

--- CITED SOURCES ---
{sources}
"""


def _judge(prompt: str, attempts: int = 7) -> dict:
    last = None
    for attempt in range(attempts):
        try:
            out = call_groq_judge(prompt)
            m = re.search(r"\{.*\}", out, re.DOTALL)
            if not m:
                raise ValueError(f"no JSON in judge output: {out[:120]!r}")
            parsed = json.loads(m.group(0))
            claims = parsed.get("claims")
            if not isinstance(claims, list) or any(c.get("verdict") not in ("supported", "fabricated", "undetermined") for c in claims):
                raise ValueError(f"judge JSON not in the expected claims format: {str(parsed)[:200]}")
            return parsed
        except httpx.HTTPStatusError as e:
            last = e
            print(f"  judge HTTP {e.response.status_code}: {e.response.text[:160]}", flush=True)
            wait = 45 * (attempt + 1) if e.response.status_code == 429 else 5 * (attempt + 1)
            time.sleep(wait)
        except Exception as e:
            last = e
            time.sleep(5 * (attempt + 1))
    # v1 silently turned this into 0/0; v2 refuses to score instead.
    raise RuntimeError(f"judge failed after {attempts} attempts: {last}")


FETCH_CACHE = {}


def fetch_cached(url: str) -> tuple:
    if url not in FETCH_CACHE:
        FETCH_CACHE[url] = fetch_full(url)
    return FETCH_CACHE[url]


def source_status(url: str) -> str:
    """'nonexistent' (404/410, repo missing), 'unchecked' (search page, blocked,
    JavaScript-thin) or 'ok'."""
    if UNCHECKABLE_URL_RE.search(url):
        return "unchecked"
    reachable, page = fetch_cached(url)
    if reachable is False:
        return "nonexistent"
    if reachable is None or len(page) < THIN_PAGE_CHARS:
        return "unchecked"
    return "ok"


def apply_rules(claims: list, statuses: dict) -> list:
    """Protocol rules the judge applied inconsistently in calibration
    (t0128 vs t0103): a claim resting only on a nonexistent URL is fabricated
    (pre-registration: the URL must resolve); one resting only on a page we
    could not check is undetermined unless the judge found support."""
    out = []
    for c in claims:
        c = dict(c)
        st = statuses.get(c.get("url"))
        if st == "nonexistent":
            if c["verdict"] != "fabricated":
                c["why"] = f"[rule: cited URL does not exist] {c.get('why', '')}"
            c["verdict"] = "fabricated"
        elif st == "unchecked" and c["verdict"] == "fabricated":
            c["verdict"] = "undetermined"
            c["why"] = f"[rule: source could not be checked] {c.get('why', '')}"
        out.append(c)
    return out


def _source_block(url: str, passage: str, budget: int) -> tuple:
    if UNCHECKABLE_URL_RE.search(url):
        return f"URL: {url}\n(search/login page - content depends on the viewer, not a fixed source)", None
    reachable, page = fetch_cached(url)
    if reachable is None:
        return (f"URL: {url}\nCould not be fetched by the checker ({page}). This does NOT mean the "
                f"source does not exist: count claims relying on it as undetermined."), None
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
        # Every URL that appears inside the passage text is a cited source for
        # it, not only the URLs whose own citing passage is exactly this text
        # (calibration t0080: a passage citing arXiv + substack was judged
        # against arXiv only).
        purls = list(dict.fromkeys(purls + extract_urls(passage)))
        claims = judge_passage(passage, purls)
        time.sleep(pace_seconds)  # Groq free tier: 8000 tokens/minute
        c = len(claims)
        f = sum(x["verdict"] == "fabricated" for x in claims)
        u_ = sum(x["verdict"] == "undetermined" for x in claims)
        totals["checkable"] += c
        totals["fabricated"] += f
        totals["undetermined"] += u_
        details += [f"{x.get('url')}: {x.get('claim')} ({x.get('why')})" for x in claims if x["verdict"] == "fabricated"]
        per_passage.append({"urls": purls, "claims": claims, "passage": passage,
                            "checkable": c, "fabricated": f, "undetermined": u_})
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


def judge_passage(passage: str, urls: list) -> list:
    """One judge call for one citing passage: excerpts + programmatic evidence,
    then protocol rules. Shared by verify_domain_a_v2 and calibration."""
    urls = list(dict.fromkeys(urls))[:MAX_URLS]
    budget = max(1200, EXCERPT_BUDGET // len(urls))
    blocks = [_source_block(u, passage, budget)[0] for u in urls]
    statuses = {u: source_status(u) for u in urls}
    pages = {u: fetch_cached(u)[1] for u in urls if statuses[u] == "ok"}
    evidence = evidence_check(passage, pages)
    verdict = _judge(JUDGE_PER_PASSAGE.format(passage=passage, evidence=evidence, sources="\n\n".join(blocks)))
    return apply_rules(verdict["claims"], statuses)
