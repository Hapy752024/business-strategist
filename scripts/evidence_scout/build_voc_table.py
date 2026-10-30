#!/usr/bin/env python3
"""Cross-source frequency table over reviewed customer voice.

Per customer need (U) and solution requirement (R) of the customer-VOC synthesis it shows
"X of N independent sources", prompted vs unprompted mentions, counter-evidence sources and
a confidence level, so a reader sees "3 of 14 sources, 2 unprompted" rather than a bare claim.

Counting rules (also rendered in the table footer):
1. Independent sources: records that share an `independence_key` OR a `duplicate_cluster_id`
   (transitively) are ONE source. Agreement among copies is not independent evidence.
2. Only accepted, firsthand, voice-typed reviews are counted at all.
3. Only `past_behaviour` and `commitment` statements count toward support. Compliments, fluff,
   feature requests, `unclassified` and missing types (legacy reviews) are shown separately as
   "mentioned but not supporting" and never add to support.
4. `total_sources` = independent reviewed firsthand sources in the SAME sampling frame as the
   item. topic_led_voc and entity_led_feedback are reported in separate columns, never summed.
5. Prompting: the review's `prompted` (bool) / `prompting` ("prompted"|"unprompted"|"unknown")
   field wins. Otherwise original posts and reviews on open platforms are `unprompted`; direct
   interview answers, comments (replying to someone else) and anything unrecognised are
   `unknown`. Prompting is never guessed. A source whose records disagree is `unknown`.
6. Confidence is computed per frame and the row reports the most conservative one:
   - high:   >= 3 independent supporting sources, >= 2 distinct source types, and no
             unresolved counter-evidence (a counter-evidence source exists and the item has no
             non-empty `counter_evidence_resolution`);
   - medium: >= 2 independent supporting sources and counter sources < supporting sources
             (also: >= 3 sources but a single type, or unresolved counter-evidence);
   - low:    anything else (0-1 sources, or counter sources >= supporting sources).
Frequency is not importance: a rarely stated need can be critical and a common one trivial.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    from reviewed_voice import VOICES, CLAIM_SUPPORTING_TYPES
except ImportError:  # imported as a package
    from scripts.evidence_scout.reviewed_voice import VOICES, CLAIM_SUPPORTING_TYPES

FRAMES = ("topic_led_voc", "entity_led_feedback")
# Platforms where the author volunteered the text (nobody asked about this need).
UNPROMPTED_SOURCES = {"reddit", "forum", "hn", "stackexchange", "quora", "x", "xai_x_search", "bluesky",
                      "producthunt", "google_places_review", "trustpilot_review", "app_store", "app_review",
                      "itunes_reviews", "amazon", "software_review", "g2_review", "shopify_app_review",
                      "cfpb_complaint", "v2ex", "zhihu", "douban", "tieba"}
FOOTER = [
    "Independent sources are counted by independence_key / duplicate_cluster_id; copies count once.",
    "Only past_behaviour and commitment statements support a need; compliments, fluff, feature requests and untyped reviews are listed separately.",
    "N is the number of independent reviewed firsthand sources in the same sampling frame; topic-led and entity-led counts are never merged.",
    "Prompting is taken from the review (`prompted`/`prompting`), else unprompted only for original posts/reviews on open platforms; otherwise unknown. It is never guessed.",
    "Confidence: high = >=3 independent supporting sources across >=2 source types with no unresolved counter-evidence; medium = >=2 supporting sources and fewer counter than supporting sources; low = otherwise. Per-frame; the row shows the most conservative.",
    "Frequency is not importance.",
]
RANK = {"low": 0, "medium": 1, "high": 2}


class _Sources:
    """Union-find over evidence ids sharing an independence key or duplicate cluster."""

    def __init__(self, records: dict[str, dict]):
        self.parent = {i: i for i in records}
        owner: dict[str, str] = {}
        for ident, r in records.items():
            for tag in ("independence_key", "duplicate_cluster_id"):
                v = r.get(tag)
                if v:
                    k = f"{tag}:{v}"
                    if k in owner:
                        self._union(ident, owner[k])
                    else:
                        owner[k] = ident

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def _union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def _prompting(record: dict, review: dict) -> str:
    value = review.get("prompted") if "prompted" in review else review.get("prompting")
    if value is True or value == "prompted":
        return "prompted"
    if value is False or value == "unprompted":
        return "unprompted"
    if value == "unknown":
        return "unknown"
    if record.get("source") in UNPROMPTED_SOURCES and record.get("capture_unit") != "document":
        return "unprompted"
    return "unknown"


def _confidence(supporting: int, types: int, counter: int, unresolved: bool) -> str:
    if supporting >= 3 and types >= 2 and not (counter and unresolved) and counter < supporting:
        return "high"
    if supporting >= 2 and counter < supporting:
        return "medium"
    return "low"


def build_table(synthesis: dict, source_review: dict, evidence_records: list[dict],
                run_summary: dict | None = None, customer_segment: str | None = None) -> dict:
    """Return {"rows", "frame_totals", "bias", "footer", ...}. One row per U/R item.

    synthesis: customer-VOC synthesis; source_review: the source-review file (`reviews`);
    evidence_records: evidence.jsonl rows; run_summary: summary.json (provider coverage gaps);
    customer_segment: optional, restricts counted reviews to that reviewed_segment.
    """
    records = {str(r.get("evidence_id")): r for r in evidence_records if r.get("evidence_id")}
    sources = _Sources(records)
    reviews = {}
    for rv in source_review.get("reviews", []) or []:
        ident = str(rv.get("evidence_id") or "")
        voice = rv.get("voice")
        rec = records.get(ident)
        if (rec and rv.get("status") == "accepted" and voice in VOICES and rv.get("firsthand") is True
                and rv.get("author_relationship") == VOICES[voice]
                and (customer_segment is None or rv.get("reviewed_segment") == customer_segment)):
            reviews[ident] = rv
    frame_of = {i: records[i].get("sampling_frame") for i in reviews}
    for key, frame in (("topic_led_evidence_ids", "topic_led_voc"), ("entity_led_evidence_ids", "entity_led_feedback")):
        for i in synthesis.get(key, []) or []:
            if i in reviews and not frame_of.get(i):
                frame_of[i] = frame

    totals = {f: set() for f in FRAMES}
    types_total: dict[str, Counter] = {f: Counter() for f in FRAMES}
    seen_src: set[tuple] = set()
    for i in reviews:
        f = frame_of.get(i)
        if f in totals:
            totals[f].add(sources.find(i))
            if (f, sources.find(i)) not in seen_src:
                seen_src.add((f, sources.find(i)))
                types_total[f][records[i].get("source") or "unknown"] += 1

    def frame_stats(item: dict, frame: str) -> dict | None:
        ids = [i for i in item.get("evidence_ids", []) if i in reviews and frame_of.get(i) == frame]
        if not ids:
            return None
        by_src: dict[str, list[str]] = defaultdict(list)
        for i in ids:
            by_src[sources.find(i)].append(i)
        support, other = {}, {}
        for s, members in by_src.items():
            sup = [m for m in members if reviews[m].get("statement_type") in CLAIM_SUPPORTING_TYPES]
            (support if sup else other)[s] = sup or members
        states = {s: {_prompting(records[m], reviews[m]) for m in ms} for s, ms in support.items()}
        pr = Counter(("unknown" if len(v) > 1 else next(iter(v))) for v in states.values())
        counter_srcs = {sources.find(i) for i in item.get("counter_evidence_ids", []) or []
                        if i in records and frame_of.get(i, records[i].get("sampling_frame")) == frame}
        counter_srcs -= set(support)  # a source that supports is not also counted against
        stypes = {records[m].get("source") for ms in support.values() for m in ms}
        unresolved = not str(item.get("counter_evidence_resolution") or "").strip()
        segs = sorted({str(reviews[m].get("reviewed_segment") or records[m].get("customer_segment") or "unknown")
                       for ms in support.values() for m in ms})
        return {"sources": len(support), "total_sources": len(totals[frame]),
                "unprompted": pr["unprompted"], "prompted": pr["prompted"], "unknown_prompting": pr["unknown"],
                "mentioned_not_supporting": len(other), "counter_sources": len(counter_srcs),
                "source_types": sorted(t for t in stypes if t), "segments": segs,
                "confidence": _confidence(len(support), len(stypes), len(counter_srcs), unresolved)}

    rows = []
    for kind, key in (("need", "customer_needs"), ("requirement", "solution_requirements")):
        for item in synthesis.get(key, []) or []:
            fr = {f: s for f in FRAMES if (s := frame_stats(item, f))}
            conf = min((s["confidence"] for s in fr.values()), key=RANK.get, default="low")
            counters = set()
            for f in fr:
                counters |= {sources.find(i) for i in item.get("counter_evidence_ids", []) or [] if i in records}
            rows.append({"id": item.get("id"), "kind": kind, "text": item.get("outcome") or item.get("condition_or_capability"),
                         "frames": fr, "segments": sorted({g for s in fr.values() for g in s["segments"]}),
                         "counter_sources": len(counters), "confidence": conf})

    gaps = {name: s.get("status") for name, s in (run_summary or {}).get("providers", {}).items()
            if isinstance(s, dict) and s.get("status") not in {"ok", None}}
    skew = {}
    for f in FRAMES:
        n = len(totals[f])
        if n:
            top, cnt = types_total[f].most_common(1)[0]
            skew[f] = {"source_types": dict(types_total[f]), "dominant_type": top, "dominant_share": round(cnt / n, 2)}
    legacy = sum(1 for r in reviews.values() if r.get("statement_type") is None)
    return {"generated_view": True, "rows": rows,
            "frame_totals": {f: len(totals[f]) for f in FRAMES},
            "bias": {"frames_not_sampled": [f for f in FRAMES if not totals[f]],
                     "provider_coverage_gaps": gaps, "source_type_skew": skew,
                     "legacy_untyped_reviews": legacy,
                     "note": "Public posts and reviews over-represent strong opinions; people who were satisfied, silent or unreachable are missing."},
            "footer": FOOTER}


def _cell(s: dict | None) -> str:
    if not s:
        return "n/a (no evidence in frame)"
    return (f"{s['sources']} of {s['total_sources']} ({s['unprompted']} unprompted, {s['prompted']} prompted, "
            f"{s['unknown_prompting']} unknown); {s['mentioned_not_supporting']} mentioned, not supporting; "
            f"{s['counter_sources']} counter; {s['confidence']}")


def render_markdown(table: dict) -> str:
    out = ["# Cross-source frequency table", "",
           "| ID | Need / requirement | Segments | Topic-led VOC | Entity-led feedback | Counter sources | Confidence |",
           "|---|---|---|---|---|---|---|"]
    for r in table["rows"]:
        text = str(r.get("text") or "").replace("|", "/")
        out.append(f"| {r['id']} | {text} | {', '.join(r['segments']) or 'n/a'} | {_cell(r['frames'].get('topic_led_voc'))} "
                   f"| {_cell(r['frames'].get('entity_led_feedback'))} | {r['counter_sources']} | {r['confidence']} |")
    b = table["bias"]
    out += ["", "## Bias and coverage", ""]
    out.append("- Not sampled: " + (", ".join(b["frames_not_sampled"]) or "none (both frames have reviewed sources)"))
    out.append("- Provider coverage gaps: " + (", ".join(f"{k} ({v})" for k, v in b["provider_coverage_gaps"].items()) or "none recorded in the run summary"))
    for f, s in b["source_type_skew"].items():
        out.append(f"- Source-type skew in {f}: {s['dominant_type']} is {int(s['dominant_share'] * 100)}% of sources ({s['source_types']})")
    if b["legacy_untyped_reviews"]:
        out.append(f"- {b['legacy_untyped_reviews']} legacy review(s) have no statement_type and do not count as support.")
    out.append("- " + b["note"])
    out += ["", "## How to read this table", ""] + [f"- {line}" for line in table["footer"]]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--synthesis", type=Path, required=True)
    p.add_argument("--source-review", type=Path, required=True)
    p.add_argument("--summary", type=Path, help="Run summary.json for provider coverage gaps.")
    p.add_argument("--customer-segment")
    p.add_argument("--out-dir", type=Path, required=True)
    a = p.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    records = [json.loads(line) for line in a.evidence.read_text(encoding="utf-8").splitlines() if line.strip()]
    table = build_table(load(a.synthesis), load(a.source_review), records,
                        load(a.summary) if a.summary else None, a.customer_segment)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    (a.out_dir / "voc-table.json").write_text(json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (a.out_dir / "voc-table.md").write_text(render_markdown(table), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
