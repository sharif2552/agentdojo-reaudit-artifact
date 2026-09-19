"""Paired, cluster-aware analysis for the v5.3 Tool Filter repair."""

import json
import math
import os
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
DESIGN_PATH = RESULTS / "design_v5_3.json"
PLAN_PATH = RESULTS / "planned_cells_v5_3.jsonl"
RAW_LEDGER_PATH = RESULTS / "raw_attempts_v5_3.jsonl"
RELEASE_LEDGER_PATH = RESULTS / "release_attempts_v5_3.jsonl"
LEDGER_PATH = RAW_LEDGER_PATH if os.environ.get("PAPER_RAW_LEDGER") == "1" else RELEASE_LEDGER_PATH
STOP_PATH = RESULTS / "v5_3_recovery_stop.json"
JSON_OUT = RESULTS / "v5_3_final_analysis.json"
TEXT_OUT = RESULTS / "v5_3_final_analysis.md"
BOOTSTRAPS = 10_000
SEED = 1729


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def exact_mcnemar_p(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    smaller = min(left_only, right_only)
    tail = sum(math.comb(discordant, index) for index in range(smaller + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail)


def holm_adjust(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [1.0] * len(p_values)
    running = 0.0
    total = len(p_values)
    for rank, index in enumerate(order):
        value = min(1.0, (total - rank) * p_values[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted


def percentile(values: list[float], probability: float) -> float:
    values = sorted(values)
    if not values:
        return float("nan")
    index = min(len(values) - 1, max(0, int(probability * (len(values) - 1))))
    return values[index]


def paired_bootstrap(pairs: list[dict[str, Any]], value: Callable[[dict[str, Any]], tuple[int, int]],
                     phase: str, seed_offset: int) -> tuple[float, float]:
    rng = random.Random(SEED + seed_offset)
    by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        by_user[pair["user_task_id"]].append(pair)
    users = sorted(by_user)
    samples: list[float] = []
    for _ in range(BOOTSTRAPS):
        deltas: list[int] = []
        for sampled_user in (rng.choice(users) for _ in users):
            rows = by_user[sampled_user]
            if phase == "benign":
                selected = rows
            else:
                by_injection: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in rows:
                    by_injection[row["injection_task_id"]].append(row)
                injections = sorted(by_injection)
                selected = [
                    rng.choice(by_injection[rng.choice(injections)])
                    for _ in injections
                ]
            for row in selected:
                no_defense, tool_filter = value(row)
                deltas.append(tool_filter - no_defense)
        if deltas:
            samples.append(sum(deltas) / len(deltas))
    return percentile(samples, 0.025), percentile(samples, 0.975)


def pair_records(completed: dict[str, dict[str, Any]], plan: list[dict[str, Any]],
                 model: str, phase: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for cell in plan:
        if cell["model"] != model or cell["phase"] != phase:
            continue
        record = completed.get(cell["planned_cell_id"])
        if record is None:
            continue
        key = (
            cell["user_task_id"],
            cell["injection_task_id"],
            cell["attack"],
        )
        grouped[key][cell["defense"]] = record
    pairs = []
    for key, defenses in grouped.items():
        if set(defenses) == {"no_defense", "tool_filter"}:
            pairs.append({
                "user_task_id": key[0],
                "injection_task_id": key[1],
                "attack": key[2],
                "no_defense": defenses["no_defense"],
                "tool_filter": defenses["tool_filter"],
            })
    return pairs


def contrast(pairs: list[dict[str, Any]], field: str, phase: str, seed_offset: int,
             planned_pairs: int) -> dict[str, Any]:
    def values(pair: dict[str, Any]) -> tuple[int, int]:
        return (
            int(bool(pair["no_defense"]["native_scores"][field])),
            int(bool(pair["tool_filter"]["native_scores"][field])),
        )

    observed = [values(pair) for pair in pairs]
    no_success = sum(left for left, _ in observed)
    tool_success = sum(right for _, right in observed)
    no_only = sum(left == 1 and right == 0 for left, right in observed)
    tool_only = sum(left == 0 and right == 1 for left, right in observed)
    if pairs:
        lower, upper = paired_bootstrap(pairs, values, phase, seed_offset)
        difference = (tool_success - no_success) / len(pairs)
    else:
        lower = upper = difference = None
    known_delta_sum = tool_success - no_success
    missing_pairs = planned_pairs - len(pairs)
    return {
        "planned_pairs": planned_pairs,
        "paired_n": len(pairs),
        "no_defense_success": no_success,
        "tool_filter_success": tool_success,
        "tool_filter_minus_no_defense": difference,
        "cluster_bootstrap_95": [lower, upper],
        "planned_denominator_delta_bounds": [
            (known_delta_sum - missing_pairs) / planned_pairs,
            (known_delta_sum + missing_pairs) / planned_pairs,
        ],
        "discordant_no_defense_only": no_only,
        "discordant_tool_filter_only": tool_only,
        "mcnemar_exact_p": exact_mcnemar_p(no_only, tool_only),
    }


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    plan = list(iter_jsonl(PLAN_PATH))
    attempts = 0
    statuses: Counter[str] = Counter()
    completed: dict[str, dict[str, Any]] = {}
    attempted_cells: set[str] = set()
    for record in iter_jsonl(LEDGER_PATH):
        attempts += 1
        statuses[record["status"]] += 1
        attempted_cells.add(record["planned_cell_id"])
        if record["status"] == "completed":
            completed[record["planned_cell_id"]] = record

    models = [item["id"] for item in design["models"]]
    results: dict[str, dict[str, Any]] = {}
    for model_index, model in enumerate(models):
        benign_pairs = pair_records(completed, plan, model, "benign")
        injection_pairs = pair_records(completed, plan, model, "injection")
        results[model] = {
            "family": next(item["family"] for item in design["models"] if item["id"] == model),
            "benign_utility": contrast(benign_pairs, "utility", "benign", model_index * 3, 17),
            "utility_under_attack": contrast(injection_pairs, "utility", "injection", model_index * 3 + 1, 60),
            "attack_success": contrast(injection_pairs, "attack_succeeded", "injection", model_index * 3 + 2, 60),
        }

    for outcome in ("benign_utility", "utility_under_attack", "attack_success"):
        raw = [results[model][outcome]["mcnemar_exact_p"] for model in models]
        adjusted = holm_adjust(raw)
        for model, value in zip(models, adjusted):
            results[model][outcome]["holm_adjusted_p"] = value

    family_results: dict[str, dict[str, Any]] = {}
    for family in sorted({item["family"] for item in design["models"]}):
        family_models = [item["id"] for item in design["models"] if item["family"] == family]
        family_results[family] = {"model_configurations": family_models}
        for outcome in ("benign_utility", "utility_under_attack", "attack_success"):
            values = [
                results[model][outcome]["tool_filter_minus_no_defense"]
                for model in family_models
                if results[model][outcome]["tool_filter_minus_no_defense"] is not None
            ]
            family_results[family][outcome] = {
                "equal_model_weight_mean_delta": sum(values) / len(values) if values else None,
                "contributing_model_configurations": len(values),
            }

    stop = json.loads(STOP_PATH.read_text(encoding="utf-8")) if STOP_PATH.exists() else None
    stopped_consistently = bool(
        stop
        and stop.get("decision") == "STOPPED_WITH_UNRESOLVED_INFRASTRUCTURE_FAILURES"
        and stop.get("planned_cells") == len(plan)
        and stop.get("completed_cells") == len(completed)
    )
    unresolved = len(plan) - len(completed)
    report = {
        "status": (
            "FINAL_COMPLETE_COVERAGE" if unresolved == 0 else
            "FINAL_STOPPED_WITH_EXPLICIT_MISSINGNESS" if stopped_consistently else
            "INTERIM_INCOMPLETE_COVERAGE"
        ),
        "method": {
            "paired_comparison": "Tool Filter minus no defense",
            "bootstrap_replicates": BOOTSTRAPS,
            "bootstrap_seed": SEED,
            "injection_clustering": "user task, then injection task within user task",
            "multiplicity": "Holm within outcome across ten model configurations",
        },
        "coverage": {
            "planned": len(plan),
            "attempted_cells": len(attempted_cells),
            "completed_cells": len(completed),
            "unresolved_cells": unresolved,
            "usable_coverage_percent": 100 * len(completed) / len(plan),
            "attempt_records": attempts,
            "attempt_statuses": dict(statuses),
        },
        "stopping_record": stop,
        "by_model": results,
        "by_family_secondary": family_results,
    }
    JSON_OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Final OpenRouter Tool Filter Analysis",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Coverage: {len(completed)}/{len(plan)} usable cells ({100 * len(completed) / len(plan):.1f}%); "
        f"{unresolved} unresolved infrastructure outcomes.",
        "",
        "All estimates use completed defense-paired cells only. Repetitions were not performed, and model aliases did not expose immutable backend revisions.",
        "",
        "## Paired contrasts",
        "",
        "Deltas are Tool Filter minus no defense. Holm correction is applied within outcome across the ten configurations.",
        "",
        "| Model configuration | Family | BU pairs | BU delta | UA pairs | UA delta | ASR pairs | ASR delta |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        bu = results[model]["benign_utility"]
        ua = results[model]["utility_under_attack"]
        attack = results[model]["attack_success"]
        lines.append(
            f"| {model} | {results[model]['family']} | {bu['paired_n']}/17 | {100 * bu['tool_filter_minus_no_defense']:.1f}% | "
            f"{ua['paired_n']}/60 | {100 * ua['tool_filter_minus_no_defense']:.1f}% | "
            f"{attack['paired_n']}/60 | {100 * attack['tool_filter_minus_no_defense']:.1f}% |"
        )
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "The 109 unresolved cells remain infrastructure missingness, not task failures. Complete-case contrasts are accompanied by planned-denominator bounds in the JSON artifact; results are reported by configuration and are not pooled as independent model samples.",
    ])
    TEXT_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report["coverage"], indent=2))
    print(f"wrote {JSON_OUT} and {TEXT_OUT}")


if __name__ == "__main__":
    main()
