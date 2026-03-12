#!/usr/bin/env python3
"""
Overnight launcher – London-only run targeting 10,000 records.

Loads batches 19-25 (1,363 queries) into the shared queue,
starts 6 workers, monitors for crashes/staleness, runs periodic
dedup, and exits cleanly when queue exhausted + workers done.
"""

import csv
import fcntl
import json
import os
import subprocess
import sys
import time

# ── Batch imports ──────────────────────────────────────────────────────────────
from config_batch55 import SEARCH_QUERIES as B55
from config_batch56 import SEARCH_QUERIES as B56
from config_batch57 import SEARCH_QUERIES as B57
from config_batch58 import SEARCH_QUERIES as B58
from config_batch59 import SEARCH_QUERIES as B59
from config_batch60 import SEARCH_QUERIES as B60
from config_batch61 import SEARCH_QUERIES as B61
from config_batch62 import SEARCH_QUERIES as B62
from config_batch63 import SEARCH_QUERIES as B63
from config_batch64 import SEARCH_QUERIES as B64
from config_batch65 import SEARCH_QUERIES as B65
from config_batch66 import SEARCH_QUERIES as B66
from config_batch67 import SEARCH_QUERIES as B67
from config_batch68 import SEARCH_QUERIES as B68
from config_batch69 import SEARCH_QUERIES as B69
from config_batch70 import SEARCH_QUERIES as B70
from config_batch71 import SEARCH_QUERIES as B71
from config_batch72 import SEARCH_QUERIES as B72
from config_batch73 import SEARCH_QUERIES as B73
from config_batch74 import SEARCH_QUERIES as B74
from config_batch75 import SEARCH_QUERIES as B75
from config_batch76 import SEARCH_QUERIES as B76
from config_batch77 import SEARCH_QUERIES as B77
from config_batch78 import SEARCH_QUERIES as B78
from config_batch79 import SEARCH_QUERIES as B79
from config_batch80 import SEARCH_QUERIES as B80

ALL_QUERIES = (B55 + B56 + B57 + B58 + B59 + B60 + B61 + B62 + B63 + B64 +
               B65 + B66 + B67 + B68 + B69 + B70 + B71 + B72 + B73 + B74 +
               B75 + B76 + B77 + B78 + B79 + B80)

# ── Settings ───────────────────────────────────────────────────────────────────
N_WORKERS      = 8
TARGET_COUNT   = 10000
POLL_INTERVAL  = 30        # seconds between progress checks
STALE_SEC      = 360       # restart worker if log unchanged for 6 min
STARTUP_GAP    = 3.0       # seconds between worker launches
DEDUP_EVERY_N  = 60        # dedup every 60 poll cycles (~30 min)

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CSV_FILE   = os.path.join(BASE_DIR, 'MARKETING_LIST.csv')
CSV_LOCK   = CSV_FILE + '.lock'
QUEUE_FILE = os.path.join(BASE_DIR, 'scraper_queue.jsonl')
QUEUE_LOCK = QUEUE_FILE + '.lock'


# ── Helpers ───────────────────────────────────────────────────────────────────

def count_records() -> int:
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f) - 1
    except FileNotFoundError:
        return 0


def queue_size() -> int:
    try:
        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())
    except FileNotFoundError:
        return 0


def write_queue(queries):
    """Write all queries to the queue file (overwrites)."""
    lfd = open(QUEUE_LOCK, 'w')
    fcntl.flock(lfd, fcntl.LOCK_EX)
    try:
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            for q, cat, mx in queries:
                f.write(json.dumps({'q': q, 'cat': cat, 'max': mx}) + '\n')
    finally:
        fcntl.flock(lfd, fcntl.LOCK_UN)
        lfd.close()


def dedup_csv():
    """Deduplicate MARKETING_LIST.csv in place by email. Returns (before, after)."""
    lfd = open(CSV_LOCK, 'w')
    fcntl.flock(lfd, fcntl.LOCK_EX)
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
        before = len(rows)
        seen, deduped = set(), []
        for row in rows:
            key = row['Email'].strip().lower()
            if key not in seen:
                seen.add(key)
                deduped.append(row)
        after = len(deduped)
        if before == after:
            return before, after
        for i, row in enumerate(deduped, 1):
            row['seq'] = i
        tmp = CSV_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(deduped)
        os.replace(tmp, CSV_FILE)
        return before, after
    finally:
        fcntl.flock(lfd, fcntl.LOCK_UN)
        lfd.close()


def restart_worker(wid: int) -> subprocess.Popen:
    cmd = [sys.executable, 'run_to_1000.py',
           '--queue-file', QUEUE_FILE,
           '--worker-id',  str(wid)]
    log_path = os.path.join(BASE_DIR, f'worker_{wid}.log')
    lf = open(log_path, 'a')
    p = subprocess.Popen(cmd, cwd=BASE_DIR, stdout=lf, stderr=lf)
    print(f"  ↺ W{wid} started/restarted (PID {p.pid})", flush=True)
    return p


