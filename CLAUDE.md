# CLAUDE.md — Agent Context

This file gives AI agents (Claude, Codex, etc.) the context needed to work on this project without asking basic questions.

## What This Project Does

Scrapes Google Maps to build a marketing email list of London restaurants and cafes.
**Output**: `MARKETING_LIST.csv` — target 10,000 rows, currently ~7,462.

## Architecture in One Paragraph

`run_overnight.py` is the orchestrator. It loads search queries from `config_batch*.py` files into a shared JSONL queue (`scraper_queue.jsonl`), then spawns N worker processes (`run_to_1000.py`). Each worker atomically pops a query from the queue using `fcntl` file-locks, scrolls Google Maps in a headless Chrome browser (Selenium), extracts business info, visits business websites in parallel (20 threads, `requests`) to find email addresses, and appends results to `MARKETING_LIST.csv` under an exclusive file lock. The orchestrator polls every 30 s, restarts crashed/stale workers, and runs dedup (by email) every 30 min.

## Key Files

```
run_to_1000.py              Worker script. One process per worker.
run_overnight.py            Orchestrator. Start this to run everything.
batches/config_batch55-80.py  Search query batches (active/current).
batches/__init__.py         Makes batches/ a Python package.
scraper_queue.jsonl         Shared work queue. One JSON object per line.
MARKETING_LIST.csv          Output CSV. Deduped by Email column.
requirements.txt            Python deps: selenium, beautifulsoup4, requests, lxml, webdriver-manager
_archive/                   Old files. Do not touch.
```

## Current State

- Records: ~7,462 / 10,000 target
- Queue: ~795 queries remaining in `scraper_queue.jsonl`
- Last run ended: 2026-03-02
- Workers: not running

## How to Resume

```bash
source venv/bin/activate
python run_overnight.py > overnight.log 2>&1 &
```

## How to Check Progress

```bash
wc -l MARKETING_LIST.csv        # record count (subtract 1 for header)
wc -l scraper_queue.jsonl       # queries remaining
tail -f overnight.log           # live log
```

## How to Add More Queries (when queue runs out)

1. Create `batches/config_batchN.py` with:
```python
SEARCH_QUERIES = [
    ("restaurants <area> London", "Restaurant", 60),
    ...
]
```
2. Import it in `run_overnight.py` (`from batches.config_batchN import SEARCH_QUERIES as BN`) and add to `ALL_QUERIES`.

## Constraints

- **London only** — Greater London boroughs only. No Surrey, Kent, Essex, etc.
- Platform: macOS/Linux only (uses `fcntl`, not Windows-compatible)
- Python 3.8+, Google Chrome must be installed

## CSV Schema

`seq, Email, Business_Name, Category, Phone, Address, Website, Rating, Review_Count, Google_Maps_URL`

Dedup key: `Email` (case-insensitive).

## Common Tasks for Agents

- **"Resume the scraper"**: Run `python run_overnight.py` after activating venv
- **"How many records?"**: `wc -l MARKETING_LIST.csv` (subtract 1)
- **"Queue is empty, add more queries"**: Create new `config_batchN.py`, update `run_overnight.py`
- **"Deduplicate the CSV"**: Call `dedup_csv()` from `run_overnight.py` or use pandas `drop_duplicates(subset='Email')`
- **"Workers are crashing"**: Check `worker_0.log`, likely Chrome or chromedriver version issue
- **"Reduce load on Google"**: Lower `N_WORKERS` in `run_overnight.py` (default 8, try 4)
