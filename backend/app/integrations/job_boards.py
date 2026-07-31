"""
Job board search and legitimacy verification.
Uses DuckDuckGo to find listings across Indeed, LinkedIn, ZipRecruiter, Glassdoor.
Verifies each listing is real before surfacing it to the apply engine.
"""
import hashlib
import re

import httpx
from ddgs import DDGS

from app.integrations.web_search import _sanitize

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

_SOURCES = [
    ("indeed",       'site:indeed.com "{title}" {location} job'),
    ("linkedin",     'site:linkedin.com/jobs "{title}" {location}'),
    ("ziprecruiter", 'site:ziprecruiter.com "{title}" {location}'),
    ("glassdoor",    'site:glassdoor.com/job-listing "{title}" {location}'),
]

# Red flags that suggest a fake or scam job posting
_SCAM_PATTERNS = re.compile(
    r"no experience (needed|required)|make \$[\d,]+/?(day|week|hour) from home"
    r"|work from home.*\$[\d,]+(k|,000)/?(week|day)"
    r"|guaranteed (income|salary|pay)"
    r"|send (your )?social security|direct deposit info required"
    r"|wire transfer|advance fee|gift card"
    r"|urgently (hiring|needed).*no (resume|experience|interview)"
    r"|be your own boss.*unlimited income"
    r"|mystery shopper|secret shopper.*payment",
    re.IGNORECASE,
)

# Domains that are known real job boards / company career pages
_TRUSTED_DOMAINS = frozenset({
    "indeed.com", "linkedin.com", "ziprecruiter.com", "glassdoor.com",
    "monster.com", "dice.com", "lever.co", "greenhouse.io", "workday.com",
    "smartrecruiters.com", "icims.com", "taleo.net", "jobvite.com",
    "careers.google.com", "careers.microsoft.com", "amazon.jobs",
    "careers.apple.com", "meta.com", "stripe.com",
})


def _job_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def search_jobs(title: str, location: str = "remote", max_per_source: int = 5) -> list[dict]:
    """Search multiple job boards and return raw listings."""
    jobs: list[dict] = []
    seen_ids: set[str] = set()

    with DDGS() as ddgs:
        for source, template in _SOURCES:
            query = template.format(title=title, location=location)
            try:
                results = list(ddgs.text(query, max_results=max_per_source))
            except Exception:
                continue

            for r in results:
                url = r.get("href", "").strip()
                if not url or not url.startswith("http"):
                    continue
                jid = _job_id(url)
                if jid in seen_ids:
                    continue
                seen_ids.add(jid)
                jobs.append({
                    "job_id": jid,
                    "source": source,
                    "title": _sanitize(r.get("title", "")),
                    "url": url,
                    "snippet": _sanitize(r.get("body", "")[:400]),
                    "domain": _extract_domain(url),
                    "description": "",
                    "company": "",
                    "legitimacy": "unverified",
                    "legitimacy_flags": [],
                })

    return jobs


def fetch_job_description(url: str, timeout: int = 10) -> str:
    """Fetch and extract text content from a job posting URL."""
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True, headers=_HEADERS)
        if resp.status_code != 200:
            return ""
        text = resp.text
        # Strip HTML tags
        text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:4000]
    except Exception:
        return ""


def verify_job(job: dict) -> dict:
    """
    Run legitimacy checks on a job listing.
    Returns the job dict with legitimacy and flags populated.
    """
    flags: list[str] = []
    text = (job.get("snippet", "") + " " + job.get("description", "")).lower()

    # Scam pattern check
    if _SCAM_PATTERNS.search(text):
        flags.append("SCAM_PATTERN: suspicious language detected")

    # Check domain trust
    domain = job.get("domain", "")
    if domain:
        trusted = any(t in domain for t in _TRUSTED_DOMAINS)
        if not trusted:
            flags.append(f"UNKNOWN_DOMAIN: {domain} is not a recognized job board")

    # Check if URL is still active
    url = job.get("url", "")
    if url:
        try:
            resp = httpx.head(url, timeout=6, follow_redirects=True, headers=_HEADERS)
            if resp.status_code == 404:
                flags.append("EXPIRED: job posting returns 404 — likely filled or removed")
            elif resp.status_code >= 400:
                flags.append(f"HTTP_ERROR: posting returned {resp.status_code}")
        except Exception:
            flags.append("UNREACHABLE: could not verify posting URL")

    # Missing company name is a weak signal
    if not job.get("company"):
        flags.append("NO_COMPANY: company name not detected in listing")

    # Salary too good to be true (in snippet)
    salary_match = re.search(r"\$(\d[\d,]+)\s*(per|/)\s*(day|week|hour)", text)
    if salary_match:
        val = int(salary_match.group(1).replace(",", ""))
        if val > 1000:  # >$1000/day = suspicious
            flags.append(f"SALARY_SUSPICIOUS: ${val}/day is unusually high — verify")

    # Determine overall verdict
    critical = [f for f in flags if f.startswith("SCAM") or f.startswith("EXPIRED")]
    if critical:
        legitimacy = "suspicious"
    elif len(flags) >= 2:
        legitimacy = "needs_review"
    elif flags:
        legitimacy = "likely_real"
    else:
        legitimacy = "verified"

    return {**job, "legitimacy": legitimacy, "legitimacy_flags": flags}


def enrich_and_verify(jobs: list[dict]) -> list[dict]:
    """Fetch full descriptions and verify legitimacy for a list of jobs."""
    enriched = []
    for job in jobs:
        desc = fetch_job_description(job["url"])
        job["description"] = desc

        # Try to extract company name from description
        company_match = re.search(
            r"(?:company|employer|about us|who we are)[:\s]+([A-Z][A-Za-z0-9 &,.-]{2,50})",
            desc[:800],
        )
        if company_match:
            job["company"] = company_match.group(1).strip()

        job = verify_job(job)
        enriched.append(job)

    return enriched
