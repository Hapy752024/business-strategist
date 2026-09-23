#!/usr/bin/env python3
"""Collect operator evidence for a business-archetype playbook."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import tempfile
from pathlib import Path

from workspace import create_topic_workspace, slugify, update_stage, resolve_run_dir, cases


ROOT = Path(__file__).resolve().parents[2]


OPERATOR_TERMS = {
    "en": ["founder first customers", "founder pricing", "founder failed acquisition", "operator retention"],
    "de": ["Gründer erste Kunden", "Gründer Preisgestaltung", "Gründer Kundengewinnung gescheitert", "Unternehmer Kundenbindung"],
    "fr": ["fondateur premiers clients", "fondateur tarification", "fondateur échec acquisition clients", "entrepreneur fidélisation clients"],
    "es": ["fundador primeros clientes", "fundador precios", "fundador fracaso captación clientes", "emprendedor retención clientes"],
    "it": ["fondatore primi clienti", "fondatore prezzi", "fondatore acquisizione clienti fallita", "imprenditore fidelizzazione clienti"],
}


def founder_query_plan(args):
    from collect import selected_providers, QUERY_PLAN_PROVIDERS
    language = args.language.split("-")[0].lower()
    terms = [term.strip() for term in args.operator_keywords.split(",") if term.strip()] or OPERATOR_TERMS.get(language, [])
    if not terms:
        raise ValueError("No operator vocabulary for this language; supply --operator-keywords or --query-plan")
    if language != "en" and not args.topic_keywords:
        raise ValueError("Supply source-language --topic-keywords or an exact --query-plan for non-English operator research")
    if args.geo.upper() == "AUTO" or args.language.upper() == "AUTO":
        raise ValueError("Operator query planning requires explicit --geo and --language")
    providers = selected_providers(args.providers)
    if set(providers) - QUERY_PLAN_PROVIDERS:
        raise ValueError("Operator plans require searchable providers; choose explicit --providers supported by --query-plan")
    seed = args.topic_keywords or args.archetype
    return {"schema_version": 1, "revision": "operator-initial", "queries": [
        {"query_id": f"{provider}-{index}", "candidate_id": f"operator-{index}",
         "query": f"{seed} {term}", "provider": provider, "locale": f"{args.geo.upper()}:{args.language.lower()}",
         "intent": "operator_lesson", "source_family": "operator_accounts", "seed_origin": "generated"}
        for provider in providers for index, term in enumerate(terms)]}


def collector_command(args, evidence_dir):
    from research_queries import query_arguments
    return [sys.executable, str(ROOT / "scripts/evidence_scout/collect.py"),
        "--topic", args.topic, "--customer-segment", args.customer_segment,
        "--research-mode", "discovery",
        "--hypothesis-id", "OP1", "--days", str(args.days), "--limit", str(args.limit),
        "--providers", args.providers, "--geo", args.geo, "--language", args.language,
        "--out-dir", str(evidence_dir)] + query_arguments(args)


def parse_args():
    parser = argparse.ArgumentParser(description="Research validation, launch, first-customer, and scaling playbooks from founder/operator sources.")
    from research_queries import add_query_arguments
    add_query_arguments(parser)
    parser.add_argument("--operator-keywords", default="", help="Comma-separated source-language operator situations; used instead of the built-in vocabulary.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--archetype", required=True, help="For example B2B SaaS, marketplace, local service, or regulated insurance broker.")
    parser.add_argument("--customer-segment", default="")
    parser.add_argument("--stage", default="idea", choices=["idea", "interviews", "prototype", "mvp", "pilots", "revenue", "scale"])
    parser.add_argument("--geo", default="AUTO")
    parser.add_argument("--language", default="AUTO")
    parser.add_argument("--days", type=int, default=3650)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--providers", default="serper_search,youtube,hn")
    parser.add_argument("--workspace", default="")
    parser.add_argument("--case", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated = None
    try:
        if not args.query_plan:
            generated = founder_query_plan(args)
        # Validate and preview the actual collector command before workspace mutation.
        with tempfile.TemporaryDirectory(prefix="operator-query-preview-") as directory:
            preview_args = argparse.Namespace(**vars(args))
            if generated:
                path = Path(directory) / "queries.json"
                path.write_text(json.dumps(generated, ensure_ascii=False), encoding="utf-8")
                preview_args.query_plan = str(path)
            preview_args.query_preview = True
            preview = subprocess.run(collector_command(preview_args, Path(directory) / "evidence"), cwd=ROOT, text=True, capture_output=True, check=False)
            if args.query_preview or preview.returncode:
                print(preview.stdout, end="")
                print(preview.stderr, end="", file=sys.stderr)
                return preview.returncode
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    candidate = Path(args.workspace) if args.workspace else ROOT / 'projects' / slugify(args.topic)
    if args.case and ((candidate / cases.PROJECT).exists() or (candidate / 'market_research/manifest.json').exists()):
        cases.read_project(candidate)
    workspace = create_topic_workspace(args.topic, args.workspace, args.customer_segment)
    modern = cases.locate(workspace)
    if modern:
        run_dir, workspace = resolve_run_dir(topic=args.topic, workspace_arg=str(workspace), case_id=args.case,
            out_dir='', legacy_output=False, workspace_subdir='market_research/operator_playbooks/runs')
    else:
        if args.case:
            raise ValueError('Explicit migration required for case mode')
        import uuid
        run_dir = workspace / 'strategy/playbooks/runs' / (slugify(args.archetype) + '-' + uuid.uuid4().hex)
    evidence_dir = run_dir / 'evidence'
    run_dir.mkdir(parents=True, exist_ok=True)
    if generated:
        query_path = run_dir / "operator-query-plan.json"
        query_path.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.query_plan = str(query_path)
    plan = f"""# Founder / Operator Playbook Research Plan

