#!/usr/bin/env python3
"""
London SME scraper worker – supports parallel execution.

Key optimizations vs v1:
  1. Accepts --start/--end/--worker-id for query slicing (multi-worker)
  2. Batch email fetching: collects N business URLs, fetches emails
     in parallel with ThreadPoolExecutor (6x faster than sequential)
  3. fcntl file-lock on MARKETING_LIST.csv for safe concurrent writes
  4. Reduced click/back delays

Usage (single):
    python run_to_1000.py

Usage (via run_parallel.py – 3 workers):
    python run_parallel.py
"""

import argparse
import csv
import fcntl
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ── CLI args ──────────────────────────────────────────────────────────────────
_p = argparse.ArgumentParser()
_p.add_argument('--start',      type=int,  default=0)
_p.add_argument('--end',        type=int,  default=None)
_p.add_argument('--worker-id',  type=int,  default=0)
_p.add_argument('--queue-file', type=str,  default=None)
args = _p.parse_args()
WORKER_ID  = args.worker_id
QUEUE_FILE = args.queue_file
QUEUE_LOCK = (QUEUE_FILE + '.lock') if QUEUE_FILE else None

# ── Config ────────────────────────────────────────────────────────────────────
TARGET_COUNT       = 10000
BASE_DIR           = os.path.dirname(os.path.abspath(__file__))
MARKETING_LIST     = os.path.join(BASE_DIR, 'MARKETING_LIST.csv')
LOCK_FILE          = MARKETING_LIST + '.lock'
LOCATION           = 'London'
HEADLESS_MODE      = True
WINDOW_SIZE        = "1920,1080"
SCROLL_DELAY       = 1.5
CLICK_DELAY        = 1      # seconds to wait after clicking a listing
BACK_DELAY         = 0.8    # seconds to wait after going back
CATEGORY_DELAY     = 2
EMAIL_TIMEOUT      = 5
EMAIL_BATCH_SIZE   = 20     # collect this many businesses, then fetch emails in parallel
EMAIL_THREADS      = 20     # parallel threads for email fetching
FIELDNAMES = ['seq', 'Email', 'Business_Name', 'Category', 'Phone', 'Address',
              'Website', 'Rating', 'Review_Count', 'Google_Maps_URL']

