#!/usr/bin/env python3
"""Collect 50 historical medical-paper abstracts from six exact flagship journals.

Run: python collect_historical_medical.py --output-root PATH
PATH is the historical-2022 directory (contains shards/ and fulltexts/).
Requires requests. Uses public Europe PMC metadata and openly accessible full text.
The sample is a journal/year-stratified convenience sample, not a systematic review.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET

import requests

API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
ACCESS_DATE = "2026-10-30"
JOURNALS = (
    ("New England Journal of Medicine", "0028-4793", 2),
    ("The Lancet", "0140-6736", 2),
    ("JAMA", "0098-7484", 2),
    ("BMJ", "0959-8138", 2),
    ("Nature Medicine", "1078-8956", 1),
    ("Nature", "0028-0836", 1),
)
YEARS = range(2018, 2023)
EXCLUDED_TYPES = {
    "editorial", "letter", "comment", "published erratum", "correction",
    "news", "historical article", "biography", "retracted publication",
    "retraction of publication", "expression of concern", "clinical trial protocol",
    "preprint", "congress", "interview", "personal narrative",
}
EXCLUDED_TITLES = re.compile(
    r"^(?:correction(?:s)?|erratum|author correction|publisher correction|"
    r"retraction|expression of concern)\b|\bstudy protocol\b|\bprotocol for\b", re.I
)


def clean(text):
    class AbstractParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)
        def handle_starttag(self, tag, attrs):
            if tag in {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6"}:
                self.parts.append("\n")
        def handle_endtag(self, tag):
            if tag in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6"}:
                self.parts.append("\n")
    parser = AbstractParser()
    parser.feed(text or "")
    parser.close()
    return "\n".join(re.sub(r"\s+", " ", line).strip() for line in "".join(parser.parts).splitlines() if line.strip()).strip()


def get(url, **kwargs):
    """One bounded retry for transient errors; no retry on paywalls or missing files."""
    for attempt in range(2):
        try:
            response = requests.get(
                url, timeout=25,
                headers={"User-Agent": "HistoricalPaperWritingCorpus/1.0 (research metadata collection)"},
                **kwargs,
            )
            if response.status_code in (429, 500, 502, 503, 504) and attempt == 0:
                time.sleep(0.5)
                continue
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == 1:
                raise
            if "response" in locals() and response.status_code < 500 and response.status_code != 429:
                raise
            time.sleep(0.5)
    raise RuntimeError("request did not complete")


def query_stratum(journal, issn, year, count):
    query = (f"ISSN:{issn} AND PUB_YEAR:{year} AND "
             f"FIRST_PDATE:[{year}-01-01 TO {year}-12-31] AND HAS_ABSTRACT:y")
    if journal == "Nature":
        query += " AND (TITLE_ABS:patient* OR TITLE_ABS:clinical OR TITLE_ABS:disease OR TITLE_ABS:cancer)"
    response = get(API + "/search", params={
        "query": query, "format": "json", "resultType": "core", "pageSize": 100,
    })
    data = response.json()
    candidates = data.get("resultList", {}).get("result", [])
    rejected = Counter()
    eligible = []
    for raw in candidates:
        ji = raw.get("journalInfo", {}).get("journal", {})
        if issn not in (ji.get("issn"), ji.get("essn")):
            rejected["journal_issn_mismatch"] += 1
            continue
        try:
            pubyear = int(raw.get("pubYear", "0"))
            firstdate = date.fromisoformat(raw.get("firstPublicationDate", ""))
        except (ValueError, TypeError):
            rejected["missing_valid_year_or_date"] += 1
            continue
        if pubyear != year or firstdate.year != year or firstdate > date(2022, 12, 31):
            rejected["outside_stratum_or_cutoff"] += 1
            continue
        abstract = clean(raw.get("abstractText", ""))
        title = clean(raw.get("title", ""))
        types = raw.get("pubTypeList", {}).get("pubType", [])
        lower_types = {t.lower() for t in types}
        if len(abstract.split()) < 70:
            rejected["abstract_under_70_words"] += 1
            continue
        if lower_types & EXCLUDED_TYPES or EXCLUDED_TITLES.search(title):
            rejected["excluded_type_or_protocol_title"] += 1
            continue
        if ("review" in lower_types and not (
            {"systematic review", "meta-analysis"} & lower_types or
            re.search(r"systematic review|meta.analysis", title, re.I)
        )):
            rejected["narrative_review"] += 1
            continue
        if "journal article" not in lower_types and not (lower_types & {"systematic review", "meta-analysis"}):
            rejected["not_article_or_systematic_review"] += 1
            continue
        eligible.append(raw)
    # Prefer obtainable full text, then deterministic PMID order. Selection does not
    # equate journal status, citation counts, or recency with writing quality.
    eligible.sort(key=lambda x: (
        0 if x.get("isOpenAccess") == "Y" else 1,
        0 if x.get("pmcid") else 1,
        x.get("id", ""),
    ))
    chosen = eligible[:count]
    if len(chosen) != count:
        raise RuntimeError(f"{journal} {year}: need {count}, found {len(chosen)} eligible")
    records = []
    for rank, raw in enumerate(chosen, 1):
        pmid = raw["id"]
        ji = raw["journalInfo"]["journal"]
        record = {
            "id": f"med-{pmid}", "title": clean(raw["title"]),
            "authors": [a.get("fullName", "") for a in raw.get("authorList", {}).get("author", [])
                        if a.get("fullName")],
            "venue": journal, "year": int(raw["pubYear"]),
            "url": f"https://europepmc.org/article/MED/{pmid}",
            "abstract": clean(raw["abstractText"]), "doi": raw.get("doi"),
            "pmid": pmid, "pmcid": raw.get("pmcid"),
            "journal_issn": issn, "source_journal_title": ji.get("title"),
            "first_publication_date": raw["firstPublicationDate"],
            "accessed_date": ACCESS_DATE,
            "selection_method": "2018-2022 exact-journal/year strata; 2/year for NEJM, Lancet, JAMA, BMJ and 1/year for Nature Medicine, Nature; public-full-text availability preferred then ascending PMID; first 100 API results per stratum; no probability or systematic-review claim",
            "collection_level": "abstract", "semantic_review_performed": False,
            "full_text_status": "not_attempted", "publication_types": raw.get("pubTypeList", {}).get("pubType", []),
            "source_api": API + "/search", "source_query": query,
            "is_open_access": raw.get("isOpenAccess") == "Y",
            "selection_rank_within_stratum": rank,
        }
        record["_fullTextUrlList"] = raw.get("fullTextUrlList", {}).get("fullTextUrl", [])
        records.append(record)
    return records, {
        "event": "stratum_selection", "journal": journal, "issn": issn,
        "year": year, "query": query, "api_hit_count": data.get("hitCount"),
        "candidate_count": len(candidates), "eligible_count": len(eligible),
        "selected_count": len(records), "rejected_reasons": dict(rejected),
        "source_url": response.url,
    }


def download_full_text(record, root):
    attempts = []
    pmcid = record.get("pmcid")
    candidates = []
    if pmcid:
        candidates.append(("xml", f"{API}/{pmcid}/fullTextXML"))
    for item in record.pop("_fullTextUrlList", []):
        availability = str(item.get("availability", "")).lower()
        if str(item.get("documentStyle", "")).lower() == "pdf" and any(
            a in availability for a in ("free", "open access")
        ):
            candidates.append(("pdf", item["url"]))
    for extension, url in candidates:
        try:
            response = get(url)
            data = response.content
            if len(data) > 30 * 1024 * 1024:
                raise ValueError("file over 30 MiB bounded-download limit")
            if extension == "xml":
                tree = ET.fromstring(data)
                if tree.find(".//body") is None:
                    raise ValueError("XML has no article body")
            elif not data.startswith(b"%PDF-"):
                raise ValueError("response is not a PDF")
            path = root / "fulltexts" / f"{record['id']}.{extension}"
            path.write_bytes(data)
            record.update({
                "full_text_status": "downloaded_open_access_xml" if extension == "xml" else "downloaded_public_pdf",
                "full_text_local_path": path.relative_to(root).as_posix(),
                "full_text_sha256": hashlib.sha256(data).hexdigest(),
                "full_text_source_url": response.url,
            })
            attempts.append({"url": url, "status": "downloaded", "bytes": len(data), "format": extension})
            break
        except (requests.RequestException, ValueError, ET.ParseError) as exc:
            attempts.append({"url": url, "status": "unavailable", "reason": str(exc)[:250]})
    else:
        record["full_text_status"] = "unavailable_after_public_attempts" if candidates else "no_public_full_text_link_in_metadata"
    return record, {"event": "full_text_attempts", "id": record["id"], "attempts": attempts,
                    "final_status": record["full_text_status"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_root.resolve()
    (root / "shards").mkdir(parents=True, exist_ok=True)
    (root / "fulltexts").mkdir(parents=True, exist_ok=True)
    logs = [{"event": "collection_started", "accessed_date": ACCESS_DATE,
             "actual_utc_timestamp": datetime.now(timezone.utc).isoformat(),
             "cutoff": "2022-12-31", "max_workers": 4, "timeout_seconds": 25,
             "max_retries": 1, "journal_allowlist": [{"venue": x[0], "issn": x[1]} for x in JOURNALS]}]
    records = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(query_stratum, journal, issn, year, count)
                   for journal, issn, count in JOURNALS for year in YEARS]
        for future in as_completed(futures):
            selected, log = future.result()
            records.extend(selected)
            logs.append(log)
            print(f"selected {log['journal']} {log['year']}: {len(selected)}", flush=True)
    if len(records) != 50 or len({x["id"] for x in records}) != 50:
        raise RuntimeError("expected exactly 50 distinct abstracts")
    downloaded = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(download_full_text, r, root) for r in records]):
            record, log = future.result()
            downloaded.append(record)
            logs.append(log)
            print(f"full text {record['id']}: {record['full_text_status']}", flush=True)
    downloaded.sort(key=lambda x: (x["venue"], x["year"], x["id"]))
    shard = root / "shards" / "medical.jsonl"
    with shard.open("w", encoding="utf-8", newline="\n") as handle:
        for row in downloaded:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (root / "shards" / "medical-log.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in logs), encoding="utf-8")
    summary = {
        "record_count": len(downloaded), "cutoff": "2022-12-31", "accessed_date": ACCESS_DATE,
        "venues": dict(Counter(r["venue"] for r in downloaded)),
        "years": dict(sorted(Counter(r["year"] for r in downloaded).items())),
        "full_text_statuses": dict(Counter(r["full_text_status"] for r in downloaded)),
        "abstracts_semantically_reviewed_in_corpus": 0,
        "inspection_note": "Separate medical-inspection files identify the inspected subset and actual section levels; collection records remain metadata/abstract-level.",
        "selection_biases": ["six selected flagship journals", "2018-2022 only", "fixed journal/year quotas", "first 100 API results per stratum", "open-access availability preferred", "Nature restricted to health-related title/abstract terms"],
        "not_claimed": ["systematic coverage", "full-text review of all papers", "causal relation between writing style and acceptance", "quality ranking of journals or articles"],
    }
    (root / "shards" / "medical-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
