# Site Intel Lead Enricher

Turn a plain list of business websites into a scored, explainable lead list — with contact details, tech stack, and the specific automation gap each business has.

## Problem
Agencies and freelancers selling automation to roofers, HVAC firms, clinics, salons and realtors waste hours opening websites one by one to find contact info and decide who is worth contacting.

## Solution
Feed in a CSV (`name,website`). The tool fetches each homepage politely (robots.txt respected, retries, timeouts), extracts facts, scores the automation opportunity 0–100 with **human-readable reasons**, and writes a ranked CSV/JSON. An optional LLM step writes a one-sentence personalised opener; without an API key it falls back to a deterministic template.

## Features
- Emails, phones, social links, CMS/tech stack (WordPress, Wix, HubSpot, Calendly, live chat, booking tools…)
- Industry detection (roofing, HVAC, plumbing, clinic, salon, real estate, cleaning, electrical)
- Transparent rule-based scoring with HOT / WARM / COLD tiers — every point has a stated reason
- Concurrent processing, retry/backoff, robots.txt compliance
- Optional OpenAI-compatible LLM summaries that never break the pipeline on failure
- CSV + JSON output, CLI, unit tests (network mocked)

## Architecture
```
leads.csv -> fetch.py (robots, retries) -> extract.py (HTML -> facts)
          -> scoring.py (score + reasons) -> ai.py (optional opener) -> enriched_leads.csv/json
```
`extract.py` and `scoring.py` are pure functions, so they are easy to test and reuse (e.g. inside an n8n Code node or API).

## Tech Stack
Python 3.10+, requests, BeautifulSoup4, pytest.

## How It Works
1. Normalise URL and check `robots.txt`.
2. Download homepage (up to 2 retries).
3. Parse emails/phones/socials/tech/industry/booking/chat/mobile/HTTPS signals.
4. Score: industry match +20, contact info +15, no booking +15, no chat +10, not mobile-optimised +10, and smaller gap rules (see `scoring.py`).
5. Rank and export.

## Installation
```bash
git clone https://github.com/Waqas-Ai-Engineer/site-intel-lead-enricher.git
cd site-intel-lead-enricher
pip install -r requirements.txt
cp .env.example .env   # optional, only for LLM summaries
```

## Configuration
| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Optional. Enables AI summaries (export it in your shell; never commit it) |
| `OPENAI_MODEL` | Default `gpt-4o-mini` |
| `OPENAI_BASE_URL` | Any OpenAI-compatible endpoint |

## Usage
```bash
PYTHONPATH=src python -m site_intel examples/leads.csv -o output --no-llm
PYTHONPATH=src python -m site_intel leads.csv -w 8        # with AI summaries
PYTHONPATH=src pytest -q
```

## Example
Input row `Apex Roofing,apexroof.com` may yield: `score=85, tier=HOT, industries=roofing, emails=info@…, reasons="Target industry match: roofing | No online booking -> appointment-automation opportunity | …"`. (Output depends entirely on the live site; no sample numbers are claimed.)

## Project Structure
```
src/site_intel/  fetch.py extract.py scoring.py ai.py pipeline.py cli.py
tests/           unit + mocked pipeline tests
examples/        sample input CSV
```

## Future Improvements
Crawl /contact and /about pages, Supabase/Postgres sink, n8n webhook wrapper, Google Maps/CRM import, deduplication, per-niche scoring profiles.

## Open-Source Foundation / Attribution
100% original code. No third-party repositories were copied or adapted. Use responsibly: respect robots.txt, site terms, and anti-spam laws (CAN-SPAM, GDPR/PECR, Spam Act) when contacting leads.

## Author
Muhammad Waqas — AI Agents & Business Automation
