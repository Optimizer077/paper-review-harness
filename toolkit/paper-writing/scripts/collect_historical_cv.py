#!/usr/bin/env python3
"""Collect a deterministic, pre-2023 CVF main-conference sample.

Usage: python collect_historical_cv.py --output-root output/research/historical-2022
Requires requests and beautifulsoup4; pymupdf is optional for inspection extracts.
Downloads are publicly available publisher copies; downloading is not reading.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE = 'https://openaccess.thecvf.com/'
PLAN = [('CVPR', 2020, 25), ('CVPR', 2021, 25), ('CVPR', 2022, 25),
        ('ICCV', 2019, 12), ('ICCV', 2021, 13)]
LOCAL = threading.local()
LOG = []
LOCK = threading.Lock()

def log(**item):
    with LOCK:
        LOG.append(item)

def session():
    if not hasattr(LOCAL, 'session'):
        LOCAL.session = requests.Session()
        LOCAL.session.headers['User-Agent'] = 'HistoricalPaperWritingResearch/1.0 (public scholarly metadata; bounded requests)'
    return LOCAL.session

def get(url, binary=False):
    for attempt in range(2):
        try:
            response = session().get(url, timeout=(8, 20))
            response.raise_for_status()
            value = response.content if binary else response.text
            log(url=url, status='ok', http_status=response.status_code,
                attempt=attempt + 1, bytes=len(response.content))
            return value
        except requests.RequestException as exc:
            log(url=url, status='error', attempt=attempt + 1, error=str(exc))
            if attempt == 0:
                time.sleep(0.2)
    return None

def listing(venue, year, count):
    url = f'{BASE}{venue}{year}' + ('?day=all' if year >= 2021 else '')
    html = get(url)
    if html is None:
        raise RuntimeError(f'Unable to read {url}')
    soup = BeautifulSoup(html, 'html.parser')
    pages = [soup]
    if not soup.select('dt.ptitle a'):
        for anchor in soup.select('a[href]'):
            if re.fullmatch(rf'{venue}{year}\.py\?day=\d{{4}}-\d{{2}}-\d{{2}}', anchor['href']):
                day_html = get(urljoin(BASE, anchor['href']))
                if day_html:
                    pages.append(BeautifulSoup(day_html, 'html.parser'))
    found = {}
    for page in pages:
        for anchor in page.select('dt.ptitle a'):
            link = urljoin(BASE, anchor.get('href', ''))
            if re.search(rf'/content(?:_|/){venue}_?{year}/html/', link) and 'workshop' not in link.lower():
                found[link] = anchor.get_text(' ', strip=True)
    items = sorted(found.items(), key=lambda pair: (pair[1].casefold(), pair[0]))
    if len(items) < count:
        raise RuntimeError(f'{venue} {year}: found only {len(items)} main papers')
    # Evenly spaced positions across the full title-sorted proceedings, including endpoints.
    positions = [round(i * (len(items) - 1) / (count - 1)) for i in range(count)]
    selected = [(venue, year, items[i][0], url, i, len(items)) for i in positions]
    log(url=url, status='selection', venue=venue, year=year, available=len(items),
        requested=count, positions=positions, order='title.casefold(), url')
    return selected, [(venue, year, u, url, i, len(items)) for i, (u, _) in enumerate(items) if i not in positions]

def paper(item):
    venue, year, url, listing_url, rank, population = item
    html = get(url)
    if html is None:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    title_node, abstract_node = soup.select_one('#papertitle'), soup.select_one('#abstract')
    author_node = soup.select_one('#authors')
    title = title_node.get_text(' ', strip=True) if title_node else ''
    abstract = abstract_node.get_text(' ', strip=True) if abstract_node else ''
    author_text = author_node.get_text(' ', strip=True) if author_node else ''
    if not title or len(abstract.split()) < 25 or str(year) not in author_text or f'({venue})' not in author_text or year > 2022:
        log(url=url, status='invalid', reason='missing title/abstract or publication provenance')
        return None
    authors = (author_node.select_one('i').get_text(' ', strip=True).split(', ')
               if author_node and author_node.select_one('i') else [])
    pdf = next((urljoin(BASE, a['href']) for a in soup.select('a[href]')
                if a.get_text(strip=True).lower() == 'pdf' and a['href'].lower().endswith('.pdf')), None)
    ident = f'cv-{venue.lower()}-{year}-' + hashlib.sha256(url.encode()).hexdigest()[:12]
    return {'id': ident, 'title': title, 'authors': authors, 'venue': venue, 'year': year,
            'url': url, 'abstract': abstract, 'pdf_url': pdf, 'accessed_date': '2026-10-30',
            'selection_method': 'Evenly spaced ranks in official main-conference title-sorted listing; deterministic endpoint-inclusive rounding.',
            'selection_source_url': listing_url, 'selection_rank_zero_based': rank,
            'selection_population_size': population, 'collection_level': 'abstract',
            'semantic_review_performed': False, 'full_text_status': 'not_attempted'}

def download(record, root):
    target = root / 'fulltexts' / f"{record['id']}.pdf"
    if target.exists() and target.read_bytes()[:4] == b'%PDF':
        content = target.read_bytes()
    elif not record['pdf_url']:
        record['full_text_status'] = 'no_public_pdf_link'
        return record
    else:
        content = get(record['pdf_url'], binary=True)
        if not content or content[:4] != b'%PDF':
            record['full_text_status'] = 'download_failed'
            return record
        target.write_bytes(content)
    record.update(full_text_status='downloaded_not_semantically_read',
                  full_text_local_path=target.relative_to(root).as_posix(),
                  full_text_sha256=hashlib.sha256(content).hexdigest())
    return record

def extract_inspection_candidates(records, root):
    try:
        import fitz
    except ImportError:
        return []
    selected = []
    groups = [('CVPR', 2020, 2), ('CVPR', 2021, 1), ('CVPR', 2022, 1), ('ICCV', 2019, 1), ('ICCV', 2021, 1)]
    for venue, year, number in groups:
        for record in [r for r in records if r['venue'] == venue and r['year'] == year and r.get('full_text_local_path')]:
            try:
                doc = fitz.open(root / record['full_text_local_path'])
                # Publisher PDFs preserve column order better in source block order;
                # sorting purely by y coordinate interleaves two-column sentences.
                text = '\n'.join(page.get_text(sort=False) for page in list(doc)[:3])
                match = re.search(r'(?:\n|^)\s*1[.\s]+Introduction\s*\n', text, re.I)
                if not match:
                    doc.close()
                    continue
                intro = text[match.end():]
                stop = re.search(r'\n\s*2[.\s]+(?:Related|Background|Preliminar|Method)', intro, re.I)
                if stop:
                    intro = intro[:stop.start()]
                intro = intro[:14000]
                if len(intro.split()) < 100:
                    doc.close()
                    continue
                selected.append({'id': record['id'], 'title': record['title'], 'venue': venue,
                                 'year': year, 'url': record['url'], 'pdf_url': record['pdf_url'],
                                 'full_text_local_path': record['full_text_local_path'],
                                 'abstract': record['abstract'], 'introduction_extracted': intro,
                                 'extraction_pages_one_based': [1, 2, 3],
                                 'inspection_level': 'extracted_candidate_not_yet_semantically_reviewed',
                                 'extraction_note': 'PDF text order can contain figure captions or page headers; inspect before interpreting.'})
                doc.close()
                number -= 1
                if number == 0:
                    break
            except Exception as exc:
                log(url=record['url'], status='extraction_error', error=str(exc))
    (root / 'cv-inspection-candidates.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding='utf-8')
    return selected

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, default=Path('output/research/historical-2022'))
    parser.add_argument('--download', action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    root = args.output_root
    (root / 'shards').mkdir(parents=True, exist_ok=True)
    (root / 'fulltexts').mkdir(parents=True, exist_ok=True)
    selected, reserve, records = [], {}, []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(listing, *row): row for row in PLAN}
        for future in as_completed(futures):
            row = futures[future]
            picked, extra = future.result()
            selected.extend(picked)
            reserve[(row[0], row[1])] = extra
        for future in as_completed([pool.submit(paper, item) for item in sorted(selected)]):
            record = future.result()
            if record:
                records.append(record)
    for venue, year, count in PLAN:
        have = sum(r['venue'] == venue and r['year'] == year for r in records)
        for item in reserve[(venue, year)]:
            if have >= count:
                break
            record = paper(item)
            if record:
                record['selection_method'] += ' Invalid selected pages replaced by earliest remaining title rank.'
                records.append(record)
                have += 1
    records.sort(key=lambda r: (r['venue'], r['year'], r['title'].casefold(), r['url']))
    def save_records():
        (root / 'shards' / 'cv.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
    save_records()
    print(f'Collected {len(records)} valid abstracts.', flush=True)
    if args.download:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i, future in enumerate(as_completed([pool.submit(download, r, root) for r in records]), 1):
                future.result()
                if i % 20 == 0:
                    save_records()
                    print(f'PDF attempts completed: {i}/{len(records)}', flush=True)
    save_records()
    candidates = extract_inspection_candidates(records, root)
    summary = {'generated_date': '2026-10-30', 'cutoff_year_inclusive': 2022,
               'record_count': len(records), 'abstracts_validated': len(records),
               'pdfs_downloaded': sum(r['full_text_status'] == 'downloaded_not_semantically_read' for r in records),
               'inspection_candidates_extracted': len(candidates), 'semantic_inspections': 0,
               'publication_strata': [{'venue': v, 'year': y, 'count': sum(r['venue'] == v and r['year'] == y for r in records)} for v, y, _ in PLAN],
               'collection_scope': 'CVF official main conference, excluding workshops. Deterministic stratified sample, not quality-ranked or representative of all writing.',
               'network_policy': '4 workers maximum; 8 second connect/20 second read timeouts; at most one retry; no challenge bypass.'}
    (root / 'shards' / 'cv-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (root / 'shards' / 'cv-log.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in LOG), encoding='utf-8')
    print(json.dumps(summary), flush=True)
    if len(records) != 100:
        raise SystemExit('Expected exactly 100 CV records')

if __name__ == '__main__':
    main()
