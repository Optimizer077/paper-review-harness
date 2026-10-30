#!/usr/bin/env python3
"""Compute evidence-backed editorial scores; scores are not submission approval.

Version 1 keeps its original inline-weight interface. Version 2 uses a separate,
validated rubric and keeps completion, confidence, and critical blockers separate
from numeric ratings. This module uses only the Python standard library.
"""
import argparse
import copy
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path
import re


def _score_v1(data):
    rows = data.get("criteria") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("criteria must be a nonempty list")
    seen, total, assessed, earned = set(), 0.0, 0.0, 0.0
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
            raise ValueError("criteria need unique nonempty string IDs")
        seen.add(row["id"])
        weight, rating = row.get("weight"), row.get("rating")
        if type(weight) not in (int, float) or not math.isfinite(weight) or weight <= 0:
            raise ValueError("weights must be finite and positive")
        total += weight
        if rating is not None:
            if type(rating) not in (int, float) or not math.isfinite(rating) or not 0 <= rating <= 4:
                raise ValueError("ratings must be 0..4 or null")
            evidence = row.get("evidence")
            if not isinstance(evidence, list) or not evidence or not all(isinstance(x, str) and x.strip() for x in evidence):
                raise ValueError("each assessed rating needs nonempty evidence strings")
            assessed += weight
            earned += weight * rating / 4
    if not math.isclose(total, 100.0, abs_tol=1e-8):
        raise ValueError("weights must sum to 100")
    result = dict(data)
    result.update(score_out_of_100=round(earned, 2) if math.isclose(assessed, 100) else None,
                  earned_subtotal=round(earned, 2), assessed_weight_percent=round(assessed, 2),
                  status="complete" if math.isclose(assessed, 100) else "provisional",
                  readiness="blocked" if data.get("critical_blockers") else ("reviewed" if math.isclose(assessed, 100) else "incomplete"),
                  interpretation="Editorial rating of inspected scope; not acceptance probability or scientific certification. Critical blockers remain separate.")
    return result


MANUSCRIPT_DOMAINS = {
    "argument": ("research-question", "motivation-gap", "contribution-calibration", "literature-positioning"),
    "evidence": ("method-specification", "design-validity", "comparison-fairness", "analysis-uncertainty", "robustness-failures", "claim-evidence-entailment"),
    "consistency": ("concept-definitions", "notation-units", "numbers-denominators", "cross-section-alignment"),
    "communication": ("title-abstract", "introduction-logic", "paragraph-sentence-logic", "jargon-acronyms", "reader-teachback", "figures-tables"),
    "transparency": ("reproducibility-artifacts", "limitations-transfer", "ethics-disclosures", "venue-compliance"),
}
MANUSCRIPT_CORE = {
    "research-question", "design-validity", "claim-evidence-entailment",
    "concept-definitions", "numbers-denominators", "cross-section-alignment",
}
EMPIRICAL_WEIGHTS = dict(zip(
    [cid for ids in MANUSCRIPT_DOMAINS.values() for cid in ids],
    [5, 5, 5, 5, 7, 7, 6, 6, 4, 5, 5, 5, 5, 5, 3, 3, 2, 2, 3, 2, 3, 3, 2, 2],
))
LIMITATIONS = [
    "Editorial assessment of the inspected revision and evidence; not scientific certification, an acceptance probability, or submission approval.",
    "Evidence records identify observations and locations; their presence does not verify that an observation is true or sufficient.",
    "Confidence is reported separately and never multiplies a rating. Missing-assessment bounds are possible score bounds, not statistical confidence intervals.",
    "A numeric score does not resolve a critical blocker. Reviewed is not submission approval; it means the assessment requirements were met.",
]
COMPUTED_FIELDS = {
    "rubric_sha256", "rubric_title", "profile_title", "score_out_of_100", "earned_subtotal",
    "nominal_weight", "applicable_weight", "assessed_weight", "excluded_weight",
    "assessed_weight_percent", "assessment_coverage_percent", "missing_assessment_bounds",
    "status", "readiness", "domain_scores", "active_blockers", "core_deficits",
    "low_confidence_core_checks", "revision_priorities", "limitations", "interpretation", "comparison",
    "scoring_policy_id", "scoring_policy_sha256", "effective_score_out_of_100",
    "score_cap_out_of_100", "score_caps", "strict_gate_failures",
}


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _identifier(value, label):
    _text(value, label)
    if value != value.strip() or any(ch.isspace() for ch in value):
        raise ValueError(f"{label} must not contain whitespace")
    return value


def _object(value, label, required, optional=()):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    missing = set(required) - value.keys()
    extra = value.keys() - (set(required) | set(optional))
    if missing or extra:
        raise ValueError(f"{label}: missing fields {sorted(missing)}; unexpected fields {sorted(extra)}")
    return value


