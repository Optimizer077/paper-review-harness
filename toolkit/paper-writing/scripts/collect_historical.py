#!/usr/bin/env python3
"""Collect/merge the 300-paper, pre-2023 top-venue writing reference corpus.

Three portable shard collectors run concurrently when --collect is supplied.
The merge rejects incomplete counts, duplicate papers, dates after 2022, and
venues outside the explicitly chosen scope. Downloading is not semantic review.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

VENUES = {
    "cvpr": "CVPR", "iccv": "ICCV", "neurips": "NeurIPS", "nips": "NeurIPS",
    "iclr": "ICLR", "icml": "ICML", "nature": "Nature",
    "nejm": "NEJM", "new england journal of medicine": "NEJM", "the new england journal of medicine": "NEJM",
    "the lancet": "The Lancet", "lancet": "The Lancet", "jama": "JAMA",
    "bmj": "BMJ", "bmj clinical research ed": "BMJ", "bmj (clinical research ed.)": "BMJ",
    "nature medicine": "Nature Medicine", "nat med": "Nature Medicine",
}
MEDICAL_ISSNS = {"NEJM": {"0028-4793", "1533-4406"}, "The Lancet": {"0140-6736", "1474-547X"},
                 "JAMA": {"0098-7484", "1538-3598"}, "BMJ": {"0959-8138", "1756-1833", "1468-5833"},
                 "Nature Medicine": {"1078-8956", "1546-170X"}, "Nature": {"0028-0836", "1476-4687"}}


def normalized_title(value):
    return re.sub(r"[^\w]+", "", value.casefold())


def validate_rows(rows, root, expected=300):
    if len(rows) != expected:
        raise ValueError(f"Expected exactly {expected} papers, received {len(rows)}")
    seen = {k: set() for k in ("id", "url", "title", "doi")}
    downloaded = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Paper rows must be objects")
        for key in ("id", "title", "url", "abstract", "venue"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Paper lacks nonempty {key}")
        if len(row["abstract"].split()) < 20:
            raise ValueError(f"Abstract implausibly short for {row['id']}")
        if type(row.get("year")) is not int or not 1900 <= row["year"] <= 2022:
            raise ValueError(f"Paper outside 2022 cutoff: {row['id']}")
        canonical = VENUES.get(row["venue"].strip().casefold())
        if not canonical:
            raise ValueError(f"Venue outside explicit allowlist: {row['venue']}")
        row["venue"] = canonical
        for key in ("id", "url", "title", "doi"):
            value = normalized_title(row[key]) if key == "title" else str(row.get(key) or "").strip().casefold()
            if not value:
                continue
            if value in seen[key]:
                raise ValueError(f"Duplicate {key}: {value}")
            seen[key].add(value)
        if canonical in MEDICAL_ISSNS:
            value = row.get("journal_issn", "")
            issns = set(re.findall(r"\d{4}-[\dXx]{4}", json.dumps(value)))
            if not issns.intersection(MEDICAL_ISSNS[canonical]):
                raise ValueError(f"Medical journal identity not verified by ISSN: {row['id']}")
            first = row.get("first_publication_date")
            if not isinstance(first, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", first) or date.fromisoformat(first) > date(2022, 12, 31):
                raise ValueError(f"Medical first-publication date missing/after cutoff: {row['id']}")
        relative = row.get("full_text_local_path")
        if relative:
            source = (root / relative).resolve()
            if not source.is_relative_to(root.resolve()) or not source.is_file():
                raise ValueError(f"Full-text path missing/outside corpus: {relative}")
            actual = hashlib.sha256(source.read_bytes()).hexdigest()
            if actual != row.get("full_text_sha256"):
                raise ValueError(f"Full-text hash mismatch: {row['id']}")
            downloaded += 1
    return downloaded


def merge(root):
    rows = []
    for name in ("cv", "ml", "medical"):
        path = root / "shards" / (name + ".jsonl")
        if not path.is_file():
            raise ValueError(f"Shard missing: {path}")
        shard = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        quota, family = {"cv": (100, {"CVPR", "ICCV"}), "ml": (150, {"NeurIPS", "ICLR", "ICML"}),
                         "medical": (50, set(MEDICAL_ISSNS))}[name]
        if len(shard) != quota:
            raise ValueError(f"{name} shard needs exactly {quota} papers, received {len(shard)}")
        if any(VENUES.get(str(r.get("venue", "")).strip().casefold()) not in family for r in shard):
            raise ValueError(f"{name} shard contains a paper outside its venue family")
        rows.extend(shard)
    downloads = validate_rows(rows, root)
    expected_counts = {"CVPR": 75, "ICCV": 25, "NeurIPS": 75, "ICLR": 50, "ICML": 25,
                       "NEJM": 10, "The Lancet": 10, "JAMA": 10, "BMJ": 10, "Nature Medicine": 5, "Nature": 5}
    if Counter(r["venue"] for r in rows) != Counter(expected_counts):
        raise ValueError("Per-venue counts do not match the documented 300-paper sampling plan")
    rows.sort(key=lambda r: (r["venue"], r["year"], r["id"]))
    registry = root / "papers.jsonl"
    registry.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    summary = {"version": 2, "cutoff_year": 2022, "requested_papers": 300, "total_records": len(rows),
               "counts": dict(sorted(Counter(r["venue"] for r in rows).items())),
               "years": dict(sorted(Counter(str(r["year"]) for r in rows).items())),
               "abstract_records": len(rows), "fulltext_downloaded": downloads,
               "corpus_sha256": hashlib.sha256(registry.read_bytes()).hexdigest(),
               "date_and_venue_validation": "passed", "source_of_truth": "papers.jsonl",
               "limits": ["Explicit venue selection, not an objective ranking or representative sample.",
                          "Collected abstracts and downloaded bodies do not imply semantic reading or scientific validation.",
                          "Current submission guidance is separate from the historical paper corpus."]}
    inspected = set()
    for name in ("cv", "ml", "medical"):
        inspection_path = root / (name + "-inspection.json")
        if inspection_path.exists():
            data = json.loads(inspection_path.read_text(encoding="utf-8-sig"))
            for item in data.get("inspections", data.get("records", [])):
                rid = item.get("id", item.get("record_id"))
                if rid not in {r["id"] for r in rows}:
                    raise ValueError(f"Inspection references an unknown corpus paper: {rid}")
                inspected.add(rid)
    summary["specialist_papers_inspected_at_abstract_or_selected_section_level"] = len(inspected)
    summary["complete_paper_scientific_reviews_claimed"] = 0
    (root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--collect", action="store_true", help="Run three collectors concurrently before merging")
    args = p.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    try:
        if args.collect:
            scripts = Path(__file__).resolve().parent
            def run(name):
                command = [sys.executable, str(scripts / f"collect_historical_{name}.py"), "--output-root", str(args.output_root)]
                log = args.output_root / f"{name}-cli.log"
                with log.open("w", encoding="utf-8") as stream:
                    result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
                if result.returncode:
                    raise ValueError(f"{name} collector exited {result.returncode}; inspect {log}")
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(run, ("cv", "ml", "medical")))
        print(json.dumps(merge(args.output_root), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError) as exc:
        p.exit(2, f"Invalid corpus: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
