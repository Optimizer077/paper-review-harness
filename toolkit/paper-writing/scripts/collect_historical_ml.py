#!/usr/bin/env python3
"""Collect a deterministic 150-paper ML shard (2020--2022, official main venues).

Requires requests, beautifulsoup4; PDF reading for inspection separately uses pypdf.
PDF download availability is recorded independently from semantic reading.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

QUOTAS = {"NeurIPS": {2020:25, 2021:25, 2022:25},
          "ICLR": {2020:17, 2021:17, 2022:16},
          "ICML": {2020:9, 2021:8, 2022:8}}
PMLR = {2020:119, 2021:139, 2022:162}
ACCESSED = "2026-10-30"
HOSTS = defaultdict(lambda: threading.BoundedSemaphore(4))
LOG_LOCK = threading.Lock()
LOG = []
LEGACY_ICLR = {}
PDF_DENIED = Counter()

def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()

def log(**entry):
    with LOG_LOCK:
        LOG.append(entry)

def fetch(url, binary=False):
    """At most two attempts, no retries on access-denied/challenge responses."""
    host = urlparse(url).netloc
    if binary and PDF_DENIED[host] >= 2:
        log(url=url, event="host_access_denied_circuit", request_type="pdf")
        return None
    for attempt in range(2):
        try:
            with HOSTS[urlparse(url).netloc]:
                response = requests.get(url, timeout=25, headers={
                    "User-Agent":"PaperWritingCorpus/1.0 (research; bounded requests)"})
            log(url=url, status=response.status_code, attempt=attempt+1,
                bytes=len(response.content), request_type="pdf" if binary else "metadata")
            if binary and response.status_code in (401,403):
                with LOG_LOCK:
                    PDF_DENIED[host] += 1
            if response.status_code in (401, 403, 404, 429):
                return None
            response.raise_for_status()
            if binary:
                return response.content if response.content.startswith(b"%PDF-") else None
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as error:
            log(url=url, error=str(error), attempt=attempt+1,
                request_type="pdf" if binary else "metadata")
    return None

def listing(venue, year):
    if venue == "ICLR" and year == 2020:
        index = "https://iclr.cc/virtual_2020/papers.json"
        raw = fetch(index)
        if not raw:
            raise RuntimeError(f"Listing unavailable: {index}")
        for item in json.loads(raw):
            url = f"https://iclr.cc/virtual_2020/poster_{item['id']}.html"
            LEGACY_ICLR[url] = item["content"]
        ordered = sorted(LEGACY_ICLR,key=lambda u:hashlib.sha256(u.encode()).hexdigest())
        log(event="listing",venue=venue,year=year,index=index,eligible=len(ordered),
            selection="ascending SHA-256 of canonical official paper URL")
        return venue,year,ordered
    if venue == "NeurIPS":
        index = f"https://proceedings.neurips.cc/paper/{year}"
    elif venue == "ICLR":
        index = f"https://iclr.cc/virtual/{year}/papers.html"
    else:
        index = f"https://proceedings.mlr.press/v{PMLR[year]}/"
    html = fetch(index)
    if not html:
        raise RuntimeError(f"Listing unavailable: {index}")
    soup = BeautifulSoup(html, "html.parser")
    found = {}
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if venue == "NeurIPS":
            matches = "-Abstract" in href and (year < 2022 or "-Conference.html" in href)
        elif venue == "ICLR":
            matches = bool(re.fullmatch(rf"/virtual/{year}/poster/\d+", href))
        else:
            matches = anchor.get_text(strip=True) == "abs" and f"/v{PMLR[year]}/" in href
        if matches:
            url = urljoin(index, href)
            found[url] = clean(anchor.get_text(" ", strip=True))
    # Seedless deterministic sampling spreads choices across the whole official listing.
    ordered = sorted(found, key=lambda u: hashlib.sha256(u.encode()).hexdigest())
    log(event="listing", venue=venue, year=year, index=index, eligible=len(ordered),
        selection="ascending SHA-256 of canonical official paper URL")
    return venue, year, ordered

def meta(soup, name):
    node = soup.find("meta", attrs={"name":name})
    return clean(node.get("content", "")) if node else ""

def parse_record(task):
    venue, year, url = task
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    title = meta(soup, "citation_title")
    authors = [clean(m.get("content", "")) for m in soup.find_all("meta", attrs={"name":"citation_author"})]
    pdf = meta(soup, "citation_pdf_url")
    if venue == "ICLR":
        title_node = soup.select_one("h1.event-title") or soup.find("h2")
        title = clean(title_node.get_text(" ", strip=True)) if title_node else ""
        authors_node = soup.select_one(".event-organizers")
        authors = [clean(a) for a in authors_node.get_text(" ", strip=True).split("⋅")] if authors_node else []
        abstract_node = soup.select_one(".abstract-text-inner") or soup.select_one("#abstractText")
        abstract = clean(abstract_node.get_text(" ", strip=True)) if abstract_node else ""
        review = next((a["href"] for a in soup.find_all("a", href=True)
                       if "openreview.net/forum?id=" in a["href"]), "")
        review_id = parse_qs(urlparse(review).query).get("id", [""])[0]
        pdf = f"https://openreview.net/pdf?id={review_id}" if review_id else ""
        if year == 2020:
            entry = LEGACY_ICLR[url]
            title = clean(entry["title"])
            authors = entry["authors"]
            abstract_node = soup.select_one("#abstractExample")
            abstract = clean(abstract_node.get_text(" ",strip=True)) if abstract_node else ""
            abstract = re.sub(r"^Abstract:\s*", "", abstract)
            review_id = url.rsplit("poster_",1)[-1].split(".html")[0]
            pdf = f"https://openreview.net/pdf?id={review_id}"
    elif venue == "ICML":
        node = soup.select_one("#abstract") or soup.select_one(".abstract")
        abstract = clean(node.get_text(" ", strip=True)) if node else ""
    else:
        heading = next((h for h in soup.find_all(re.compile("h[1-6]"))
                        if h.get_text(strip=True) == "Abstract"), None)
        node = heading.find_next("p") if heading else None
        abstract = clean(node.get_text(" ", strip=True)) if node else ""
    if abstract.startswith("Abstract "):
        abstract = abstract[9:].strip()
    if not title or not authors or len(abstract) < 80 or not pdf:
        log(event="record_rejected", url=url, title_present=bool(title),
            authors_present=bool(authors), abstract_characters=len(abstract), pdf_present=bool(pdf))
        return None
    identifier = f"ml-{venue.lower()}-{year}-" + hashlib.sha256(url.encode()).hexdigest()[:12]
    result = dict(id=identifier, title=title, authors=authors, venue=venue, year=year,
                  url=url, abstract=abstract, pdf_url=pdf, accessed_date=ACCESSED,
                  selection_method="Deterministic ascending SHA-256 of official main-conference paper URL; first valid records per fixed venue/year quota",
                  collection_level="abstract", semantic_review_performed=False,
                  full_text_status="not_attempted")
    doi = meta(soup,"citation_doi")
    if doi:
        result["doi"] = doi
    return result

def download(task):
    root, record = task
    target = root / "fulltexts" / f"{record['id']}.pdf"
    if target.exists() and target.read_bytes().startswith(b"%PDF-"):
        data = target.read_bytes()
        record["full_text_status"] = "downloaded"
        log(event="pdf_reused", url=record["pdf_url"], path=str(target))
    else:
        denied_before = PDF_DENIED[urlparse(record["pdf_url"]).netloc] >= 2
        data = fetch(record["pdf_url"], binary=True)
        record["full_text_status"] = "downloaded" if data else ("unavailable_host_access_denied" if denied_before else "unavailable_after_bounded_attempt")
        if data:
            target.write_bytes(data)
    if data:
        record["full_text_local_path"] = target.relative_to(root).as_posix()
        record["full_text_sha256"] = hashlib.sha256(data).hexdigest()
    return record

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_root.resolve()
    (root / "shards").mkdir(parents=True, exist_ok=True)
    (root / "fulltexts").mkdir(exist_ok=True)
    groups = [(v,y) for v, years in QUOTAS.items() for y in years]
    started = time.monotonic()
    records = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        indexes = list(pool.map(lambda t:listing(*t), groups))
        # Batch each venue/year. Invalid pages are replaced by the next deterministic URLs.
        pending = { (v,y):list(urls) for v,y,urls in indexes }
        counts = Counter()
        while any(counts[g] < QUOTAS[g[0]][g[1]] for g in groups):
            jobs = []
            for venue,year in groups:
                needed = QUOTAS[venue][year] - counts[(venue,year)]
                jobs.extend((venue,year,u) for u in pending[(venue,year)][:needed])
                pending[(venue,year)] = pending[(venue,year)][needed:]
            if not jobs:
                raise RuntimeError("Insufficient valid official metadata for required quotas")
            for record in pool.map(parse_record, jobs):
                if record:
                    records.append(record)
                    counts[(record["venue"],record["year"])] += 1
            print("Abstracts:", len(records), flush=True)
        records = list(pool.map(download, [(root,r) for r in records]))
    records.sort(key=lambda r:(r["venue"],r["year"],r["id"]))
    assert len(records) == 150 and len({r["url"] for r in records}) == 150
    assert all(2020 <= r["year"] <= 2022 and r["abstract"] and r["authors"] for r in records)
    shard = root / "shards" / "ml.jsonl"
    shard.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in records),encoding="utf-8")
    (root / "shards" / "ml-log.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in LOG), encoding="utf-8")
    summary = dict(records=len(records), venue_counts=dict(Counter(r["venue"] for r in records)),
                   year_counts=dict(Counter(r["year"] for r in records)),
                   venue_year_counts={f"{v}-{y}":n for (v,y),n in counts.items()},
                   full_text_counts=dict(Counter(r["full_text_status"] for r in records)),
                   semantic_reviewed_papers=0, quotas=QUOTAS, accessed_date=ACCESSED,
                   elapsed_seconds=round(time.monotonic()-started,1),
                   scope="Main-conference records only; fixed 2020--2022 quotas; not a representative or quality-ranked sample",
                   selection="First valid metadata pages ordered by SHA-256 of canonical official URL within each venue/year")
    inspection_path = root / "ml-inspection.json"
    if inspection_path.exists():
        inspected = json.loads(inspection_path.read_text(encoding="utf-8"))
        valid_ids = {r["id"] for r in records}
        matching = [i for i in inspected.get("inspections",[]) if i.get("record_id") in valid_ids]
        summary["semantic_reviewed_papers"] = len(matching)
        summary["semantic_review_level"] = "Abstract and introduction only; separate ml-inspection.json retained from prior documented review"
        summary["full_papers_read"] = 0
    (root / "shards" / "ml-summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

if __name__ == "__main__":
    main()
