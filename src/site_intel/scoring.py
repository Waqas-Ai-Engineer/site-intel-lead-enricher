"""Transparent, rule-based automation-opportunity scoring (0-100)."""
from __future__ import annotations
from .extract import SiteFacts

# (points, label) — each rule is a visible sales angle, so the score is explainable.
def score(f: SiteFacts, reachable: bool = True) -> tuple[int, list[str]]:
    if not reachable:
        return 0, ["Website unreachable"]
    pts, why = 0, []
    if f.industries:
        pts += 20; why.append(f"Target industry match: {', '.join(f.industries)}")
    if f.emails or f.phones:
        pts += 15; why.append("Public contact details found")
    if not f.has_booking:
        pts += 15; why.append("No online booking -> appointment-automation opportunity")
    if not f.has_live_chat:
        pts += 10; why.append("No live chat -> AI chat/lead-capture opportunity")
    if f.has_contact_form:
        pts += 5; why.append("Has contact form (can wire to CRM/auto-reply)")
    if "Google Analytics" not in f.tech and "Facebook Pixel" not in f.tech:
        pts += 5; why.append("No analytics/pixel detected -> tracking gap")
    if not f.mobile_viewport:
        pts += 10; why.append("Not mobile-optimised")
    if not f.https:
        pts += 5; why.append("No HTTPS")
    if "HubSpot" not in f.tech:
        pts += 5; why.append("No CRM script detected")
    if len(f.socials) >= 2:
        pts += 5; why.append("Active on social channels")
    if f.word_count < 150:
        pts += 5; why.append("Thin website content")
    return min(pts, 100), why


def tier(s: int) -> str:
    return "HOT" if s >= 65 else "WARM" if s >= 40 else "COLD"