def _finite_number(value, label, minimum=0):
    if type(value) not in (int, float):
        raise ValueError(f"{label} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite or value < minimum:
        raise ValueError(f"{label} must be finite and at least {minimum}")
    return value


def _json_values(value, label="document"):
    """Reject non-JSON Python values and nonfinite numbers, even in metadata."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        _finite_number(value, label, minimum=-math.inf)
        return
    if isinstance(value, list):
        for item in value:
            _json_values(item, label)
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for item in value.values():
            _json_values(item, label)
        return
    raise ValueError(f"{label} must contain only JSON-compatible values and string object keys")


def _string_list(value, label, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(f"{label} must be {'a nonempty' if nonempty else 'a'} list")
    for item in value:
        _text(item, label)
    return value


def _hash(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")
    return value


def _date(value):
    _text(value, "evaluated_at")
    # Accept a calendar date or an ISO datetime; reject permissive compact dates.
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?", value):
        raise ValueError("evaluated_at must be an ISO date or datetime")
    try:
        if "T" in value:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("evaluated_at must be a valid ISO date or datetime") from exc


def rubric_fingerprint(rubric):
    """Hash the complete catalog, weights, guidance, and anchors deterministically."""
    _json_values(rubric, "rubric")
    payload = json.dumps(rubric, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_rubric(rubric):
    _json_values(rubric, "rubric")
    _object(rubric, "rubric", {
        "version", "rubric_id", "max_rating", "default_profile", "core_threshold",
        "domains", "criteria", "profiles",
    })
    if type(rubric["version"]) is not int or rubric["version"] != 2:
        raise ValueError("rubric version must be 2")
    if type(rubric["max_rating"]) is not int or rubric["max_rating"] != 4:
        raise ValueError("rubric max_rating must be 4")
    if type(rubric["core_threshold"]) is not int or rubric["core_threshold"] != 2:
        raise ValueError("rubric core_threshold must be 2")
    _identifier(rubric["rubric_id"], "rubric_id")
    _identifier(rubric["default_profile"], "default_profile")
    domains = rubric["domains"]
    if not isinstance(domains, list) or not domains:
        raise ValueError("rubric domains must be a nonempty list")
    domain_ids = set()
    for domain in domains:
        _object(domain, "domain", {"id", "title"})
        did = _identifier(domain["id"], "domain.id")
        _text(domain["title"], "domain.title")
        if did in domain_ids:
            raise ValueError("rubric domain IDs must be unique")
        domain_ids.add(did)
    criteria = rubric["criteria"]
    if not isinstance(criteria, list) or not criteria:
        raise ValueError("rubric criteria must be a nonempty list")
    catalog = {}
    for criterion in criteria:
        _object(criterion, "rubric criterion", {
            "id", "title", "domain", "description", "core", "allow_not_applicable",
            "anchors", "checks", "role_ids",
        })
        cid = _identifier(criterion["id"], "criterion.id")
        if cid in catalog:
            raise ValueError(f"duplicate rubric criterion: {cid}")
        for key in ("title", "description"):
            _text(criterion[key], f"{cid}.{key}")
        _identifier(criterion["domain"], f"{cid}.domain")
        if criterion["domain"] not in domain_ids:
            raise ValueError(f"{cid} belongs to an unknown domain")
        for key in ("core", "allow_not_applicable"):
            if type(criterion[key]) is not bool:
                raise ValueError(f"{cid}.{key} must be a boolean")
        if criterion["core"] and criterion["allow_not_applicable"]:
            raise ValueError(f"core criterion {cid} cannot allow N/A")
        anchors = _object(criterion["anchors"], f"{cid}.anchors", {str(n) for n in range(5)})
        for level, anchor in anchors.items():
            _text(anchor, f"{cid}.anchors.{level}")
        if len({text.strip() for text in anchors.values()}) != 5:
            raise ValueError(f"{cid} needs distinct anchors for all five rating levels")
        _string_list(criterion["checks"], f"{cid}.checks", nonempty=True)
        _string_list(criterion["role_ids"], f"{cid}.role_ids")
        catalog[cid] = criterion
    if {c["domain"] for c in criteria} != domain_ids:
        raise ValueError("every rubric domain must contain criteria")
    profiles = rubric["profiles"]
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("rubric profiles must be a nonempty object")
    if rubric["default_profile"] not in profiles:
        raise ValueError("default_profile must name a rubric profile")
    for name, profile in profiles.items():
        _identifier(name, "profile name")
        _object(profile, f"profile {name}", {"title", "weights", "guidance"})
        _text(profile["title"], f"profile {name}.title")
        weights = _object(profile["weights"], f"profile {name}.weights", set(catalog))
        for cid, weight in weights.items():
            _finite_number(weight, f"{name}.{cid}.weight")
        if not math.isclose(sum(weights.values()), 100, rel_tol=0, abs_tol=1e-8):
            raise ValueError(f"profile {name} weights must sum to 100")
        guidance = profile["guidance"]
        if not isinstance(guidance, dict) or not guidance or guidance.keys() - catalog.keys():
            raise ValueError(f"profile {name}.guidance must contain known criterion overrides")
        for cid, instruction in guidance.items():
            _text(instruction, f"{name}.{cid}.guidance")
    if rubric["rubric_id"] == "paper-writing-v2":
        expected = {cid: did for did, ids in MANUSCRIPT_DOMAINS.items() for cid in ids}
        if set(catalog) != set(expected) or domain_ids != set(MANUSCRIPT_DOMAINS):
            raise ValueError("paper-writing-v2 requires the canonical 24-criterion, five-domain catalog")
        for cid, criterion in catalog.items():
            if criterion["domain"] != expected[cid]:
                raise ValueError(f"{cid} must belong to {expected[cid]}")
            if cid in MANUSCRIPT_CORE and not criterion["core"]:
                raise ValueError(f"{cid} must be core")
            if criterion["allow_not_applicable"] != (cid == "figures-tables"):
                raise ValueError("only figures-tables initially permits N/A and must retain that documented option")
        if not {"empirical-ml", "theory", "clinical", "systematic-review"}.issubset(profiles):
            raise ValueError("paper-writing-v2 requires all four contribution profiles")
        if profiles["empirical-ml"]["weights"] != EMPIRICAL_WEIGHTS:
            raise ValueError("empirical-ml must use the canonical criterion weights")
    return catalog


def _evidence(value, label, required, source_ids=True):
    if not isinstance(value, list) or (required and not value):
        raise ValueError(f"{label} must be {'a nonempty' if required else 'a'} evidence list")
    for record in value:
        _object(record, label, {"locator", "observation"}, {"source_id"} if source_ids else ())
        _text(record["locator"], f"{label}.locator")
        _text(record["observation"], f"{label}.observation")
        if "source_id" in record:
            _identifier(record["source_id"], f"{label}.source_id")


def _validate_evaluation(data, rubric, catalog, fingerprint):
    _json_values(data, "evaluation")
    _object(data, "evaluation", {
        "version", "rubric_id", "profile", "subject", "reviewer", "evaluated_at", "criteria", "critical_blockers",
    }, COMPUTED_FIELDS | {"strictness"})
    if type(data["version"]) is not int or data["version"] != 2:
        raise ValueError("evaluation version must be 2")
    if data["rubric_id"] != rubric["rubric_id"]:
        raise ValueError("evaluation rubric_id does not match the supplied rubric")
    if "rubric_sha256" in data and _hash(data["rubric_sha256"], "rubric_sha256") != fingerprint:
        raise ValueError("evaluation rubric_sha256 does not match the current rubric")
    _identifier(data["profile"], "profile")
    if data["profile"] not in rubric["profiles"]:
        raise ValueError("evaluation profile must name a rubric profile")
    subject = _object(data["subject"], "subject", {"id", "revision"}, {"artifact_sha256"})
    _identifier(subject["id"], "subject.id")
    _text(subject["revision"], "subject.revision")
    if "artifact_sha256" in subject:
        _hash(subject["artifact_sha256"], "subject.artifact_sha256")
    reviewer = _object(data["reviewer"], "reviewer", {"id", "type"})
    _identifier(reviewer["id"], "reviewer.id")
    if reviewer["type"] not in ("agent", "human"):
        raise ValueError("reviewer.type must be agent or human")
    _date(data["evaluated_at"])
    rows = data["criteria"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("criteria must be a nonempty list")
    indexed = {}
    for row in rows:
        _object(row, "rating criterion", {"id", "status", "rating", "confidence", "evidence", "rationale"}, {"action", "applicability_reason"})
        cid = _identifier(row["id"], "rating criterion.id")
        if cid not in catalog or cid in indexed:
            raise ValueError(f"unknown or duplicate criterion: {cid}")
        _text(row["rationale"], f"{cid}.rationale")
        if "action" in row:
            _text(row["action"], f"{cid}.action")
        status = row["status"]
        if status not in ("assessed", "unassessed", "not_applicable"):
            raise ValueError(f"{cid}.status must be assessed, unassessed, or not_applicable")
        if status == "assessed":
            if type(row["rating"]) is not int or not 0 <= row["rating"] <= 4:
                raise ValueError(f"{cid}.rating must be an integer from 0 to 4")
            if row["confidence"] not in ("low", "medium", "high"):
                raise ValueError(f"{cid}.confidence must be low, medium, or high")
        elif row["rating"] is not None or row["confidence"] is not None:
            raise ValueError(f"{cid}: unassessed and N/A criteria require null rating and confidence")
        if status == "not_applicable":
            if catalog[cid]["core"] or not catalog[cid]["allow_not_applicable"]:
                raise ValueError(f"{cid} does not permit N/A")
            _text(row.get("applicability_reason"), f"{cid}.applicability_reason")
        elif "applicability_reason" in row:
            raise ValueError(f"{cid}.applicability_reason is only valid for N/A")
        _evidence(row["evidence"], f"{cid}.evidence", required=status != "unassessed")
        indexed[cid] = row
    if set(indexed) != set(catalog):
        raise ValueError(f"ratings must include every rubric criterion; missing {sorted(catalog.keys() - indexed.keys())}")
    if all(row["status"] == "not_applicable" for row in rows):
        raise ValueError("all criteria cannot be N/A")
    blockers = data["critical_blockers"]
    if not isinstance(blockers, list):
        raise ValueError("critical_blockers must be a list")
    blocker_ids = set()
    for blocker in blockers:
        _object(blocker, "critical blocker", {"id", "criterion_id", "description", "status", "evidence"}, {"resolution"})
        bid = _identifier(blocker["id"], "blocker.id")
        if bid in blocker_ids:
            raise ValueError("blocker IDs must be unique")
        blocker_ids.add(bid)
        _identifier(blocker["criterion_id"], "blocker.criterion_id")
        if blocker["criterion_id"] not in catalog:
            raise ValueError("blocker must reference a rubric criterion")
        _text(blocker["description"], "blocker.description")
        if blocker["status"] not in ("open", "resolved"):
            raise ValueError("blocker.status must be open or resolved")
        _evidence(blocker["evidence"], f"blocker {bid}.evidence", required=True, source_ids=False)
        if blocker["status"] == "resolved" or "resolution" in blocker:
            _text(blocker.get("resolution"), "blocker.resolution")
    return indexed


def _metrics(ids, rows, weights):
    nominal = math.fsum(weights[cid] for cid in ids)
    excluded = math.fsum(weights[cid] for cid in ids if rows[cid]["status"] == "not_applicable")
    applicable = math.fsum(weights[cid] for cid in ids if rows[cid]["status"] != "not_applicable")
    assessed = math.fsum(weights[cid] for cid in ids if rows[cid]["status"] == "assessed")
    earned = math.fsum(weights[cid] * rows[cid]["rating"] / 4 for cid in ids if rows[cid]["status"] == "assessed")
    complete = all(rows[cid]["status"] != "unassessed" for cid in ids)
    return {
        "nominal_weight": nominal, "applicable_weight": applicable,
        "assessed_weight": assessed, "excluded_weight": excluded,
        "earned_subtotal": earned,
        "score_out_of_100": round(100 * earned / applicable, 2) if complete and applicable > 0 else None,
        "assessment_coverage_percent": round(100 * assessed / applicable, 2) if applicable > 0 else None,
        "status": "complete" if complete else "provisional",
        "missing_assessment_bounds": {
            "lower": round(100 * earned / applicable, 2) if applicable > 0 else None,
            "upper": round(100 * (earned + applicable - assessed) / applicable, 2) if applicable > 0 else None,
        },
    }


def _priorities(data, rows, core_deficits, low_confidence):
    priorities = []
    for blocker in data["critical_blockers"]:
        if blocker["status"] == "open":
            priorities.append({
                "kind": "critical_blocker", "criterion_id": blocker["criterion_id"],
                "blocker_id": blocker["id"], "reason": blocker["description"],
                "action": f"Resolve and document the blocker: {blocker['description']}",
                "evidence": copy.deepcopy(blocker["evidence"]),
            })
    for cid, row in rows.items():
        if row["status"] == "unassessed":
            priorities.append({
                "kind": "missing_assessment", "criterion_id": cid,
                "reason": "Unassessed; quality is unknown, not an established failure.",
                "action": row.get("action", "Inspect the relevant manuscript and source evidence, then record a rating, confidence, and evidence locations."),
                "evidence": copy.deepcopy(row["evidence"]),
            })
    for kind, findings in (("core_deficit", core_deficits), ("low_confidence_core", low_confidence)):
        for finding in findings:
            cid = finding["criterion_id"]
            row = rows[cid]
            priorities.append({
                "kind": kind, "criterion_id": cid, "rating": row["rating"],
                "reason": row["rationale"],
                "action": row.get("action", "Address the recorded core deficit and reassess against its rubric anchors." if kind == "core_deficit" else "Inspect additional source evidence to resolve low confidence in this core assessment."),
                "evidence": copy.deepcopy(row["evidence"]),
            })
    deficit_ids = {finding["criterion_id"] for finding in core_deficits}
    for cid, row in sorted(rows.items(), key=lambda item: (item[1]["rating"] if item[1]["rating"] is not None else 5, item[0])):
        if row["status"] == "assessed" and row["rating"] < 3 and cid not in deficit_ids:
            priorities.append({
                "kind": "rated_weakness", "criterion_id": cid, "rating": row["rating"],
                "reason": row["rationale"],
                "action": row.get("action", "Address the observed weakness and reassess against the next rubric anchor."),
                "evidence": copy.deepcopy(row["evidence"]),
            })
    return priorities


def scoring_policy(strictness):
    """Load the shared, versioned editorial policy and its canonical fingerprint."""
    if strictness not in ("standard", "aggressive"):
        raise ValueError("strictness must be standard or aggressive")
    document = _read_json(Path(__file__).resolve().parents[1] / "assets/scoring-policies.json")
    if document.get("version") != 1:
        raise ValueError("unsupported scoring policy version")
    policy = document["policies"][strictness]
    return policy, rubric_fingerprint({"version": document["version"], "policy": policy})


def _apply_policy(result, catalog, rows, policy, strictness):
    caps, failures = [], []

    def cap(rule, reason, evidence, **identity):
        caps.append(dict(rule=rule, cap=policy["caps"][rule], reason=reason,
                         evidence=copy.deepcopy(evidence), **identity))

    for cid, criterion in catalog.items():
        row = rows[cid]
        if row["status"] != "assessed":
            continue
        if criterion["core"] and row["rating"] < policy["core_min_rating"]:
            failures.append(dict(kind="core_below_target", criterion_id=cid,
                                 reason=f"Core rating {row['rating']}/4 is below {policy['core_min_rating']}/4.",
                                 evidence=copy.deepcopy(row["evidence"])))
        if criterion["core"] and (row["confidence"] == "low" or
                                    (policy["require_high_confidence_core"] and row["confidence"] != "high")):
            failures.append(dict(kind="core_confidence", criterion_id=cid,
                                 reason=f"Core confidence is {row['confidence']}; additional evidence is required.",
                                 evidence=copy.deepcopy(row["evidence"])))
        if strictness != "aggressive":
            continue
        if row["rating"] <= 1:
            rule = "core_severe" if criterion["core"] else "criterion_severe"
            cap(rule, f"{'Core' if criterion['core'] else 'Applicable'} criterion rated {row['rating']}/4.",
                row["evidence"], criterion_id=cid)
            failures.append(dict(kind="criterion_severe", criterion_id=cid,
                                 reason="Applicable criterion is rated 0 or 1.", evidence=copy.deepcopy(row["evidence"])))
        elif criterion["core"] and row["rating"] == 2:
            cap("core_below_target", "Core criterion is partially adequate at 2/4; aggressive target is 3/4.",
                row["evidence"], criterion_id=cid)
        if criterion["core"] and row["confidence"] != "high":
            cap("core_confidence_" + row["confidence"],
                f"Core assessment has {row['confidence']} confidence; confidence does not alter its raw rating.",
                row["evidence"], criterion_id=cid)
    for domain in result["domain_scores"]:
        displayed = domain["score_out_of_100"]
        # Thresholds use the underlying ratio, not its rounded display: 74.999
        # must not clear 75, and 59.999 must remain below the severe cutoff.
        value = (100 * domain["earned_subtotal"] / domain["applicable_weight"]
                 if displayed is not None else None)
        if value is None or value >= policy["min_domain_score"]:
            continue
        evidence = [dict(criterion_id=cid, **item) for cid, criterion in catalog.items()
                    if criterion["domain"] == domain["id"] for item in rows[cid]["evidence"]]
        reason = (f"Complete domain's unrounded score is below {policy['min_domain_score']}/100; "
                  f"displayed score is {displayed:g}/100.")
        failures.append(dict(kind="domain_below_target", domain_id=domain["id"], reason=reason, evidence=copy.deepcopy(evidence)))
        if strictness == "aggressive":
            cap("domain_severe" if value < 60 else "domain_below_target", reason, evidence, domain_id=domain["id"])
    if strictness == "aggressive":
        for blocker in result["active_blockers"]:
            cap("open_blocker", blocker["description"], blocker["evidence"],
                blocker_id=blocker["id"], criterion_id=blocker["criterion_id"])
    score_cap = min([100] + [item["cap"] for item in caps])
    raw = result["score_out_of_100"]
    result.update(score_caps=caps, strict_gate_failures=failures, score_cap_out_of_100=score_cap,
                  effective_score_out_of_100=min(raw, score_cap) if raw is not None else None)
    if result["readiness"] not in ("blocked", "incomplete") and failures:
        result["readiness"] = "needs_revision_or_evidence"


def score(data, rubric=None, strictness=None):
    """Return a new scored document, preserving the original rating records."""
    mode = strictness if strictness is not None else (data.get("strictness", "standard") if isinstance(data, dict) else "standard")
    if mode not in ("standard", "aggressive"):
        raise ValueError("strictness must be standard or aggressive")
    if rubric is None:
        if isinstance(data, dict) and data.get("version") == 2:
            raise ValueError("version 2 evaluations require a separate rubric")
        if isinstance(data, dict) and "version" in data and (type(data["version"]) is not int or data["version"] != 1):
            raise ValueError("unsupported evaluation version; version 2 requires a separate rubric")
        if mode != "standard":
            raise ValueError("Version 1 supports standard scoring only; use a version 2 rubric for aggressive review.")
        return _score_v1(data)
    catalog = validate_rubric(rubric)
    fingerprint = rubric_fingerprint(rubric)
    rows = _validate_evaluation(data, rubric, catalog, fingerprint)
    policy, policy_hash = scoring_policy(mode)
    if "scoring_policy_sha256" in data and _hash(data["scoring_policy_sha256"], "scoring_policy_sha256") != policy_hash:
        raise ValueError("evaluation scoring_policy_sha256 does not match the selected scoring policy")
    if "scoring_policy_id" in data and data["scoring_policy_id"] != policy["id"]:
        raise ValueError("evaluation scoring_policy_id does not match the selected scoring policy")
    weights = rubric["profiles"][data["profile"]]["weights"]
    metrics = _metrics(list(catalog), rows, weights)
    if metrics["applicable_weight"] <= 0:
        raise ValueError("evaluation needs positive applicable weight")
    active = [copy.deepcopy(blocker) for blocker in data["critical_blockers"] if blocker["status"] == "open"]
    core_deficits, low_confidence = [], []
    for cid, criterion in catalog.items():
        row = rows[cid]
        if criterion["core"] and row["status"] == "assessed":
            finding = {"criterion_id": cid, "rating": row["rating"], "confidence": row["confidence"], "evidence": copy.deepcopy(row["evidence"]), "rationale": row["rationale"]}
            if row["rating"] < rubric["core_threshold"]:
                core_deficits.append(finding)
            if row["confidence"] == "low":
                low_confidence.append(finding)
    if active:
        readiness = "blocked"
    elif metrics["status"] == "provisional":
        readiness = "incomplete"
    elif core_deficits or low_confidence:
        readiness = "needs_revision_or_evidence"
    else:
        readiness = "reviewed"
    result = {key: copy.deepcopy(value) for key, value in data.items() if key not in COMPUTED_FIELDS}
    result.update(metrics)
    result.update(
        rubric_sha256=fingerprint, profile_title=rubric["profiles"][data["profile"]]["title"],
        assessed_weight_percent=metrics["assessed_weight"], readiness=readiness,
        active_blockers=active, core_deficits=core_deficits, low_confidence_core_checks=low_confidence,
        domain_scores=[dict(id=domain["id"], title=domain["title"], **_metrics(
            [cid for cid, criterion in catalog.items() if criterion["domain"] == domain["id"]], rows, weights,
        )) for domain in rubric["domains"]],
        revision_priorities=_priorities(data, rows, core_deficits, low_confidence),
        limitations=list(LIMITATIONS), interpretation=LIMITATIONS[0],
        strictness=mode, scoring_policy_id=policy["id"], scoring_policy_sha256=policy_hash,
    )
    _apply_policy(result, catalog, rows, policy, mode)
    return result


def compare_evaluations(prior, current, rubric):
    """Compare recorded assessments without conflating scores and scientific truth."""
    if not isinstance(prior, dict) or not isinstance(current, dict) or prior.get("version") != 2 or current.get("version") != 2:
        raise ValueError("comparison requires version 2 evaluations")
    if "rubric_sha256" not in prior:
        raise ValueError("comparison requires a prior scored JSON document with rubric_sha256")
    before, after = score(prior, rubric), score(current, rubric)
    if before["strictness"] != after["strictness"] or before["scoring_policy_sha256"] != after["scoring_policy_sha256"]:
        raise ValueError("comparison requires matching strictness modes and scoring policy fingerprints")
    if before["subject"]["id"] != after["subject"]["id"]:
        raise ValueError("comparison requires matching subject.id")
    if before["rubric_sha256"] != after["rubric_sha256"]:
        raise ValueError("comparison requires matching rubric fingerprints")
    if before["profile"] != after["profile"]:
        raise ValueError("comparison requires matching profiles")
    old = {row["id"]: row for row in before["criteria"]}
    new = {row["id"]: row for row in after["criteria"]}
    same_applicability = all((old[cid]["status"] == "not_applicable") == (new[cid]["status"] == "not_applicable") for cid in old)
    reason = None
    if before["status"] != "complete" or after["status"] != "complete":
        reason = "Both assessments must be complete to report a total score delta."
    elif not same_applicability:
        reason = "Applicability patterns differ; total scores use different denominators."
    delta = round(after["score_out_of_100"] - before["score_out_of_100"], 2) if reason is None else None
    return {
        "subject_id": after["subject"]["id"], "prior_revision": before["subject"]["revision"],
        "current_revision": after["subject"]["revision"], "profile": after["profile"],
        "rubric_sha256": after["rubric_sha256"],
        "comparison_kind": "same_revision_assessments" if before["subject"]["revision"] == after["subject"]["revision"] else "different_revisions",
        "prior_reviewer": before["reviewer"], "current_reviewer": after["reviewer"],
        "prior_coverage_percent": before["assessment_coverage_percent"],
        "current_coverage_percent": after["assessment_coverage_percent"],
        "total_score_delta": delta, "total_score_delta_reason": reason,
        "effective_score_delta": round(after["effective_score_out_of_100"] - before["effective_score_out_of_100"], 2) if reason is None else None,
        "effective_score_delta_reason": reason,
        "strictness": after["strictness"], "scoring_policy_sha256": after["scoring_policy_sha256"],
        "applicability_patterns_match": same_applicability,
        "criterion_deltas": [{
            "id": cid, "prior_status": old[cid]["status"], "current_status": new[cid]["status"],
            "prior_rating": old[cid]["rating"], "current_rating": new[cid]["rating"],
            "rating_delta": new[cid]["rating"] - old[cid]["rating"] if old[cid]["status"] == new[cid]["status"] == "assessed" else None,
            "rating_delta_reason": None if old[cid]["status"] == new[cid]["status"] == "assessed" else "Not comparable: both criteria must be assessed; missing and N/A ratings are not zero.",
            "prior_confidence": old[cid]["confidence"], "current_confidence": new[cid]["confidence"],
        } for cid in old],
        "limitations": "Differences describe recorded editorial assessments, including possible rater disagreement; they do not prove improvement in scientific truth. Ratings are not averaged.",
    }


def _md(value):
    # Keep authored evidence legible without allowing it to break report tables.
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")


def _number(value):
    return "not available" if value is None else f"{value:g}"


def render_markdown(result, rubric=None):
    """Render the score, limitations, decisions, and evidence into a review report."""
    if result.get("version") != 2:
        report = (
            "# Editorial assessment (version 1)\n\n"
            f"Score: {_number(result['score_out_of_100'])}/100; status: {result['status']}; readiness: {result['readiness']}.\n\n"
            f"Assessed nominal weight: {_number(result['assessed_weight_percent'])}%.\n\n"
            f"{result['interpretation']}\n"
        )
        if result.get("critical_blockers"):
            report += "\nRecorded critical blockers keep this assessment blocked:\n\n"
            report += "\n".join(f"- {_md(blocker)}" for blocker in result["critical_blockers"]) + "\n"
        return report
    catalog = validate_rubric(rubric) if rubric is not None else {}
    if rubric is not None and result["rubric_sha256"] != rubric_fingerprint(rubric):
        raise ValueError("report rubric fingerprint does not match the assessment")
    bounds = result["missing_assessment_bounds"]
    lines = [
        "# Editorial assessment", "",
        f"Subject: **{_md(result['subject']['id'])}**; revision: **{_md(result['subject']['revision'])}**.", "",
        f"Profile: {_md(result['profile'])}; rubric: {_md(result['rubric_id'])}.", "",
        f"Rubric SHA-256: `{result['rubric_sha256']}`.", "",
        f"Reviewer: {_md(result['reviewer']['id'])} ({result['reviewer']['type']}); evaluated: {_md(result['evaluated_at'])}.", "",
        f"**Score: {_number(result['score_out_of_100'])}/100; coverage: {_number(result['assessment_coverage_percent'])}%; status: {result['status']}; readiness: {result['readiness']}.**", "",
        f"Earned subtotal: {_number(result['earned_subtotal'])}; nominal/applicable/assessed/excluded weights: {_number(result['nominal_weight'])} / {_number(result['applicable_weight'])} / {_number(result['assessed_weight'])} / {_number(result['excluded_weight'])}.", "",
        f"Missing-assessment bounds: {_number(bounds['lower'])}–{_number(bounds['upper'])}/100. These fill missing ratings with 0 or 4; they are not statistical confidence intervals.", "",
        "## Domains", "",
        "| Domain | Score /100 | Coverage % | Nominal | Applicable | Assessed | Excluded |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for domain in result["domain_scores"]:
        lines.append("| " + " | ".join([_md(domain["title"])] + [_number(domain[key]) for key in ("score_out_of_100", "assessment_coverage_percent", "nominal_weight", "applicable_weight", "assessed_weight", "excluded_weight")]) + " |")
    lines += ["", "## Scoring policy", "",
              f"Strictness: **{result.get('strictness', 'standard')}**; policy: `{result.get('scoring_policy_id', 'standard-v1')}`.", "",
              f"Policy SHA-256: `{result.get('scoring_policy_sha256', 'not recorded')}`.", "",
              f"**Effective score: {_number(result.get('effective_score_out_of_100', result['score_out_of_100']))}/100; raw anchored score: {_number(result['score_out_of_100'])}/100.**", "",
              "Effective score is the minimum of the complete raw score and applicable policy caps. Caps are not additive penalties or an acceptance forecast. Incomplete assessments have no effective total or effective bounds.", ""]
    if not result.get("score_caps"):
        lines.append("No policy cap triggered by the recorded assessments.")
    for item in result.get("score_caps", []):
        identity = item.get("blocker_id") or item.get("criterion_id") or item.get("domain_id")
        lines.append(f"- Cap {_number(item['cap'])}/100 — `{item['rule']}` ({_md(identity)}): {_md(item['reason'])}")
        for record in item["evidence"]:
            lines.append(f"  - Evidence at {_md(record['locator'])}: {_md(record['observation'])}")
    for failure in result.get("strict_gate_failures", []):
        lines.append(f"- Readiness gate: {_md(failure.get('criterion_id', failure.get('domain_id')))} — {_md(failure['reason'])}")
    lines += ["", "## Criteria", "", "| Criterion | Status | Rating /4 | Confidence | Rationale / applicability | Evidence locations and observations |", "| --- | --- | ---: | --- | --- | --- |"]
    for row in result["criteria"]:
        label = catalog.get(row["id"], {}).get("title", row["id"])
        rationale = row["rationale"]
        if row["status"] == "not_applicable":
            rationale += " Applicability: " + row["applicability_reason"]
        evidence = "; ".join(f"{item['locator']}: {item['observation']}" for item in row["evidence"]) or "No evidence recorded; unassessed."
        lines.append(f"| {_md(label)} (`{_md(row['id'])}`) | {row['status']} | {_number(row['rating'])} | {row['confidence'] or 'not assessed'} | {_md(rationale)} | {_md(evidence)} |")
    lines += ["", "## Critical blockers", ""]
    if not result["critical_blockers"]:
        lines.append("No critical blockers recorded. This does not verify that none exist.")
    for blocker in result["critical_blockers"]:
        lines += [f"- **{blocker['status']} — {_md(blocker['id'])}** ({_md(blocker['criterion_id'])}): {_md(blocker['description'])}"]
        for item in blocker["evidence"]:
            lines.append(f"  - Evidence at {_md(item['locator'])}: {_md(item['observation'])}")
        if "resolution" in blocker:
            lines.append(f"  - Recorded resolution: {_md(blocker['resolution'])}")
    lines += ["", "## Core checks", ""]
    if not result["core_deficits"] and not result["low_confidence_core_checks"]:
        lines.append("No assessed core deficits or low-confidence core checks recorded. Unassessed criteria remain unknown.")
    for label, key in (("Below core threshold", "core_deficits"), ("Low-confidence core assessment", "low_confidence_core_checks")):
        for finding in result[key]:
            lines.append(f"- {label}: {_md(finding['criterion_id'])}; rating {finding['rating']}/4; confidence {finding['confidence']}.")
    lines += ["", "## Revision priorities", ""]
    if not result["revision_priorities"]:
        lines.append("No priority triggered by the recorded assessment rules. Reviewed is not submission approval.")
    for index, priority in enumerate(result["revision_priorities"], 1):
        lines.append(f"{index}. **{_md(priority['kind'])} — {_md(priority['criterion_id'])}**: {_md(priority['reason'])} Action: {_md(priority['action'])}")
        for item in priority["evidence"]:
            lines.append(f"   - Evidence at {_md(item['locator'])}: {_md(item['observation'])}")
    comparison = result.get("comparison")
    if comparison:
        lines += ["", "## Assessment comparison", "", f"Revisions: {_md(comparison['prior_revision'])} → {_md(comparison['current_revision'])}; {comparison['comparison_kind']}.", "", f"Total score delta: {_number(comparison['total_score_delta'])}. {_md(comparison['total_score_delta_reason'] or 'Both assessments are complete with matching applicability.')}", "", f"Effective score delta: {_number(comparison.get('effective_score_delta'))}. {_md(comparison.get('effective_score_delta_reason') or 'Matching scoring policy and complete, comparable assessments.')}", "", "| Criterion | Prior rating | Current rating | Delta | Prior status | Current status |", "| --- | ---: | ---: | ---: | --- | --- |"]
        for delta in comparison["criterion_deltas"]:
            lines.append(f"| {_md(delta['id'])} | {_number(delta['prior_rating'])} | {_number(delta['current_rating'])} | {_number(delta['rating_delta'])} | {delta['prior_status']} | {delta['current_status']} |")
        lines += ["", comparison["limitations"]]
    lines += ["", "## Limitations", ""] + [f"- {limitation}" for limitation in result["limitations"]]
    return "\n".join(lines) + "\n"


def _read_json(path):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"nonfinite JSON number: {value}")

    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object, parse_constant=reject_constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--rubric", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--compare", type=Path, help="Prior scored version 2 JSON document, including rubric_sha256")
    parser.add_argument("--strictness", choices=("standard", "aggressive"), help="Version 2 scoring policy; defaults to input strictness, then standard")
    args = parser.parse_args()
    try:
        data = _read_json(args.input)
        rubric = _read_json(args.rubric) if args.rubric else None
        result = score(data, rubric, strictness=args.strictness)
        if args.compare:
            if rubric is None:
                raise ValueError("comparison requires a version 2 rubric")
            result["comparison"] = compare_evaluations(_read_json(args.compare), result, rubric)
        report = render_markdown(result, rubric) if args.markdown else None
        output = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(report, encoding="utf-8")
        return 0
    except (ValueError, OSError, TypeError) as exc:
        parser.exit(2, f"Invalid evaluation: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
