"""Polite HTTP fetching with retries, timeouts and robots.txt respect."""
from __future__ import annotations
import logging
import time
import urllib.robotparser
from urllib.parse import urlparse
import requests

log = logging.getLogger("site_intel.fetch")
UA = "SiteIntelBot/0.1 (+portfolio project; respects robots.txt)"


def normalize_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def allowed_by_robots(url: str, session: requests.Session, timeout: float = 5) -> bool:
    p = urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    try:
        r = session.get(f"{p.scheme}://{p.netloc}/robots.txt", timeout=timeout, headers={"User-Agent": UA})
        if r.status_code >= 400:
            return True
        rp.parse(r.text.splitlines())
        return rp.can_fetch(UA, url)
    except requests.RequestException:
        return True


def fetch_html(url: str, session: requests.Session | None = None, retries: int = 2,
               timeout: float = 10, respect_robots: bool = True) -> tuple[str | None, str]:
    """Return (html or None, status message)."""
    s = session or requests.Session()
    url = normalize_url(url)
    if not url:
        return None, "empty url"
    if respect_robots and not allowed_by_robots(url, s):
        return None, "blocked by robots.txt"
    last = "unknown error"
    for attempt in range(retries + 1):
        try:
            r = s.get(url, timeout=timeout, headers={"User-Agent": UA}, allow_redirects=True)
            if r.status_code == 200 and "html" in r.headers.get("Content-Type", "html"):
                return r.text, "ok"
            last = f"HTTP {r.status_code}"
            if r.status_code < 500:
                break
        except requests.RequestException as e:
            last = type(e).__name__
        time.sleep(0.5 * (attempt + 1))
    log.warning("fetch failed for %s: %s", url, last)
    return None, last
