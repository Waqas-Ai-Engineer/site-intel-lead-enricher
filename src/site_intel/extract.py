"""Pure HTML -> structured facts extraction (no network, fully testable)."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)|\d{2,4})[\s.-]?\d{3,4}[\s.-]?\d{3,4}")
JUNK_EMAIL_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")
SOCIAL_HOSTS = {
    "facebook.com": "facebook", "instagram.com": "instagram", "linkedin.com": "linkedin",
    "twitter.com": "twitter", "x.com": "twitter", "youtube.com": "youtube", "tiktok.com": "tiktok",
}
TECH_SIGNATURES = {
    "WordPress": ["wp-content", "wp-includes"],
    "Wix": ["wixstatic.com", "wix.com"],
    "Squarespace": ["squarespace.com", "static1.squarespace"],
    "Shopify": ["cdn.shopify.com"],
    "Webflow": ["webflow.com", "w-nav"],
    "Google Analytics": ["googletagmanager.com", "google-analytics.com", "gtag("],
    "Facebook Pixel": ["fbq(", "connect.facebook.net"],
    "HubSpot": ["hs-scripts.com", "hubspot"],
    "Calendly": ["calendly.com"],
    "Live chat": ["tawk.to", "intercom", "livechatinc", "drift.com", "crisp.chat"],
    "Online booking": ["acuityscheduling", "booksy", "fresha", "setmore", "housecallpro", "servicetitan", "jobber"],
}
SERVICE_KEYWORDS = {
    "roofing": ["roof", "shingle", "gutter"],
    "hvac": ["hvac", "heating", "air conditioning", "furnace", "ac repair"],
    "plumbing": ["plumb", "drain", "water heater"],
    "electrical": ["electrician", "electrical"],
    "clinic": ["clinic", "dental", "dentist", "physio", "chiropract"],
    "salon": ["salon", "barber", "hair", "beauty", "spa"],
    "real_estate": ["real estate", "realtor", "property", "listings"],
    "cleaning": ["cleaning", "maid", "janitorial"],
}


@dataclass
class SiteFacts:
    title: str = ""
    description: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    socials: dict[str, str] = field(default_factory=dict)
    tech: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    has_contact_form: bool = False
    has_booking: bool = False
    has_live_chat: bool = False
    mobile_viewport: bool = False
    https: bool = False
    word_count: int = 0


def _clean_phone(p: str) -> str | None:
    digits = re.sub(r"\D", "", p)
    return p.strip() if 9 <= len(digits) <= 13 else None


def extract_facts(html: str, url: str = "") -> SiteFacts:
    soup = BeautifulSoup(html or "", "html.parser")
    f = SiteFacts(https=url.lower().startswith("https://"))
    f.title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    md = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    f.description = (md.get("content") or "").strip() if md else ""
    f.mobile_viewport = soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)}) is not None

    emails, phones = set(), set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("mailto:"):
            emails.add(href[7:].split("?")[0].lower())
        elif href.lower().startswith("tel:"):
            p = _clean_phone(href[4:])
            if p:
                phones.add(p)
        else:
            for host, name in SOCIAL_HOSTS.items():
                if re.search(rf"(^|//|\.){re.escape(host)}/", href.lower()):
                    f.socials.setdefault(name, href)
    for script in soup(["script", "style", "noscript"]):
        script.extract()
    text = soup.get_text(" ", strip=True)
    f.word_count = len(text.split())
    for m in EMAIL_RE.findall(text):
        emails.add(m.lower())
    for m in PHONE_RE.findall(text):
        p = _clean_phone(m)
        if p:
            phones.add(p)
    f.emails = sorted(e for e in emails if not e.endswith(JUNK_EMAIL_SUFFIX))
    f.phones = sorted(phones)[:5]

    raw = html.lower()
    f.tech = sorted(name for name, sigs in TECH_SIGNATURES.items() if any(s in raw for s in sigs))
    f.has_booking = "Online booking" in f.tech or "Calendly" in f.tech or bool(
        re.search(r"book (an? )?(appointment|online|now|a call)|schedule (an? )?(appointment|service|call)", text, re.I))
    f.has_live_chat = "Live chat" in f.tech
    f.has_contact_form = soup.find("form") is not None
    lowtext = (text + " " + f.title + " " + f.description).lower()
    f.industries = [k for k, kws in SERVICE_KEYWORDS.items() if any(w in lowtext for w in kws)]
    return f
