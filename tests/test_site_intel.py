import csv
from unittest.mock import patch
from site_intel.extract import extract_facts
from site_intel.scoring import score, tier
from site_intel.pipeline import run
from site_intel.fetch import normalize_url

HTML = """<html><head><title>Apex Roofing & Gutters</title>
<meta name="description" content="Residential roof repair"></head><body>
<a href="mailto:info@apexroof.com">Email</a><a href="tel:+1 555 123 4567">Call</a>
<a href="https://facebook.com/apexroof">fb</a><a href="https://instagram.com/apexroof">ig</a>
<img src="logo@2x.png"><form></form><p>Call 555-987-6543 today</p></body></html>"""


def test_extract_basic():
    f = extract_facts(HTML, "http://apexroof.com")
    assert f.emails == ["info@apexroof.com"]
    assert "roofing" in f.industries
    assert set(f.socials) == {"facebook", "instagram"}
    assert f.has_contact_form and not f.mobile_viewport and not f.https
    assert len(f.phones) >= 2


def test_score_and_tier():
    s, why = score(extract_facts(HTML, "http://apexroof.com"))
    assert s >= 65 and tier(s) == "HOT" and any("booking" in w for w in why)
    assert score(extract_facts(HTML), reachable=False)[0] == 0


def test_booking_detected():
    f = extract_facts("<html><body>Book an appointment online <script src='calendly.com/x'></script></body></html>")
    assert f.has_booking


def test_normalize():
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("") == ""


def test_pipeline(tmp_path):
    inp = tmp_path / "in.csv"
    inp.write_text("name,website\nApex,apexroof.com\nDead,dead.invalid\n")

    def fake(url, session=None, respect_robots=True, **kw):
        return (HTML, "ok") if "apex" in url else (None, "ConnectionError")

    with patch("site_intel.pipeline.fetch_html", side_effect=fake):
        res = run(inp, tmp_path / "out", workers=2, use_llm=False)
    assert res[0]["name"] == "Apex" and res[1]["score"] == 0
    rows = list(csv.DictReader(open(tmp_path / "out" / "enriched_leads.csv")))
    assert len(rows) == 2 and (tmp_path / "out" / "enriched_leads.json").exists()
