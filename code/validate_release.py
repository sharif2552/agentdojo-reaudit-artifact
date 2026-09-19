#!/usr/bin/env python3
"""Validate the compact public research release."""

import json
import math
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path: Path):
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_plan(path: Path, expected: int) -> set[str]:
    ids = [row["planned_cell_id"] for row in jsonl(path)]
    require(len(ids) == expected, f"{path.name}: expected {expected}, found {len(ids)}")
    require(len(set(ids)) == len(ids), f"{path.name}: duplicate planned_cell_id")
    return set(ids)


def validate_ledger(
    path: Path,
    plan_ids: set[str],
    expected_rows: int,
    expected_completed: int,
    expected_ambiguous: int,
) -> None:
    completed: Counter[str] = Counter()
    row_count = 0
    for row in jsonl(path):
        row_count += 1
        require(row["planned_cell_id"] in plan_ids, f"{path.name}: out-of-plan record")
        require("provider" not in row, f"{path.name}: raw provider payload leaked")
        if row["status"] == "completed":
            completed[row["planned_cell_id"]] += 1
    require(row_count == expected_rows, f"{path.name}: attempt-count drift")
    require(len(completed) == expected_completed, f"{path.name}: completed-cell drift")
    require(
        sum(count > 1 for count in completed.values()) == expected_ambiguous,
        f"{path.name}: ambiguity drift",
    )


def validate_release_integrity() -> None:
    secret_patterns = (
        re.compile(r"\bgsk_[A-Za-z0-9]{20,}"),
        re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_]{20,}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    )
    binary_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".gif"}
    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() in binary_suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in secret_patterns):
            findings.append(str(path.relative_to(ROOT)))
    require(not findings, f"possible secret material found in: {findings}")


def validate_manuscript_claims(groq: dict, router: dict) -> None:
    audit = load_json(RESULTS / "workspace_injection_vector_audit.json")
    require(len(audit["vectors"]) == 16, "source-audit vector-count drift")
    require(
        sum(vector["collision"] == "near_miss" for vector in audit["vectors"]) == 2,
        "source-audit near-miss count drift",
    )
    require(
        all(vector["collision"] != "yes" for vector in audit["vectors"]),
        "source audit now contains an active collision",
    )

    expected_benign_deltas = {
        "openai/gpt-oss-120b": -0.8461538461538461,
        "openai/gpt-oss-20b": -0.5714285714285714,
    }
    for model, expected in expected_benign_deltas.items():
        observed = groq["paired_contrasts"][model]["benign"]["tool_filter"]["utility"][
            "comparison_minus_no_defense"
        ]
        require(math.isclose(observed, expected), f"{model}: benign utility claim drift")
        attacks = groq["strata"][model]["tool_filter"]["injection"]["attack_success"]
        require(attacks == 0, f"{model}: Tool Filter attack-success count is no longer zero")

    by_model = router["by_model"]
    require(len(by_model) == 10, "OpenRouter configuration-count drift")
    require(len({entry["family"] for entry in by_model.values()}) == 5, "OpenRouter family-count drift")
    require(
        all(entry["benign_utility"]["tool_filter_minus_no_defense"] < 0 for entry in by_model.values()),
        "Tool Filter no longer reduces benign utility in every OpenRouter configuration",
    )
    supported_attack_reductions = [
        model
        for model, entry in by_model.items()
        if entry["attack_success"]["tool_filter_minus_no_defense"] < 0
        and entry["attack_success"]["holm_adjusted_p"] < 0.05
    ]
    require(len(supported_attack_reductions) == 3, "supported attack-reduction count drift")
    unchanged_attack_with_large_utility_loss = [
        model
        for model, entry in by_model.items()
        if entry["attack_success"]["tool_filter_minus_no_defense"] == 0
        and entry["benign_utility"]["tool_filter_minus_no_defense"] <= -0.5
    ]
    require(
        len(unchanged_attack_with_large_utility_loss) == 2,
        "zero-ASR-change configuration count drift",
    )


def main() -> None:
    validate_release_integrity()
    groq = load_json(RESULTS / "v5_1_balanced_final_analysis.json")
    router = load_json(RESULTS / "v5_3_final_analysis.json")

    require(groq["status"] == "FINAL_STOPPED_WITH_EXPLICIT_MISSINGNESS", "Groq result is not frozen-final")
    require(router["status"] == "FINAL_STOPPED_WITH_EXPLICIT_MISSINGNESS", "OpenRouter result is not frozen-final")
    require(
        groq["coverage"]["planned"] == 1096
        and groq["coverage"]["usable"] == 879
        and groq["coverage"]["unresolved"] == 215
        and groq["coverage"]["ambiguous_excluded"] == 2,
        "Groq headline coverage drift",
    )
    require(
        router["coverage"]["planned"] == 1540
        and router["coverage"]["completed_cells"] == 1431
        and router["coverage"]["unresolved_cells"] == 109,
        "OpenRouter headline coverage drift",
    )
    validate_manuscript_claims(groq, router)

    groq_ids = validate_plan(RESULTS / "planned_cells_v5_1_balanced.jsonl", 1096)
    router_ids = validate_plan(RESULTS / "planned_cells_v5_3.jsonl", 1540)
    validate_ledger(RESULTS / "release_attempts_v5_1.jsonl", groq_ids, 4344, 881, 2)
    validate_ledger(RESULTS / "release_attempts_v5_3.jsonl", router_ids, 4689, 1431, 0)
    print("Release validation: PASS")


if __name__ == "__main__":
    main()
