#!/usr/bin/env python3
"""Regenerate Task B consensus labels and validation statistics."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODEL_DIR = ROOT / "out_runall_v3"
MODEL_FILES = {
    "qwen": "ackB_qwen.json",
    "deepseek_v3": "ackB_ds.json",
    "deepseek_v4_flash": "ackB_dsv4.json",
    "longcat_2": "ackB_longcat.json",
}


def read_rater(path: Path) -> dict[str, int]:
    with path.open(encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return {row["id"]: int(row["label"]) for row in rows}


def cohen_kappa(left: list[int], right: list[int]) -> float:
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    p_left = sum(left) / len(left)
    p_right = sum(right) / len(right)
    expected = p_left * p_right + (1 - p_left) * (1 - p_right)
    return (observed - expected) / (1 - expected)


def fleiss_kappa(rows: list[list[int]], categories: tuple[int, ...]) -> float:
    n_raters = len(rows[0])
    agreement = sum(
        (sum(sum(value == category for value in row) ** 2 for category in categories) - n_raters)
        / (n_raters * (n_raters - 1))
        for row in rows
    ) / len(rows)
    proportions = [
        sum(value == category for row in rows for value in row) / (len(rows) * n_raters)
        for category in categories
    ]
    expected = sum(value**2 for value in proportions)
    return (agreement - expected) / (1 - expected)


def main() -> None:
    raters = [read_rater(HERE / f"rater_{letter}.csv") for letter in "ABC"]
    models = {
        name: json.loads((MODEL_DIR / filename).read_text(encoding="utf-8"))
        for name, filename in MODEL_FILES.items()
    }
    ids = sorted(raters[0])
    if any(sorted(rater) != ids for rater in raters):
        raise ValueError("Rater files do not contain identical item IDs")

    output_rows = []
    human_majorities: list[int] = []
    model_majorities: list[int] = []
    raw_human_rows: list[list[int]] = []
    for item_id in ids:
        human = [rater[item_id] for rater in raters]
        binary = [value for value in human if value in (0, 1)]
        if len(binary) < 2:
            raise ValueError(f"Insufficient binary human labels for {item_id}")
        human_majority = int(sum(binary) > len(binary) / 2)
        model = [int(models[name][item_id]) for name in MODEL_FILES]
        model_majority = int(sum(model) >= 3)
        raw_human_rows.append(human)
        human_majorities.append(human_majority)
        model_majorities.append(model_majority)
        output_rows.append(
            [item_id, *human, human_majority, *model, model_majority]
        )

    header = [
        "id", "rater_A", "rater_B", "rater_C", "human_majority",
        *MODEL_FILES.keys(), "model_majority",
    ]
    with (HERE / "consensus.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(output_rows)

    agreements = sum(a == b for a, b in zip(human_majorities, model_majorities))
    complete_agreements = sum(len(set(row)) == 1 for row in raw_human_rows)
    summary = {
        "n_unique_sentences": len(ids),
        "human_label_counts": [dict(sorted(Counter(rater.values()).items())) for rater in raters],
        "human_majority_positive_n": sum(human_majorities),
        "human_majority_positive_rate": sum(human_majorities) / len(ids),
        "model_majority_positive_n": sum(model_majorities),
        "model_majority_positive_rate": sum(model_majorities) / len(ids),
        "human_model_agreement_n": agreements,
        "human_model_agreement_rate": agreements / len(ids),
        "human_model_cohen_kappa": cohen_kappa(human_majorities, model_majorities),
        "complete_three_rater_agreement_n": complete_agreements,
        "complete_three_rater_agreement_rate": complete_agreements / len(ids),
        "fleiss_kappa_categories_0_1_9": fleiss_kappa(raw_human_rows, (0, 1, 9)),
    }
    (HERE / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
