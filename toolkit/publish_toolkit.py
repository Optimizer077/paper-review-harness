#!/usr/bin/env python3
"""Export a deterministic, metadata-only public toolkit from an output root.

Usage: python publish_toolkit.py --source OUTPUT --dest STAGING_TOOLKIT
Only the explicit public allowlist is read. No network or Git operations occur.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


EXPORTER = "paper-writing-public-export-v1"
MANIFEST = "public-manifest.json"
TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".yaml", ".yml", ".txt"}
SKIP_PARTS = {"__pycache__", ".git", ".pytest_cache", "archive", "node_modules"}
TESTS = {
    "test_paper_harness.py", "test_packet_invariants.py", "test_scoring.py",
    "test_scoring_v2.py", "test_scoring_v2_independent.py",
}
METADATA_KEYS = {
    "id", "title", "authors", "venue", "year", "url", "doi", "pmid", "pmcid",
    "journal_issn", "source_journal_title", "first_publication_date", "accessed_date",
    "selection_method", "selection_population_size", "selection_rank_within_stratum",
    "selection_rank_zero_based", "selection_source_url", "source_api", "source_query",
    "publication_types", "is_open_access", "pdf_url", "full_text_source_url",
    "semantic_review_performed", "semantic_review_sections", "full_paper_read",
}
PRIVATE_PATH = re.compile(
    r"(?i)(?<![\w])(?:[a-z]:[\\/][^\s\"'<>`]+"
    r"|/(?:Users|home)/[^\s\"'<>`]+|file:" r"///[^\s\"'<>`]+)"
)
SECRET = re.compile(
    r"(?<![A-Za-z0-9])(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}"
    r"|sk-(?:proj-)?[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)"
)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def portable_markdown(content, source, relative):
    # Convert known original-host links before converting command examples.
    source_root = source.parent
    variants = {str(source_root), source_root.as_posix()}
    for root in sorted(variants, key=len, reverse=True):
        for slash in ("/", "\\"):
            prefix = root + slash + source.name + slash
            pattern = re.compile(r"\]\(<?" + re.escape(prefix) + r"([^)>]+)>?\)", re.I)
            def relative_link(match):
                target = match.group(1).replace("\\", "/")
                target = re.sub(r":\d+$", "", target)
                return "](" + os.path.relpath(target, relative.parent.as_posix()).replace("\\", "/") + ")"
            content = pattern.sub(relative_link, content)
        content = content.replace(root, ".")
    content = content.replace("output/", "").replace("output\\", "")
    content = content.replace("project root, `.`", "toolkit root (this directory's top-level `README.md`)")
    # The private toolkit self-assessment is intentionally excluded.
    content = content.replace("evaluation-ratings.json", "my-toolkit-ratings.json")
    if relative.as_posix() == "paper-writing/references/research-basis.md":
        content += (
            "\n## Public distribution\n\nThis export includes citation metadata and original editorial "
            "inspection notes only. Abstracts and article bodies are omitted. Original collection "
            "and inspection flags describe provenance; they do not imply that those source texts "
            "are bundled here. The summary distinguishes original collection counts from zero "
            "public local abstracts and article bodies. Follow source links to inspect originals.\n"
        )
    return content


def clean_inspection(value):
    if isinstance(value, dict):
        return {key: clean_inspection(item) for key, item in value.items()
                if not key.endswith("_local_path") and key not in {"abstract", "introduction_extracted", "full_text"}}
    if isinstance(value, list):
        return [clean_inspection(item) for item in value]
    return value


def public_independent_test(content):
    # The original snapshot assertion reads a private toolkit self-assessment.
    # Keep its useful catalog/limitation coverage using explicit invented ratings.
    replacement = '''    def test_toolkit_limitation_anchor_with_synthetic_arithmetic(self):
        rubric = load("paper-writing/assets/toolkit-rubric.json")
        _, data = manuscript()
        data.update(rubric_id=rubric["rubric_id"], profile="toolkit")
        data["criteria"] = [{"id": c["id"], "status": "assessed", "rating": 4,
                             "confidence": "high", "rationale": "Synthetic arithmetic fixture.",
                             "evidence": [{"locator": "fixture", "observation": "Invented ratings; not a toolkit evaluation."}]}
                            for c in rubric["criteria"]]
        row(data, "real-manuscript-calibration")["rating"] = 1
        out = scorer.score(data, rubric)
        self.assertLess(out["score_out_of_100"], 100)
        self.assertEqual(out["assessment_coverage_percent"], 100)
        self.assertEqual(row(out, "real-manuscript-calibration")["rating"], 1)
        self.assertIn("not scientific certification", scorer.render_markdown(out, rubric))

'''
    return re.sub(
        r"(?ms)^    def test_current_toolkit_rating_and_limitation_anchor_are_consistent\(self\):.*?(?=^    def |\Z)",
        replacement, content, count=1,
    )


def selected_sources(source):
    skill = source / "paper-writing"
    if not (skill / "SKILL.md").is_file():
        raise ValueError("--source must be an output root containing paper-writing/SKILL.md")
    files = []
    for path in sorted(skill.rglob("*"), key=lambda item: item.relative_to(source).as_posix()):
        relative = path.relative_to(source)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink is not eligible: {relative.as_posix()}")
        if path.is_file():
            if path.suffix.lower() not in TEXT_SUFFIXES or path.name.startswith("."):
                raise ValueError(f"Unexpected skill asset requires review: {relative.as_posix()}")
            files.append(path)
    for name in ("manuscript.md", "project.json", "evaluation-v1-legacy.json"):
        path = source / "examples" / name
        if path.is_file():
            files.append(path)
    for path in sorted((source / "validation").glob("test*.py")):
        # Newly added aggressive-policy tests are synthetic and stdlib only.
        if path.name in TESTS or "aggressive" in path.name:
            files.append(path)
    for stem in ("cv-inspection", "ml-inspection", "medical-inspection"):
        for suffix in (".md", ".json"):
            path = source / "research" / "historical-2022" / (stem + suffix)
            if path.is_file():
                files.append(path)
    return files


def export_metadata(source, build):
    original = source / "research" / "historical-2022"
    rows = [json.loads(line) for line in (original / "papers.jsonl").read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    ids = [row["id"] for row in rows]
    if len(rows) != 300 or len(set(ids)) != 300:
        raise ValueError("Historical registry must contain exactly 300 unique source IDs")
    public = []
    for row in rows:
        item = {key: value for key, value in row.items() if key in METADATA_KEYS}
        item.update({
            "export_level": "citation_metadata_only",
            "original_collection_level": row.get("original_collection_level", row.get("collection_level")),
            "original_full_text_status": row.get("original_full_text_status", row.get("full_text_status")),
            "public_local_abstract_available": False,
            "public_local_body_available": False,
        })
        public.append(item)
    public.sort(key=lambda row: row["id"])
    output = build / "research" / "historical-2022"
    registry = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in public)
    write_text(output / "papers.jsonl", registry)
    summary = load_json(original / "summary.json")
    public_summary = {
        "version": 1, "distribution": "citation_metadata_only", "cutoff_year": 2022,
        "total_records": len(public), "source_of_truth": "papers.jsonl",
        "counts": dict(sorted(Counter(row["venue"] for row in public).items())),
        "years": dict(sorted(Counter(str(row["year"]) for row in public).items())),
        "original_collection_abstract_records": summary.get("original_collection_abstract_records", summary.get("abstract_records", 300)),
        "original_available_bodies": summary.get("original_available_bodies", summary.get("fulltext_downloaded", 238)),
        "public_local_abstract_records": 0, "public_local_article_bodies": 0,
        "abstract_records": 0, "fulltext_downloaded": 0,
        "corpus_sha256": hashlib.sha256(registry.encode("utf-8")).hexdigest(),
        "original_corpus_sha256": summary.get("original_corpus_sha256", summary.get("corpus_sha256")),
        "specialist_papers_inspected_at_abstract_or_selected_section_level": summary.get("specialist_papers_inspected_at_abstract_or_selected_section_level", 18),
        "complete_paper_scientific_reviews_claimed": 0,
        "limits": [
            "Metadata and original editorial observations only; no abstracts, PDF, XML or extracted article bodies are distributed.",
            "Original collection and inspection flags describe the source collection, not public local availability.",
            "A convenience collection does not establish research quality, source truth or acceptance probability.",
            "Follow original source URLs and applicable permissions to inspect article text.",
        ],
    }
    write_text(output / "summary.json", json_text(public_summary))


def readme(build):
    policy = build / "paper-writing" / "assets" / "scoring-policies.json"
    policy_note = (
        "The scorer also includes an explicit aggressive scoring policy in "
        "`paper-writing/assets/scoring-policies.json`; consult `score_evaluation.py --help` "
        "and the scorecard for selection and interpretation. The aggressive policy changes "
        "scoring expectations, not the scientific evidence available.\n\n"
        if policy.is_file() else ""
    )
    return (
        "# Paper writing toolkit\n\n"
        "A portable scientific writing skill, mechanical manuscript audit, independent reviewer "
        "packet workflow, and evidence-backed editorial scoring tools. The audit and scorer "
        "use Python's standard library; they do not call an AI service.\n\n"
        "Start with [the skill](paper-writing/SKILL.md), [harness commands](paper-writing/references/harness-guide.md), "
        "and [the scorecard](paper-writing/references/evaluation-scorecard.md). Run commands below "
        "from this toolkit directory.\n\n"
        "```sh\npython paper-writing/scripts/paper_harness.py --help\n"
        "python paper-writing/scripts/paper_harness.py audit examples/manuscript.md --context examples/project.json --out audit.json\n"
        "python paper-writing/scripts/paper_harness.py plan examples/manuscript.md --context examples/project.json --out review-plan.json\n"
        "python paper-writing/scripts/score_evaluation.py --help\n"
        "python -m unittest discover -s validation -p 'test*.py' -v\n```\n\n"
        "The examples contain explicitly invented data for software validation. Generated review "
        "packets are tasks, not completed reviews. Audit passes, declared evidence, and editorial "
        "scores do not verify scientific truth or predict acceptance.\n\n"
        "The manuscript rubric defines 24 anchored criteria across five domains, with empirical ML, "
        "theory, clinical, and systematic-review contribution profiles. Choose the relevant profile, "
        "supply inspected evidence and rationale, and report coverage and blockers alongside scores.\n\n"
        + policy_note +
        "## Historical citations and access\n\n"
        "`research/historical-2022/papers.jsonl` contains 300 stable citation IDs with authors, "
        "venues, source links and bounded inspection provenance. This is a metadata-only export: "
        "zero local abstracts and zero article bodies. The original collection recorded 300 abstracts "
        "and 238 available bodies; those original counts are explicitly distinguished in `summary.json`. "
        "The accompanying specialist notes are original editorial observations, not complete article reviews. "
        "No journal full articles are mirrored. Use original publisher or repository links to inspect "
        "sources under their applicable access terms.\n\n"
        "Collectors remain available as source code. They require the optional packages in "
        "`paper-writing/scripts/corpus-requirements.txt` and perform network access only when explicitly run. "
        "Collection metadata, downloads and selected-section inspection are separate evidence levels.\n\n"
        "## Reproducing the public export\n\n"
        "```sh\npython publish_toolkit.py --source PATH_TO_OUTPUT_ROOT --dest PATH_TO_NEW_PUBLIC_TOOLKIT\n```\n\n"
        "The exporter uses a narrow allowlist, removes source abstracts and local body paths, converts "
        "known host-specific Markdown paths, rejects unrecognized home paths and common credentials, "
        "and emits a deterministic SHA-256 `public-manifest.json`. It excludes private drafts, "
        "research sessions, assessments, raw logs, archives and downloaded bodies. Re-running may "
        "replace only a destination previously marked by this exporter.\n"
    )


def scan(build):
    errors = []
    for path in sorted(build.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(build)
        if any(part in SKIP_PARTS or part.startswith(".env") or part.lower() in
               {"tokens", "tokens.json", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}
               for part in relative.parts):
            errors.append(f"sensitive or generated path: {relative.as_posix()}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            errors.append(f"unexpected binary or file type: {relative.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8-sig")
        if PRIVATE_PATH.search(text):
            errors.append(f"unrecognized private host path: {relative.as_posix()}")
        if SECRET.search(text):
            errors.append(f"possible credential: {relative.as_posix()}")
    if errors:
        raise ValueError("Public export scan failed:\n" + "\n".join(errors))


def build_export(source, build):
    for path in selected_sources(source):
        if path.is_symlink():
            raise ValueError("Symlink is not eligible for public export")
        relative = path.relative_to(source)
        content = path.read_text(encoding="utf-8-sig")
        if path.suffix == ".md":
            content = portable_markdown(content, source, relative)
        elif relative.parts[:2] == ("research", "historical-2022") and path.suffix == ".json":
            content = json_text(clean_inspection(json.loads(content)))
        elif relative.as_posix() == "validation/test_scoring_v2_independent.py":
            content = public_independent_test(content)
        write_text(build / relative, content)
    export_metadata(source, build)
    write_text(build / "README.md", readme(build))
    write_text(build / "publish_toolkit.py", Path(__file__).read_text(encoding="utf-8-sig"))
    scan(build)
    files = []
    for path in sorted(build.rglob("*"), key=lambda item: item.relative_to(build).as_posix()):
        if path.is_file():
            data = path.read_bytes()
            files.append({"path": path.relative_to(build).as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {
        "created_by": EXPORTER, "schema_version": 1,
        "distribution": "metadata_only_public_toolkit",
        "test_adjustments": ["Private toolkit score snapshot assertion replaced by an explicit synthetic arithmetic fixture; original source test is unchanged."],
        "file_count_excluding_manifest": len(files), "bytes_excluding_manifest": sum(row["bytes"] for row in files),
        "safety_scan": "passed", "files": files,
    }
    write_text(build / MANIFEST, json_text(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Output root containing paper-writing, examples, validation and research")
    parser.add_argument("--dest", required=True, type=Path, help="New public toolkit directory, or a previous export destination")
    args = parser.parse_args()
    if args.dest.is_symlink():
        parser.error("Destination must not be a symlink")
    source, dest = args.source.resolve(), args.dest.resolve()
    if source == dest or source in dest.parents and "paper-writing" in dest.relative_to(source).parts:
        parser.error("Destination must not replace the source or be inside the source skill")
    if dest in source.parents or dest == Path(dest.anchor):
        parser.error("Destination must not be an ancestor of the source or a filesystem root")
    if dest.exists():
        if dest.is_symlink() or not (dest / MANIFEST).is_file() or load_json(dest / MANIFEST).get("created_by") != EXPORTER:
            parser.error("Refusing to replace an existing directory without this exporter's manifest")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="public-toolkit-build-", dir=dest.parent) as temp:
            build = Path(temp) / "toolkit"
            build.mkdir()
            manifest = build_export(source, build)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(build), str(dest))
        print(json.dumps({"status": "exported", "files": manifest["file_count_excluding_manifest"] + 1,
                          "bytes": manifest["bytes_excluding_manifest"] + (dest / MANIFEST).stat().st_size,
                          "safety_scan": "passed"}, sort_keys=True))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
