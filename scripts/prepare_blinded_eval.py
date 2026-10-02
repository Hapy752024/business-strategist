#!/usr/bin/env python3
"""Create separated blinded A/B output files for an independent human reviewer."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def read_trials(root: Path) -> dict[tuple[str, int], tuple[dict, str]]:
    results = {}
    for metadata in root.glob("*-r*/trial.json"):
        row = json.loads(metadata.read_text(encoding="utf-8"))
        key = (row["task_id"], row["repeat"])
        if key in results: raise ValueError(f"duplicate task/repeat: {key}")
        answer_path = metadata.parent / "answer.txt"
        answer = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else (metadata.parent / "stdout.txt").read_text(encoding="utf-8")
        if row.get("status") != "ok": answer = f"[INVOCATION FAILED: {row.get('error')}]\n{answer}"
        results[key] = row, answer
    return results


def prepare(baseline: Path, current: Path, out: Path, *, seed: int, split: str = "all", rubric: Path | None = None) -> dict:
    a, b = read_trials(baseline), read_trials(current)
    if set(a) != set(b): raise ValueError("baseline and current trial task/repetition sets must match")
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    review = out / "review"
    coordinator = out / "coordinator"
    review.mkdir(parents=True, exist_ok=False)
    coordinator.mkdir(parents=True, exist_ok=False)
    (review / "task-inputs").mkdir()
    (review / "outputs").mkdir()
    key = {"schema_version":1, "seed":seed, "mapping":{}}
    ratings = {"reviewer_id": None, "ratings": []}
    skipped = 0
    for task_repeat in sorted(a):
        baseline_row, baseline_answer = a[task_repeat]
        current_row, current_answer = b[task_repeat]
        if baseline_row.get("arm") != "baseline" or current_row.get("arm") != "current":
            raise ValueError(f"arm labels do not match input directories for {task_repeat}")
        if split != "all" and (baseline_row.get("split") != split or current_row.get("split") != split):
            skipped += 1; continue
        baseline_input = (Path(baseline_row["workspace"]) / "input.json").read_bytes()
        current_input = (Path(current_row["workspace"]) / "input.json").read_bytes()
        if baseline_input != current_input:
            raise ValueError(f"paired task input changed between arms: {task_repeat}")
        mapping = {"A":"baseline", "B":"current"} if rng.randrange(2) else {"A":"current", "B":"baseline"}
        task_id, repeat = task_repeat
        stub = f"{task_id}-r{repeat}"
        (review / "task-inputs" / f"{stub}.json").write_bytes(baseline_input)
        for blind, arm in mapping.items():
            answer = baseline_answer if arm == "baseline" else current_answer
            (review / "outputs" / f"{stub}-{blind}.txt").write_text(answer, encoding="utf-8")
            ratings["ratings"].append({"task_id":task_id, "repeat":repeat, "variant":blind, "critical_failure":None,
                "ratings":{dimension:None for dimension in ("source_fidelity", "consequential_episode_coverage", "explanatory_usefulness", "segment_boundaries", "execution_completeness", "conversion_truth", "uncertainty_and_limits")},
                "rationale":""})
        key["mapping"][stub] = mapping
    if rubric:
        (review / "review-key.json").write_bytes(rubric.read_bytes())
    (review / "ratings-template.json").write_text(json.dumps(ratings, indent=2) + "\n", encoding="utf-8")
    (review / "review-guide.md").write_text(
        "# Blind output review\n\n"
        "Read each task input beside its A/B outputs. Rate each output independently in `ratings-template.json`; each record identifies task, repetition and A/B variant. "
        "Set `reviewer_id` in your own copy. Use scores 1-4 from `review-key.json`; use `N/A` only when a dimension does not apply to that task and explain why. "
        "In each rationale, cite the output passage and relevant supplied source/input. Set `critical_failure` to null when none is present, or name the rubric failure and evidence. "
        "Do not open coordinator keys.\n\n"
        "## Human calibration protocol\n\n"
        "Two human reviewers independently rate the same development examples before discussing them. Start with `research-contrary-r1` and `research-segmentation-r1`; compare dimension scores, critical failures and evidence-based rationales. "
        "Resolve rubric interpretation differences and record any rubric change before scoring remaining outputs. Then each reviewer independently rates the remaining development outputs. "
        "Only after development ratings and rubric are locked should reviewers rate held-out outputs. Keep repetitions separate.\n\n"
        "The current development split contains research tasks; execution and website dimensions are not calibrated by these examples. The held-out split contains marketing and website tasks. "
        "The reviewer must mark only task-relevant dimensions. The task inputs contain reviewed excerpts or synthetic briefs; excerpts are not full source documents. Do not infer statistical significance from the small task set.\n", encoding="utf-8")
    (coordinator / "blind-key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    return {"paired_trials":len(key["mapping"]), "skipped_other_split":skipped, "review_directory":str(review), "key_directory":str(coordinator),
            "limitation":"The coordinator key must remain separate from the blind review materials. Random labeling does not guarantee reviewers cannot infer the arm."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--split", choices=("development", "held_out", "all"), default="all")
    parser.add_argument("--rubric", type=Path, default=Path(__file__).resolve().parents[1] / "evals/workflow-quality/review-key.json")
    args = parser.parse_args()
    try: result = prepare(args.baseline, args.current, args.out, seed=args.seed, split=args.split, rubric=args.rubric)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc: parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
