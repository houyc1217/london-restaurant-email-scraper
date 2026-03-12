# Handoff Document

## Goal

Collect 10,000 unique email records for London restaurants and cafes from Google Maps.
Output file: `MARKETING_LIST.csv`

## Current State (2026-03-02)

- **Records collected**: ~7,462
- **Still needed**: ~2,538
- **Queue remaining**: ~795 queries in `scraper_queue.jsonl`
- **Workers**: last run used 8 parallel workers via `run_overnight.py`

The last overnight run completed on 2026-03-02. Workers are no longer running.

---

## How to Resume (Most Common Task)

```bash
cd /path/to/this/repo
source venv/bin/activate

# Check current count first
wc -l MARKETING_LIST.csv          # subtract 1 for header
wc -l scraper_queue.jsonl         # queries left in queue

# Resume — this will reuse whatever is left in the queue
python run_overnight.py > overnight.log 2>&1 &
tail -f overnight.log             # monitor
```

If the queue is empty but you still need more records, see "Adding More Queries" below.

---

## If the Queue Is Empty

Check with:
```bash
wc -l scraper_queue.jsonl    # 0 = empty
```

You need to either:
1. **Add more batch configs** (see below), or
2. **Edit `run_overnight.py`** to import the new batches

### Adding More Queries

1. Create `batches/config_batch81.py` (or next available number):

```python
# config_batch81.py
SEARCH_QUERIES = [
    ("restaurants Woolwich London",   "Restaurant", 60),
    ("cafes Thamesmead London",       "Cafe",       40),
    ("takeaway Plumstead London",     "Restaurant", 50),
    # format: (search_string, category_label, max_results_per_search)
]
```

2. Add to `run_overnight.py` at the top import block:
```python
from batches.config_batch81 import SEARCH_QUERIES as B81
```

3. Add to the `ALL_QUERIES` line:
```python
ALL_QUERIES = (B55 + ... + B80 + B81)
```

4. Run again:
```bash
python run_overnight.py > overnight.log 2>&1 &
```

---

## Monitoring Commands

```bash
# How many records so far
wc -l MARKETING_LIST.csv

# How many queries left
wc -l scraper_queue.jsonl

# Live orchestrator log
tail -f overnight.log

# Individual worker logs
tail -f worker_0.log worker_1.log

# Check if any processes are running
ps aux | grep run_to_1000
ps aux | grep run_overnight
```

---

## Stopping Gracefully

```bash
# Find the overnight process
ps aux | grep run_overnight

# Kill it (workers will stop on their own when queue is empty)
kill <PID>
```

Or just close the terminal — workers are child processes and will exit.
The CSV is safe: every write uses a file lock (`MARKETING_LIST.csv.lock`).

---

## Deduplication

Dedup runs automatically every ~30 min during a run.
To run it manually at any time:

```python
from run_overnight import dedup_csv
before, after = dedup_csv()
print(f"Removed {before - after} duplicates")
```

Or use pandas:
```python
import pandas as pd
df = pd.read_csv('MARKETING_LIST.csv')
df_deduped = df.drop_duplicates(subset='Email', keep='first')
df_deduped.to_csv('MARKETING_LIST.csv', index=False)
print(len(df_deduped), "records after dedup")
```

---

## Troubleshooting

### "No module named selenium" / "No module named webdriver_manager"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Workers crash immediately / Chrome fails to start
- Ensure Google Chrome is installed and up to date
- Try: `python worker.py --queue-file scraper_queue.jsonl --worker-id 0` directly to see the error
- Common cause: Chrome version mismatch. `webdriver-manager` auto-downloads the right chromedriver — just make sure you have internet access

### Google CAPTCHA / rate limiting
- Reduce `N_WORKERS` in `run_overnight.py` from 8 to 4
- Increase `SCROLL_DELAY` and `CLICK_DELAY` in `worker.py`
- Run during off-peak hours (night)

### Queue file is corrupt
```bash
python -c "
import json
good = []
with open('scraper_queue.jsonl') as f:
    for line in f:
        try:
            good.append(json.loads(line))
        except:
            pass
print(len(good), 'valid entries')
with open('scraper_queue.jsonl', 'w') as f:
    for q in good:
        f.write(json.dumps(q) + '\n')
"
```

### Workers finish but count is below target
- Queue exhausted before target reached
- Solution: add more batch configs (see "Adding More Queries" above)
- Suggested new areas: Woolwich, Thamesmead, Plumstead, Abbey Wood, parts of Bexley, Erith, Crayford

---

## Important Constraints

- **London only** — all search queries must be within Greater London (32 boroughs + City of London)
- Do NOT scrape Surrey, Kent, Essex, Hertfordshire, Berkshire
- Only use this data for legitimate opt-in marketing purposes
- Comply with GDPR when emailing UK businesses

---

## File Reference

| File | Purpose |
|------|---------|
| `worker.py` | Worker: pops queries from queue, scrapes Google Maps, extracts emails, writes to CSV |
| `run_overnight.py` | Orchestrator: loads queue, spawns workers, monitors, deduplicates |
| `batches/config_batch55.py` – `config_batch80.py` | Search query lists for the current run |
| `scraper_queue.jsonl` | Shared work queue (JSONL format) |
| `MARKETING_LIST.csv` | Output: all collected records (deduped by email) |
| `requirements.txt` | Python dependencies |
| `_archive/` | Old scrapers, old configs, old CSVs — kept for reference |
