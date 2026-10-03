"""Optional LLM summary; falls back to a deterministic template when no key is set."""
from __future__ import annotations
import logging
import os
import requests
from .extract import SiteFacts

log = logging.getLogger("site_intel.ai")


def template_summary(name: str, f: SiteFacts, reasons: list[str]) -> str:
    ind = ", ".join(f.industries) or "general business"
    top = "; ".join(reasons[:2]) or "no clear gaps"
    return f"{name} ({ind}). Top angles: {top}."


def llm_summary(name: str, f: SiteFacts, reasons: list[str]) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return template_summary(name, f, reasons)
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    prompt = (f"Business: {name}\nTitle: {f.title}\nDescription: {f.description}\n"
              f"Industries: {f.industries}\nGaps: {reasons}\n"
              "Write ONE sentence (max 30 words) a salesperson could use as a personalised cold-email opener "
              "about an automation opportunity. Do not invent facts.")
    try:
        r = requests.post(f"{base}/chat/completions", timeout=30,
                          headers={"Authorization": f"Bearer {key}"},
                          json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                                "messages": [{"role": "user", "content": prompt}], "max_tokens": 80})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:  # noqa: BLE001 - never let the LLM break the pipeline
        log.warning("LLM summary failed (%s); using template", type(e).__name__)
        return template_summary(name, f, reasons)