# ── Initialise queue ──────────────────────────────────────────────────────────
current  = count_records()
existing = queue_size()

print(f"\n{'='*64}")
print(f"  Overnight Scraper  –  TARGET {TARGET_COUNT}")
print(f"  Current records   : {current}")
print(f"  Need              : {TARGET_COUNT - current} more")
print(f"  Batches           : 19-25  ({len(ALL_QUERIES)} total queries)")
print(f"{'='*64}")

if existing > 0:
    print(f"\nFound {existing} queries already in queue – resuming.")
else:
    print(f"\nWriting {len(ALL_QUERIES)} queries to queue…", flush=True)
    write_queue(ALL_QUERIES)
    print(f"Queue ready: {queue_size()} queries")

# ── Launch workers ─────────────────────────────────────────────────────────────
procs = {}
for wid in range(N_WORKERS):
    procs[wid] = restart_worker(wid)
    if wid < N_WORKERS - 1:
        time.sleep(STARTUP_GAP)

print(f"\nAll {N_WORKERS} workers started.")
print("Monitor logs:  tail -f worker_0.log worker_1.log")
print("Watch count:   watch -n15 'wc -l MARKETING_LIST.csv'\n", flush=True)

# ── Monitor loop ───────────────────────────────────────────────────────────────
last_restart = {}
poll_count   = 0

try:
    while True:
        time.sleep(POLL_INTERVAL)
        poll_count += 1
        current = count_records()
        q_left  = queue_size()
        ts      = time.strftime('%H:%M:%S')

        # ── Progress log ──────────────────────────────────────────────────────
        alive = [wid for wid, p in procs.items() if p.poll() is None]
        print(f"[{ts}]  {current}/{TARGET_COUNT} records  |  "
              f"queue: {q_left:4d}  |  workers alive: {alive}", flush=True)

        # ── Periodic dedup ────────────────────────────────────────────────────
        if poll_count % DEDUP_EVERY_N == 0:
            print(f"  → Running dedup…", flush=True)
            before, after = dedup_csv()
            removed = before - after
            print(f"  → Dedup: {before} → {after} rows (removed {removed})",
                  flush=True)

        # ── Target reached ────────────────────────────────────────────────────
        if current >= TARGET_COUNT:
            print(f"\n🎉  Target {TARGET_COUNT} reached! Terminating workers…",
                  flush=True)
            for p in procs.values():
                try:
                    if p.poll() is None:
                        p.terminate()
                except Exception:
                    pass
            time.sleep(10)
            break

        # ── Restart crashed workers (only if queue still has work) ────────────
        if q_left > 0:
            for wid in range(N_WORKERS):
                p = procs[wid]
                if p.poll() is not None:
                    last = last_restart.get(wid, 0)
                    if time.time() - last > 10:
                        print(f"  ↻ W{wid} exited (rc={p.returncode}), restarting…",
                              flush=True)
                        procs[wid] = restart_worker(wid)
                        last_restart[wid] = time.time()
                    continue
                # Check staleness via log file mtime
                log_path = os.path.join(BASE_DIR, f'worker_{wid}.log')
                try:
                    age = time.time() - os.path.getmtime(log_path)
                    if age > STALE_SEC:
                        last = last_restart.get(wid, 0)
                        if time.time() - last > 60:
                            print(f"  ↻ W{wid} stale ({int(age)}s), killing+restarting…",
                                  flush=True)
                            p.kill()
                            procs[wid] = restart_worker(wid)
                            last_restart[wid] = time.time()
                except FileNotFoundError:
                    pass

        # ── Exit when queue empty and all workers done ────────────────────────
        if q_left == 0 and all(p.poll() is not None for p in procs.values()):
            print(f"\nQueue exhausted and all workers done.", flush=True)
            break

except KeyboardInterrupt:
    print("\nInterrupted – stopping workers…", flush=True)
    for p in procs.values():
        try:
            p.terminate()
        except Exception:
            pass

# ── Final dedup ────────────────────────────────────────────────────────────────
print("\nRunning final dedup…", flush=True)
# Wait briefly for any in-flight workers to finish
for p in procs.values():
    try:
        p.wait(timeout=30)
    except Exception:
        pass

before, after = dedup_csv()
final = count_records()

print(f"\n{'='*64}")
print(f"  DONE")
print(f"  Final rows (unique): {final}")
print(f"  Dedup removed      : {before - after}")
print(f"  Target             : {TARGET_COUNT}")
print(f"{'='*64}\n", flush=True)
