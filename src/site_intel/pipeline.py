from __future__ import annotations
import csv
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
from .ai import llm_summary
from .extract import extract_facts
from .fetch import fetch_html, normalize_url
from .scoring import score, tier

log = logging.getLogger("site_intel.pipeline")
FIELDS = ["name", "website", "status", "score", "tier", "industries", "emails", "phones",
          "socials", "tech", "has_booking", "has_live_chat", "reasons", "summary"]


def enrich_one(row: dict, session: requests.Session | None = None, use_llm: bool = True,
               respect_robots: bool = True) -> dict:
    name = (row.get("name") or row.get("company") or "").strip()
    url = normalize_url(row.get("website") or row.get("url") or "")
    html, status = fetch_html(url, session, respect_robots=respect_robots)
    out = {"name": name, "website": url, "status": status}
    if html is None:
        out.update(score=0, tier="COLD", reasons="Website unreachable", summary="", industries="",
                   emails="", phones="", socials="", tech="", has_booking=False, has_live_chat=False)
        return out
    f = extract_facts(html, url)
    s, why = score(f)
    out.update(score=s, tier=tier(s), industries=", ".join(f.industries), emails=", ".join(f.emails),
               phones=", ".join(f.phones), socials=", ".join(f"{k}:{v}" for k, v in f.socials.items()),
               tech=", ".join(f.tech), has_booking=f.has_booking, has_live_chat=f.has_live_chat,
               reasons=" | ".join(why),
               summary=llm_summary(name, f, why) if use_llm else "")
    return out


def run(input_csv: Path, output_dir: Path, workers: int = 4, use_llm: bool = True,
        respect_robots: bool = True) -> list[dict]:
    with open(input_csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    log.info("Enriching %d businesses with %d workers", len(rows), workers)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(lambda r: enrich_one(r, None, use_llm, respect_robots), rows))
    results.sort(key=lambda r: r["score"], reverse=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "enriched_leads.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(results)
    (output_dir / "enriched_leads.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
