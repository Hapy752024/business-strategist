#!/usr/bin/env python3
"""Validate eval structure and report coverage.

Does NOT execute evals against an LLM — that requires manual review or an
LLM-backed harness. This script checks:
  - Every eval file is valid JSON with correct schema
  - All required fields are present per eval case
  - must_mention / must_not_mention are arrays of strings
  - Which skills have evals and which are missing
  - Routing evals have expected_skill and forbidden_skills
  - No duplicate eval IDs across the dataset

Usage: python3 scripts/run_evals.py [--verbose]
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / ".agents" / "skills"
ROUTING_EVALS_PATH = ROOT / "config" / "routing-evals.json"

REQUIRED_EVAL_FIELDS = {"id", "prompt", "expected_output", "files"}
OPTIONAL_EVAL_FIELDS = {"must_mention", "must_not_mention", "required_artifacts", "expected_skill", "forbidden_skills"}


def red(s):
    return f"\033[31m{s}\033[0m"


def green(s):
    return f"\033[32m{s}\033[0m"


def yellow(s):
    return f"\033[33m{s}\033[0m"


def validate_eval_case(case, skill_name, case_path):
    """Validate a single eval case. Returns list of error strings."""
    errors = []

    if not isinstance(case, dict):
        errors.append(f"{case_path}: eval case is not a dict")
        return errors

    # Required fields
    for field in REQUIRED_EVAL_FIELDS:
        if field not in case:
            errors.append(f"{case_path}: missing required field '{field}'")

    # Type checks
    if "id" in case and not isinstance(case["id"], (int, str)):
        errors.append(f"{case_path}: 'id' must be int or str")
    if "prompt" in case and not isinstance(case["prompt"], str):
        errors.append(f"{case_path}: 'prompt' must be a string")
    if "expected_output" in case and not isinstance(case["expected_output"], str):
        errors.append(f"{case_path}: 'expected_output' must be a string")
    if "files" in case and not isinstance(case["files"], list):
        errors.append(f"{case_path}: 'files' must be a list")

    # Optional field type checks
    for field in ["must_mention", "must_not_mention", "required_artifacts"]:
        if field in case and not isinstance(case[field], list):
            errors.append(f"{case_path}: '{field}' must be a list")
        if field in case and case[field]:
            for item in case[field]:
                if not isinstance(item, str):
                    errors.append(f"{case_path}: all items in '{field}' must be strings")
                    break

    # Routing fields
    if "expected_skill" in case and not isinstance(case["expected_skill"], str):
        errors.append(f"{case_path}: 'expected_skill' must be a string")
    if "forbidden_skills" in case:
        if not isinstance(case["forbidden_skills"], list):
            errors.append(f"{case_path}: 'forbidden_skills' must be a list")
        else:
            for item in case["forbidden_skills"]:
                if not isinstance(item, str):
                    errors.append(f"{case_path}: all items in 'forbidden_skills' must be strings")
                    break

    return errors


def check_evals_file(evals_path):
    """Validate one evals.json file. Returns (skill_name, errors, case_count)."""
    try:
        with open(evals_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return (evals_path.parent.parent.name, [f"Invalid JSON: {e}"], 0)
    except Exception as e:
        return (evals_path.parent.parent.name, [f"Cannot read: {e}"], 0)

    errors = []

    if not isinstance(data, dict):
        return (evals_path.parent.parent.name, ["Root is not a dict"], 0)

    if "skill_name" not in data:
        errors.append("Missing 'skill_name' field")
    if "evals" not in data:
        errors.append("Missing 'evals' array")
        return (data.get("skill_name", "unknown"), errors, 0)

    evals_list = data["evals"]
    if not isinstance(evals_list, list):
        errors.append("'evals' is not an array")
        return (data.get("skill_name", "unknown"), errors, 0)

    seen_ids = set()
    for i, case in enumerate(evals_list):
        case_path = f"{data.get('skill_name', 'unknown')}[{i}]"
        case_errors = validate_eval_case(case, data.get("skill_name", "unknown"), case_path)
        errors.extend(case_errors)

        if isinstance(case, dict) and "id" in case:
            if case["id"] in seen_ids:
                errors.append(f"{case_path}: duplicate eval id '{case['id']}'")
            seen_ids.add(case["id"])

    return (data.get("skill_name", "unknown"), errors, len(evals_list))


def check_routing_evals():
    """Validate the routing evals dataset. Returns errors list."""
    if not ROUTING_EVALS_PATH.exists():
        return [f"Routing evals file not found: {ROUTING_EVALS_PATH}"]

    try:
        with open(ROUTING_EVALS_PATH) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Routing evals: Invalid JSON: {e}"]
    except Exception as e:
        return [f"Routing evals: Cannot read: {e}"]

    errors = []

    if not isinstance(data, dict):
        return ["Routing evals: Root is not a dict"]

    if "pairs" not in data:
        return ["Routing evals: Missing 'pairs' array"]

    pairs = data["pairs"]
    if not isinstance(pairs, list):
        return ["Routing evals: 'pairs' is not an array"]

    total_routing_cases = 0
    for pi, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            errors.append(f"Routing pair[{pi}]: not a dict")
            continue
        if "pair" not in pair:
            errors.append(f"Routing pair[{pi}]: missing 'pair' name")
        evals_list = pair.get("evals", [])
        if not isinstance(evals_list, list):
            errors.append(f"Routing pair[{pi}]: 'evals' is not an array")
            continue

        for ei, case in enumerate(evals_list):
            total_routing_cases += 1
            case_path = f"routing:{pair.get('pair', '?')}[{ei}]"
            case_errors = validate_eval_case(case, "routing", case_path)
            errors.extend(case_errors)

            if isinstance(case, dict):
                if "expected_skill" not in case:
                    errors.append(f"{case_path}: routing eval missing 'expected_skill'")
                if "forbidden_skills" not in case:
                    errors.append(f"{case_path}: routing eval missing 'forbidden_skills'")

    return errors


def main():
    verbose = "--verbose" in sys.argv

    errors_total = 0
    skills_with_evals = []
    skills_without_evals = []
    total_cases = 0

    # Discover all skills
    all_skills = set()
    if SKILLS_DIR.exists():
        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                all_skills.add(skill_dir.name)

    # Check each skill's evals
    print("=== Skill Eval Coverage ===\n")
    for skill_name in sorted(all_skills):
        evals_path = SKILLS_DIR / skill_name / "evals" / "evals.json"
        if evals_path.exists():
            name, errors, count = check_evals_file(evals_path)
            total_cases += count
            if errors:
                print(red(f"  FAIL  {skill_name} — {count} cases, {len(errors)} error(s)"))
                for err in errors:
                    print(red(f"        {err}"))
                errors_total += len(errors)
            else:
                print(green(f"  PASS  {skill_name} — {count} cases"))
                skills_with_evals.append(skill_name)
        else:
            print(yellow(f"  WARN  {skill_name} — no evals.json"))
            skills_without_evals.append(skill_name)

    # Check routing evals
    print(f"\n=== Routing Evals ===\n")
    routing_errors = check_routing_evals()
    if routing_errors:
        for err in routing_errors:
            print(red(f"  FAIL  {err}"))
        errors_total += len(routing_errors)
    else:
        # Count routing cases
        with open(ROUTING_EVALS_PATH) as f:
            routing_data = json.load(f)
        routing_cases = sum(len(pair.get("evals", [])) for pair in routing_data.get("pairs", []))
        print(green(f"  PASS  routing-evals.json — {routing_cases} cases across {len(routing_data.get('pairs', []))} collision pairs"))

    # Summary
    print(f"\n=== Summary ===\n")
    print(f"  Skills with evals:    {len(skills_with_evals)}/{len(all_skills)}")
    if skills_without_evals:
        print(yellow(f"  Skills missing evals: {', '.join(sorted(skills_without_evals))}"))
    print(f"  Total eval cases:     {total_cases}")
    print(f"  Structural errors:    {errors_total}")

    if errors_total > 0:
        print(red(f"\n{errors_total} structural error(s) — fix before proceeding."))
        sys.exit(1)
    else:
        print(green("\nAll eval structure checks passed."))
        if skills_without_evals:
            print(yellow("Some skills are missing evals — this is acceptable but should be addressed."))
            sys.exit(0)
        sys.exit(0)


if __name__ == "__main__":
    main()
