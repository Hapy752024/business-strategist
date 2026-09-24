"""Shared CLI forwarding for research wrappers; the collector validates execution."""
from __future__ import annotations


def add_query_arguments(parser):
    parser.add_argument("--topic-keywords", default="", help="Short source-language category phrase, separate from the research brief.")
    parser.add_argument("--segment-keywords", default="", help="Source-language audience anchors.")
    parser.add_argument("--query-plan", default="", help="Exact provider/locale queries, review notes and optional refinement lineage.")
    parser.add_argument("--query-limit", type=int, default=12)
    parser.add_argument("--results-per-query", type=int, default=5)
    parser.add_argument("--max-http-requests", type=int, default=500)
    parser.add_argument("--query-preview", action="store_true", help="Print the collector schedule without credentials, network or workspace writes.")


def query_arguments(args):
    command = []
    for name in ("topic_keywords", "segment_keywords", "query_plan", "query_limit", "results_per_query", "max_http_requests"):
        value = getattr(args, name, None)
        if value is not None and value != "":
            command.extend(["--" + name.replace("_", "-"), str(value)])
    if getattr(args, "query_preview", False):
        command.append("--query-preview")
    return command