- Topic: {args.topic}
- Archetype: {args.archetype}
- Customer segment: {args.customer_segment or '[UNRESOLVED]'}
- Company stage: {args.stage}
- Geography / language: {args.geo} / {args.language}

## Questions

1. How did comparable operators choose their first segment?
2. What did they do before building, and what evidence changed their plan?
3. How did they acquire the first ten paying customers with limited spend?
4. Which offers, prices, partnerships, and channels worked or failed?
5. What retention, economics, compliance, and hiring gates preceded scaling?

## Interpretation rules

- Founder anecdotes are operator evidence, not proof of customer demand.
- Preserve failures, context, dates, and selection bias.
- Triangulate material tactics before recommending transfer.
"""
    (run_dir / "research_plan.md").write_text(plan, encoding="utf-8")
    update_stage(workspace, "operator_playbook", run_dir=run_dir, status="in_progress", gate_result="not_run", artifacts=[run_dir / "research_plan.md"], next_action="Collect and synthesize comparable operator evidence.")

    command = collector_command(args, evidence_dir)
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    result = {
        "topic": args.topic,
        "archetype": args.archetype,
        "workspace": str(workspace),
        "run_dir": str(run_dir),
        "evidence_dir": str(evidence_dir),
        "collector_exit_code": completed.returncode,
        "next_artifact": str(run_dir / "playbook.md"),
    }
    (run_dir / "run_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gate = "pass" if completed.returncode == 0 else "fail"
    update_stage(
        workspace,
        "operator_playbook", run_dir=run_dir,
        status="passed" if completed.returncode == 0 else "failed",
        gate_result=gate,
        artifacts=[run_dir / "research_plan.md", run_dir / "run_summary.json", evidence_dir / "report.md", evidence_dir / "evidence.jsonl"],
        open_gaps=[] if completed.returncode == 0 else ["Collector returned no strong/relevant operator evidence; inspect provider alerts and broaden sources."],
        next_action="Synthesize sourced operator patterns into the archetype playbook without treating anecdotes as demand proof.",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
