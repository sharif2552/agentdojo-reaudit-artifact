#!/usr/bin/env python3
"""Final complete-case and missingness analysis for the frozen Groq panel."""

import json
import math
import os
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PLAN = RESULTS / "planned_cells_v5_1_balanced.jsonl"
RAW_LEDGER = RESULTS / "raw_attempts_v5_1.jsonl"
RELEASE_LEDGER = RESULTS / "release_attempts_v5_1.jsonl"
LEDGER = RELEASE_LEDGER if os.environ.get("PAPER_RELEASE_LEDGER") == "1" else RAW_LEDGER
OUTPUT_JSON = RESULTS / "v5_1_balanced_final_analysis.json"
OUTPUT_MD = RESULTS / "v5_1_balanced_final_analysis.md"
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
DEFENSES = ["no_defense", "repeat_user_prompt", "spotlighting_with_delimiting", "tool_filter"]
BOOTSTRAPS = 10_000
SEED = 1729


def rows(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if not total:
        return [math.nan, math.nan]
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [center - radius, center + radius]


def exact_mcnemar(left_only: int, right_only: int) -> float:
    n = left_only + right_only
    if not n:
        return 1.0
    k = min(left_only, right_only)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


def holm(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [1.0] * len(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        result[index] = running
    return result


def percentile(values: list[float], p: float) -> float:
    values.sort()
    return values[min(len(values) - 1, max(0, int(p * (len(values) - 1))))]


def cluster_bootstrap_delta(pairs: list[dict], field: str, phase: str, seed_offset: int) -> list[float]:
    by_user = defaultdict(list)
    for pair in pairs:
        by_user[pair["user_task_id"]].append(pair)
    users = sorted(by_user)
    rng = random.Random(SEED + seed_offset)
    estimates = []
    for _ in range(BOOTSTRAPS):
        deltas = []
        for user in rng.choices(users, k=len(users)):
            candidates = by_user[user]
            if phase == "benign":
                selected = candidates
            else:
                by_injection = defaultdict(list)
                for pair in candidates:
                    by_injection[pair["injection_task_id"]].append(pair)
                injections = sorted(by_injection)
                selected = [rng.choice(by_injection[rng.choice(injections)]) for _ in injections]
            for pair in selected:
                left = int(bool(pair["no_defense"]["native_scores"].get(field)))
                right = int(bool(pair["comparison"]["native_scores"].get(field)))
                deltas.append(right - left)
        estimates.append(sum(deltas) / len(deltas))
    return [percentile(estimates, 0.025), percentile(estimates, 0.975)]


def main() -> int:
    plan = list(rows(PLAN))
    plan_by_id = {row["planned_cell_id"]: row for row in plan}
    completed = defaultdict(list)
    latest = {}
    attempts = 0
    attempt_statuses = Counter()
    for record in rows(LEDGER):
        cell_id = record["planned_cell_id"]
        if cell_id not in plan_by_id:
            continue
        attempts += 1
        attempt_statuses[record["status"]] += 1
        if cell_id not in latest or record["attempt"] >= latest[cell_id]["attempt"]:
            latest[cell_id] = record
        if record["status"] == "completed":
            completed[cell_id].append(record)
    usable = {cell_id: values[0] for cell_id, values in completed.items() if len(values) == 1}
    ambiguous = {cell_id: values for cell_id, values in completed.items() if len(values) > 1}

    strata = {}
    for model in MODELS:
        strata[model] = {}
        for defense in DEFENSES:
            strata[model][defense] = {}
            for phase in ("benign", "injection"):
                planned = [row for row in plan if row["model"] == model and row["defense"] == defense and row["phase"] == phase]
                records = [usable[row["planned_cell_id"]] for row in planned if row["planned_cell_id"] in usable]
                utility = sum(bool(record["native_scores"]["utility"]) for record in records)
                entry = {
                    "planned": len(planned),
                    "usable": len(records),
                    "missing_or_ambiguous": len(planned) - len(records),
                    "utility_success": utility,
                    "utility_rate": utility / len(records) if records else None,
                    "utility_wilson_95": wilson(utility, len(records)),
                    "utility_planned_denominator_bounds": [utility / len(planned), (utility + len(planned) - len(records)) / len(planned)],
                }
                if phase == "injection":
                    attacks = sum(bool(record["native_scores"].get("attack_succeeded")) for record in records)
                    entry.update({
                        "attack_success": attacks,
                        "attack_success_rate": attacks / len(records) if records else None,
                        "attack_success_wilson_95": wilson(attacks, len(records)),
                        "attack_success_planned_denominator_bounds": [attacks / len(planned), (attacks + len(planned) - len(records)) / len(planned)],
                    })
                strata[model][defense][phase] = entry

    contrasts = {}
    seed_offset = 0
    for model in MODELS:
        contrasts[model] = {}
        for phase in ("benign", "injection"):
            contrasts[model][phase] = {}
            for defense in DEFENSES[1:]:
                grouped = defaultdict(dict)
                for cell in plan:
                    if cell["model"] != model or cell["phase"] != phase or cell["defense"] not in {"no_defense", defense}:
                        continue
                    record = usable.get(cell["planned_cell_id"])
                    if record is None:
                        continue
                    key = (cell["user_task_id"], cell.get("injection_task_id"), cell.get("attack"))
                    grouped[key][cell["defense"]] = record
                pairs = [
                    {
                        "user_task_id": key[0], "injection_task_id": key[1], "attack": key[2],
                        "no_defense": values["no_defense"], "comparison": values[defense],
                    }
                    for key, values in grouped.items() if set(values) == {"no_defense", defense}
                ]
                outcomes = ["utility"] + (["attack_succeeded"] if phase == "injection" else [])
                result = {"planned_pairs": 17 if phase == "benign" else 120, "complete_pairs": len(pairs)}
                for field in outcomes:
                    observed = [
                        (int(bool(pair["no_defense"]["native_scores"].get(field))), int(bool(pair["comparison"]["native_scores"].get(field))))
                        for pair in pairs
                    ]
                    left = sum(item[0] for item in observed)
                    right = sum(item[1] for item in observed)
                    left_only = sum(item == (1, 0) for item in observed)
                    right_only = sum(item == (0, 1) for item in observed)
                    result[field] = {
                        "no_defense_success": left,
                        "comparison_success": right,
                        "comparison_minus_no_defense": (right - left) / len(pairs) if pairs else None,
                        "task_cluster_bootstrap_95": cluster_bootstrap_delta(pairs, field, phase, seed_offset) if pairs else [None, None],
                        "no_defense_only": left_only,
                        "comparison_only": right_only,
                        "mcnemar_exact_p": exact_mcnemar(left_only, right_only),
                    }
                    seed_offset += 1
                contrasts[model][phase][defense] = result
            for field in (["utility"] + (["attack_succeeded"] if phase == "injection" else [])):
                raw = [contrasts[model][phase][defense][field]["mcnemar_exact_p"] for defense in DEFENSES[1:]]
                for defense, adjusted in zip(DEFENSES[1:], holm(raw)):
                    contrasts[model][phase][defense][field]["holm_adjusted_p"] = adjusted

    missing_latest = Counter()
    missing_by_model = Counter()
    for cell in plan:
        cell_id = cell["planned_cell_id"]
        if cell_id in usable:
            continue
        status = "ambiguous_completion" if cell_id in ambiguous else latest.get(cell_id, {}).get("status", "not_attempted")
        missing_latest[status] += 1
        missing_by_model[(cell["model"], status)] += 1

    report = {
        "status": "FINAL_STOPPED_WITH_EXPLICIT_MISSINGNESS",
        "coverage": {
            "planned": len(plan), "usable": len(usable), "ambiguous_excluded": len(ambiguous),
            "unresolved": len(plan) - len(usable) - len(ambiguous), "attempt_records_in_panel": attempts,
            "attempt_statuses": dict(attempt_statuses), "latest_missing_statuses": dict(missing_latest),
        },
        "strata": strata,
        "paired_contrasts": contrasts,
        "missing_by_model_and_status": [
            {"model": model, "status": status, "n": count}
            for (model, status), count in sorted(missing_by_model.items())
        ],
        "rules": {
            "scientific_unit": "planned cell, not attempt",
            "complete_case": "exactly one validator-accepted completion",
            "operational_failures_are_model_failures": False,
            "bootstrap_replicates": BOOTSTRAPS,
            "seed": SEED,
        },
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Final Groq Balanced-Panel Analysis", "", f"Status: **{report['status']}**", "",
        f"Coverage: {len(usable)}/{len(plan)} usable cells ({len(usable)/len(plan):.1%}); {len(ambiguous)} ambiguous cells excluded; {len(plan)-len(usable)-len(ambiguous)} unresolved.", "",
        "## Native outcomes", "",
        "| Model | Defense | BU | UA | ASR | Coverage |", "|---|---|---:|---:|---:|---:|",
    ]
    for model in MODELS:
        for defense in DEFENSES:
            b, i = strata[model][defense]["benign"], strata[model][defense]["injection"]
            lines.append(
                f"| {model} | {defense} | {b['utility_success']}/{b['usable']} ({b['utility_rate']:.1%}) | "
                f"{i['utility_success']}/{i['usable']} ({i['utility_rate']:.1%}) | "
                f"{i['attack_success']}/{i['usable']} ({i['attack_success_rate']:.1%}) | {b['usable']+i['usable']}/{b['planned']+i['planned']} |"
            )
    lines.extend(["", "## Paired contrasts", "", "All deltas are comparison defense minus no defense on complete matched pairs.", ""])
    for model in MODELS:
        lines.append(f"### {model}")
        lines.append("")
        lines.append("| Phase | Defense | Complete pairs | Utility delta | Utility Holm p | ASR delta | ASR Holm p |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for phase in ("benign", "injection"):
            for defense in DEFENSES[1:]:
                item = contrasts[model][phase][defense]
                util = item["utility"]
                attack = item.get("attack_succeeded")
                lines.append(
                    f"| {phase} | {defense} | {item['complete_pairs']}/{item['planned_pairs']} | "
                    f"{util['comparison_minus_no_defense']:.1%} | {util['holm_adjusted_p']:.4g} | "
                    f"{attack['comparison_minus_no_defense']:.1%} | {attack['holm_adjusted_p']:.4g} |" if attack else
                    f"| {phase} | {defense} | {item['complete_pairs']}/{item['planned_pairs']} | "
                    f"{util['comparison_minus_no_defense']:.1%} | {util['holm_adjusted_p']:.4g} | N/A | N/A |"
                )
        lines.append("")
    lines.extend([
        "## Interpretation boundary", "",
        "Operational and provider failures are missing outcomes, not model task failures. Complete-case estimates must be read with the planned-denominator bounds in the JSON artifact.",
    ])
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report["coverage"], indent=2))
    print(f"wrote {OUTPUT_JSON} and {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