# ── Logging ───────────────────────────────────────────────────────────────────
_log_file = os.path.join(BASE_DIR, f'worker_{WORKER_ID}.log')
logging.basicConfig(
    level=logging.INFO,
    format=f'%(asctime)s [W{WORKER_ID}] %(message)s',
    handlers=[
        logging.FileHandler(_log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Load query slice ──────────────────────────────────────────────────────────
from config_batch10 import SEARCH_QUERIES as _ALL
_end = args.end if args.end is not None else len(_ALL)
SEARCH_QUERIES = _ALL[args.start:_end]

# ── Email helpers ─────────────────────────────────────────────────────────────
_BAD_PATTERNS = [
    '.jpg', '.png', '.gif', '.svg', '@2x', '@3x',
    'sentry.io', 'wixpress.com', 'example.com', 'test.com',
    'wordpress.com', 'squarespace.com', 'cloudflare.com',
    'amazonaws.com', 'mailchimp.com', 'sendgrid.net',
    'noreply@', 'no-reply@', 'donotreply@', 'webmaster@',
]
_EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')
_SKIP_DOMAINS = ('google.com', 'facebook.com', 'instagram.com',
                 'twitter.com', 'yelp.com', 'tripadvisor.com')
_EXCLUDE_EMAIL_DOMS = [
    'example.com', 'domain.com', 'sentry.io', 'googleapis.com',
    'wixpress.com', 'squarespace.com', 'cloudflare.com', 'amazonaws.com',
]
_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/120.0.0.0 Safari/537.36')
}


def is_valid_email(email: str) -> bool:
    if not email or '@' not in email:
        return False
    e = email.strip().lower()
    if any(p in e for p in _BAD_PATTERNS):
        return False
    return bool(_EMAIL_RE.fullmatch(e))


def fetch_email_for(url: str):
    """Fetch one email from a business website (runs in thread pool)."""
    if not url or any(s in url for s in _SKIP_DOMAINS):
        return None
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        base = url.rstrip('/')
    for check in [base + '/contact', base + '/contact-us', url]:
        try:
            r = requests.get(check, headers=_HEADERS,
                             timeout=EMAIL_TIMEOUT, allow_redirects=True)
            if r.status_code != 200:
                continue
            found = _EMAIL_RE.findall(r.text)
            good = [e for e in found
                    if is_valid_email(e)
                    and not any(d in e.lower() for d in _EXCLUDE_EMAIL_DOMS)]
            if good:
                return good[0]
        except Exception:
            continue
    return None


def fetch_emails_batch(businesses: list) -> list:
    """Fill in 'Email' field for each business dict using parallel HTTP."""
    with ThreadPoolExecutor(max_workers=EMAIL_THREADS) as pool:
        future_to_idx = {
            pool.submit(fetch_email_for, biz.get('Website', '')): i
            for i, biz in enumerate(businesses)
        }
        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            try:
                email = fut.result()
                if email:
                    businesses[idx]['Email'] = email
            except Exception:
                pass
    return businesses


# ── CSV / file-lock helpers ───────────────────────────────────────────────────

def count_csv_rows() -> int:
    try:
        with open(MARKETING_LIST, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f) - 1
    except FileNotFoundError:
        return 0


def append_record_safe(biz: dict) -> bool:
    """Append under exclusive file lock. Auto-assigns seq. Returns True if saved."""
    lfd = open(LOCK_FILE, 'w')
    fcntl.flock(lfd, fcntl.LOCK_EX)
    try:
        current_rows = count_csv_rows()
        if current_rows >= TARGET_COUNT:
            return False
        biz['seq'] = current_rows + 1          # next seq number
        exists = os.path.isfile(MARKETING_LIST)
        with open(MARKETING_LIST, 'a', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore')
            if not exists:
                w.writeheader()
            w.writerow({k: biz.get(k, '') for k in FIELDNAMES})
        return True
    finally:
        fcntl.flock(lfd, fcntl.LOCK_UN)
        lfd.close()


def load_existing():
    """Return (count, emails_set, names_set)."""
    emails, names, count = set(), set(), 0
    try:
        with open(MARKETING_LIST, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                e = row.get('Email', '').strip().lower()
                n = row.get('Business_Name', '').strip().lower()
                if e: emails.add(e)
                if n: names.add(n)
                count += 1
    except FileNotFoundError:
        pass
    return count, emails, names


# ── Shared queue (queue-mode) ─────────────────────────────────────────────

def pop_query():
    """Atomically pop the next query from the shared queue file. Returns None if empty."""
    if not QUEUE_FILE:
        return None
    lfd = open(QUEUE_LOCK, 'w')
    fcntl.flock(lfd, fcntl.LOCK_EX)
    try:
        if not os.path.exists(QUEUE_FILE):
            return None
        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            lines = [l for l in f.readlines() if l.strip()]
        if not lines:
            return None
        item = json.loads(lines[0])
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines[1:])
        return item           # {'q': str, 'cat': str, 'max': int}
    finally:
        fcntl.flock(lfd, fcntl.LOCK_UN)
        lfd.close()


# ── Scraper ───────────────────────────────────────────────────────────────────

class Worker:
    def __init__(self):
        self.driver = None
        self.existing_emails: set = set()
        self.existing_names:  set = set()
        self.new_count = 0

    # ── Browser setup ─────────────────────────────────────────────────────────

    def setup_driver(self):
        log.info("Starting Chrome (headless=%s)…", HEADLESS_MODE)
        opts = webdriver.ChromeOptions()
        if HEADLESS_MODE:
            opts.add_argument('--headless')
            opts.add_argument(f'--window-size={WINDOW_SIZE}')
        else:
            opts.add_argument('--start-maximized')
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-gpu')
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        try:
            dp = ChromeDriverManager().install()
            if os.path.basename(dp) != 'chromedriver':
                for f in os.listdir(os.path.dirname(dp)):
                    if f == 'chromedriver':
                        dp = os.path.join(os.path.dirname(dp), f)
                        break
            self.driver = webdriver.Chrome(service=Service(dp), options=opts)
        except Exception as e:
            log.warning("webdriver-manager: %s – falling back to system driver", e)
            self.driver = webdriver.Chrome(options=opts)
        self.driver.execute_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        log.info("Chrome ready.")

    # ── Navigation helpers ────────────────────────────────────────────────────

    def _back(self):
        try:
            self.driver.find_element(
                By.CSS_SELECTOR, 'button[aria-label*="Back"]').click()
            time.sleep(BACK_DELAY)
        except Exception:
            try:
                self.driver.back()
                time.sleep(BACK_DELAY)
            except Exception:
                pass

    def _results(self):
        for sel in ['div[role="article"]', 'a.hfpxzc']:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                return els
        return self.driver.find_elements(
            By.XPATH, '//a[contains(@href,"/maps/place/")]')

    # ── Google Maps search + scroll ───────────────────────────────────────────

    def search_and_scroll(self, query: str, max_results: int):
        url = f"https://www.google.com/maps/search/{query}+in+{LOCATION}"
        for attempt in range(3):
            try:
                self.driver.get(url)
                time.sleep(10 if attempt == 0 else 6)
                break
            except Exception as e:
                if attempt == 2: raise
                time.sleep(5)
        try:
            self.driver.find_element(
                By.XPATH, "//button[contains(.,'Accept all')]").click()
            time.sleep(2)
        except Exception:
            pass
        container = None
        for by, sel in [
            (By.CSS_SELECTOR, 'div[role="feed"]'),
            (By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf'),
            (By.CSS_SELECTOR, '[aria-label*="Results"]'),
            (By.XPATH, '//div[@role="main"]//div[contains(@class,"m6QErb")]'),
        ]:
            try:
                container = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((by, sel)))
                break
            except Exception:
                continue
        if not container:
            raise RuntimeError("Results container not found")
        prev_h = 0
        for _ in range(20):
            self.driver.execute_script(
                'arguments[0].scrollTop=arguments[0].scrollHeight', container)
            time.sleep(SCROLL_DELAY)
            new_h = self.driver.execute_script(
                'return arguments[0].scrollHeight', container)
            n = len(self.driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]'))
            log.info("  Scrolled → %d results", n)
            if new_h == prev_h or n >= max_results:
                break
            prev_h = new_h

    # ── Extract business info (no email – fast) ───────────────────────────────

    def extract_info(self, element, category: str):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.3)
            element.click()
            time.sleep(CLICK_DELAY)
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1')))
        except Exception:
            return None

        d = {k: '' for k in FIELDNAMES}
        d['Category'] = category
        try:
            d['Business_Name'] = self.driver.find_element(
                By.CSS_SELECTOR, 'h1.DUwDvf').text.strip()
        except Exception:
            pass
        try:
            r = self.driver.find_element(
                By.CSS_SELECTOR, 'div.F7nice span[aria-label*="stars"]')
            m = re.search(r'([\d.]+)\s*stars', r.get_attribute('aria-label') or '')
            if m: d['Rating'] = m.group(1)
            rv = self.driver.find_element(
                By.CSS_SELECTOR, 'div.F7nice span[aria-label*="reviews"]')
            m2 = re.search(r'([\d,]+)\s*reviews', rv.get_attribute('aria-label') or '')
            if m2: d['Review_Count'] = m2.group(1).replace(',', '')
        except Exception:
            pass
        for btn in self.driver.find_elements(By.CSS_SELECTOR, 'button[data-item-id]'):
            lbl = btn.get_attribute('aria-label') or ''
            if 'Address:' in lbl:
                d['Address'] = lbl.replace('Address:', '').strip()
            elif 'Phone:' in lbl or lbl.lower().startswith('phone'):
                d['Phone'] = lbl.replace('Phone:', '').strip()
            elif 'Website:' in lbl or 'website' in lbl.lower():
                c = btn.get_attribute('data-item-id') or btn.get_attribute('href') or ''
                if c.startswith('http'): d['Website'] = c
        if not d['Website']:
            for sel in ['a[data-item-id*="authority"]', 'a[aria-label*="Website"]',
                        'a[data-tooltip*="website" i]']:
                try:
                    a = self.driver.find_element(By.CSS_SELECTOR, sel)
                    h = a.get_attribute('href') or ''
                    if h.startswith('http') and 'google.com/maps' not in h:
                        if not any(x in h.lower() for x in
                                   ['facebook.com','instagram.com','twitter.com',
                                    'maps.app.goo.gl']):
                            d['Website'] = h
                            break
                except Exception:
                    continue
        d['Google_Maps_URL'] = self.driver.current_url.split('&')[0]
        return d

    # ── Process a batch (parallel email fetch + save) ─────────────────────────

    def flush_batch(self, batch: list) -> int:
        if not batch:
            return 0
        batch = fetch_emails_batch(batch)   # parallel email fetch
        saved = 0
        for biz in batch:
            if count_csv_rows() >= TARGET_COUNT:
                return saved
            email = biz.get('Email', '').strip().lower()
            name  = biz.get('Business_Name', '').strip().lower()
            if not is_valid_email(email):
                continue
            if email in self.existing_emails or name in self.existing_names:
                log.debug("  ⊘ dup: %s", email)
                continue
            if append_record_safe(biz):
                self.existing_emails.add(email)
                self.existing_names.add(name)
                self.new_count += 1
                saved += 1
                log.info("  ✅ [%d/10000] %s | %s",
                         count_csv_rows(), biz['Business_Name'], email)
        return saved

    # ── Process one query (shared by both modes) ──────────────────────────────

    def _process_query(self, query: str, category: str, max_n: int):
        try:
            self.search_and_scroll(query, max_n)
        except Exception as e:
            log.warning("Search failed: %s – skip", e)
            return

        idx, batch = 0, []
        while count_csv_rows() < TARGET_COUNT:
            results = self._results()
            if idx >= len(results):
                break
            biz = self.extract_info(results[idx], category)
            idx += 1
            if not biz or not biz.get('Business_Name'):
                self._back()
                continue
            if biz['Business_Name'].strip().lower() in self.existing_names:
                log.debug("  ⊘ dup name: %s", biz['Business_Name'])
                self._back()
                continue
            if not biz.get('Website'):
                self._back()
                continue
            batch.append(biz)
            self._back()

            if len(batch) >= EMAIL_BATCH_SIZE:
                n = self.flush_batch(batch)
                log.info("  batch(%d): %d emails found. New total=%d",
                         len(batch), n, count_csv_rows())
                batch = []

        if batch:
            self.flush_batch(batch)
        time.sleep(CATEGORY_DELAY)

    # ── Main run ──────────────────────────────────────────────────────────────

    def run(self):
        log.info("=" * 65)
        mode = "queue" if QUEUE_FILE else f"{len(SEARCH_QUERIES)} queries (slice)"
        log.info("Worker %d  |  %s  |  batch=%d  threads=%d",
                 WORKER_ID, mode, EMAIL_BATCH_SIZE, EMAIL_THREADS)
        log.info("=" * 65)
        base_count, self.existing_emails, self.existing_names = load_existing()
        log.info("Existing: %d records, %d emails known", base_count, len(self.existing_emails))

        self.setup_driver()
        t0 = datetime.now()
        try:
            if QUEUE_FILE:
                # ── Queue mode: pop atomically until queue empty / target ──
                qi = 0
                while count_csv_rows() < TARGET_COUNT:
                    item = pop_query()
                    if item is None:
                        log.info("Queue empty – worker %d done.", WORKER_ID)
                        break
                    qi += 1
                    log.info("")
                    log.info("── [Q%d] %s", qi, item['q'])
                    self._process_query(item['q'], item['cat'], item['max'])
            else:
                # ── Slice mode (legacy) ───────────────────────────────────
                for qi, (query, category, max_n) in enumerate(SEARCH_QUERIES):
                    if count_csv_rows() >= TARGET_COUNT:
                        log.info("🎉 Target reached – worker %d done.", WORKER_ID)
                        break
                    log.info("")
                    log.info("── [%d/%d] %s", qi + 1, len(SEARCH_QUERIES), query)
                    self._process_query(query, category, max_n)

        except KeyboardInterrupt:
            log.info("Worker %d interrupted.", WORKER_ID)
        except Exception as e:
            log.error("Worker %d crashed: %s", WORKER_ID, e, exc_info=True)
        finally:
            if self.driver:
                self.driver.quit()
                log.info("Worker %d browser closed.", WORKER_ID)

        elapsed = str(datetime.now() - t0).split('.')[0]
        log.info("Worker %d finished. Added %d records in %s.",
                 WORKER_ID, self.new_count, elapsed)


if __name__ == '__main__':
    Worker().run()
