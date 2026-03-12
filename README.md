# London Restaurant & Cafe Email Scraper

A parallel Google Maps scraper that collects **business name, email, phone, address, website, rating, and review count** for restaurants and cafes across London. Target: 10,000 unique email records.

## How It Works

```
run_overnight.py
  │  loads config_batch*.py → scraper_queue.jsonl
  │  spawns N worker processes
  │
  ├── run_to_1000.py (worker 0) ─┐
  ├── run_to_1000.py (worker 1)  │  each worker:
  ├── ...                        │  1. pops a query from scraper_queue.jsonl (file-locked)
  └── run_to_1000.py (worker N) ─┘  2. scrolls Google Maps, extracts business info
                                     3. visits business websites in parallel (20 threads)
                                     4. appends to MARKETING_LIST.csv (file-locked)
```

- Workers share one queue (`scraper_queue.jsonl`) and one output CSV (`MARKETING_LIST.csv`) using `fcntl` file-locks — safe for concurrent writes.
- `run_overnight.py` monitors workers every 30 s, auto-restarts crashed/stale workers, and runs dedup every 30 min.
- Dedup key: `Email` field (case-insensitive).

## Current Status

| Item | Value |
|------|-------|
| Records collected | ~7,462 (as of 2026-03-02) |
| Target | 10,000 |
| Queue remaining | ~795 queries (`scraper_queue.jsonl`) |
| Active batch configs | `config_batch55.py` – `config_batch80.py` |

## Prerequisites

- macOS or Linux (uses `fcntl` — not compatible with Windows)
- Python 3.8+
- Google Chrome installed
- `pip install -r requirements.txt`

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

### Start a full overnight run

```bash
python run_overnight.py > overnight.log 2>&1 &
```

This will:
1. Load all queries from `config_batch55` – `config_batch80` into `scraper_queue.jsonl` (skips if queue already has items)
2. Start 8 parallel workers
3. Monitor and auto-restart crashed workers
4. Stop when 10,000 records reached or queue is empty

### Monitor progress

```bash
tail -f overnight.log                      # orchestrator log
tail -f worker_0.log                       # individual worker log
watch -n15 'wc -l MARKETING_LIST.csv'     # record count
wc -l scraper_queue.jsonl                  # queries remaining
```

### Run a single worker manually (for debugging)

```bash
python run_to_1000.py --queue-file scraper_queue.jsonl --worker-id 0
```

## Output Format

`MARKETING_LIST.csv` — one row per business:

| Column | Description |
|--------|-------------|
| `seq` | Auto-incrementing row number |
| `Email` | Business email (dedup key) |
| `Business_Name` | Name on Google Maps |
| `Category` | Restaurant, Cafe, etc. |
| `Phone` | Phone number |
| `Address` | Full address |
| `Website` | Business website URL |
| `Rating` | Google Maps rating (out of 5) |
| `Review_Count` | Number of Google reviews |
| `Google_Maps_URL` | Direct link to the listing |

## Adding More Search Queries

Create a new `config_batchN.py` file in the same format as existing batch files:

```python
# config_batchN.py
SEARCH_QUERIES = [
    ("restaurants Hackney London", "Restaurant", 60),
    ("cafes Peckham London",       "Cafe",       40),
    # (search_query, category_label, max_results)
]
```

Then add it to the `run_overnight.py` import block and `ALL_QUERIES` list.

## Project Structure

```
run_to_1000.py          # Worker script (one process per worker)
run_overnight.py        # Orchestrator: loads queue, spawns workers, monitors
config_batch55-80.py    # Search query lists (one batch = ~100-200 queries)
scraper_queue.jsonl     # Shared work queue (JSONL, one query per line)
MARKETING_LIST.csv      # Output data (deduped by email)
requirements.txt        # Python dependencies
_archive/               # Old/superseded files (kept for reference)
```

## Notes

- **London only**: All queries are scoped to London postcodes and boroughs. Do not add queries for Surrey, Kent, Essex, etc.
- **Rate limiting**: If Google starts showing CAPTCHAs, reduce `N_WORKERS` in `run_overnight.py` or add longer delays in `run_to_1000.py`.
- **Email extraction success rate**: ~25-40% of businesses have a publicly listed email.
- **Resume-safe**: If the run is interrupted, just re-run `python run_overnight.py`. It detects existing queue items and resumes.
