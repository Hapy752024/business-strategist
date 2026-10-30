"""Generic Apify actor runner plus config-driven record mapping for review lanes.

Third-party scrapes of PUBLIC pages only. Lane settings live in
config/apify-actors.json. No login, cookie or credentialed-proxy option is ever
built into an input. The Apify token travels in the Authorization header only.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "validate_apis"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

from common import http_post, status_from_response  # noqa: E402

CONFIG = Path(__file__).resolve().parents[3] / "config" / "apify-actors.json"
RUN_URL = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
SCRAPE_NOTE = "third-party scrape (Apify actor) of public pages; completeness unknown, not a representative sample."
PLACEHOLDER = re.compile(r"^\{(\w+)\}$")


class CapExceeded(Exception):
    """Requested Apify items exceed the per-run cap; raised before any network call."""


def load_config(path: Path = CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_input(template: Any, values: dict[str, Any]) -> Any:
    """Fill {placeholders}; a whole-string placeholder keeps the value's type."""
    if isinstance(template, dict):
        return {key: render_input(value, values) for key, value in template.items()}
    if isinstance(template, list):
        return [render_input(value, values) for value in template]
    if isinstance(template, str):
        match = PLACEHOLDER.match(template)
        if match and match.group(1) in values:
            return values[match.group(1)]
    return template


def requested_items(lane_cfg: dict[str, Any], units: int, per_unit_limit: int) -> int:
    floor = int(lane_cfg.get("min_items_per_call", 1))
    return max(0, units) * max(1, per_unit_limit, floor) * int(lane_cfg.get("items_per_unit", 1))


def charge_cap_usd(lane_cfg: dict[str, Any], items: int) -> float:
    """Per-run charge ceiling sent to Apify: twice the expected event cost plus a floor."""
    expected = items * float(lane_cfg["cost_per_1k_usd"]) / 1000 + float(lane_cfg.get("fixed_cost_per_run_usd", 0))
    return max(float(lane_cfg.get("min_max_charge_usd", 0)), round(expected * 2 + 0.05, 4))


def run_actor(actor_id: str, input: dict[str, Any], cap: int, *, requested_items: int, token: str,
              timeout_s: int = 150, max_charge_usd: float | None = None) -> tuple[list[dict], dict[str, Any]]:
    """Run one actor synchronously. Refuses (CapExceeded) before any network call."""
    if requested_items > cap:
        raise CapExceeded(f"Apify items requested ({requested_items}) exceed the cap ({cap}); no call made.")
    url = RUN_URL.format(actor=actor_id.replace("/", "~")) + f"?timeout={timeout_s}&memory=512"
    if max_charge_usd is not None:
        url += f"&maxTotalChargeUsd={max_charge_usd}"
    response = http_post(url, headers={"Authorization": f"Bearer {token}"}, data=input,
                         timeout=timeout_s + 30, max_text_chars=2_000_000)
    body = response.get("body")
    items = [item for item in body if isinstance(item, dict)] if isinstance(body, list) else []
    return items, {"status": status_from_response(response), "http_status": response.get("status_code"), "response": response}


def _dig(item: Any, path: str) -> Any:
    for part in path.split("."):
        if not isinstance(item, dict):
            return None
        item = item.get(part)
    return item


def _clean(value: Any) -> str:
    return " ".join(html.unescape(str(value)).split()) if value is not None and not isinstance(value, (dict, list)) else ""


def _iso(value: Any) -> str | None:
    text = _clean(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return f"{text}T00:00:00Z"
    return text or None


def _map(item: dict, field_map: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {"text": [], "context": [], "engagement": {}}
    for field, target in field_map.items():
        value = _dig(item, field)
        if value in (None, "", [], {}):
            continue
        kind, _, label = target.partition(":")
        if kind == "text":
            body = html.unescape(str(value)).strip()
            if body:
                out["text"].append(f"{label}: {body}" if label else body)
        elif kind == "flag":
            out["context"].append(f"{label}=true")
        elif kind == "context":
            out["context"].append(f"{label}={_clean(value)}")
        elif kind == "engagement":
            out["engagement"][label] = value
        else:
            out[kind] = value
    return out


def _text_fingerprint(item: dict, field_map: dict[str, str]) -> str:
    """Hash of the raw free-text fields (no labels), lowercased and whitespace-collapsed."""
    parts = [str(_dig(item, f)) for f, target in field_map.items() if target.partition(":")[0] == "text" and _dig(item, f) not in (None, "", [], {})]
    norm = " ".join(html.unescape(" ".join(parts)).lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()


def _default_builder() -> Callable[..., dict[str, Any]]:
    from collect import normalize_record  # lazy: collect imports this module
    return normalize_record


def to_records(lane: str, items: list[dict], query: str, retrieved_at: str,
               build: Callable[..., dict[str, Any]] | None = None, customer_segment: str = "",
               hypothesis: str = "", subject_entity_id: str = "", config: dict | None = None,
               extra_field_map: dict[str, str] | None = None,
               seen_hashes: set[str] | None = None) -> list[dict]:
    """Map actor items to evidence records using the lane's field_map.

    Reviewer names, usernames, store names and profile links are never mapped.
    Vendor replies (target ``vendor_reply``) become separate supplier records.
    """
    cfg = (config or load_config())["lanes"][lane]
    build = build or _default_builder()
    seen = seen_hashes if seen_hashes is not None else set()
    backend = f"apify_{lane}"
    field_map = {**cfg["field_map"], **(extra_field_map or {})}
    flag_field = cfg.get("incentivised_flag_field")
    note = f"{lane}: {SCRAPE_NOTE}"
    records: list[dict] = []

    def finish(rec: dict, parent: str | None = None) -> dict:
        rec["retrieved_at"] = retrieved_at
        rec["collection_method"] = "third_party_scrape"
        rec["retrieval_backend"] = backend
        rec["sampling_metadata"]["subset_limitations"] = note
        if parent:
            rec["parent_source_record_id"] = parent
        return rec

    def emit(item: dict, fmap: dict[str, str], source: str, parent: str | None, entity_lane: bool) -> dict | None:
        m = _map(item, fmap)
        text = "\n\n".join(m["text"]).strip()
        url = _clean(m.get("source_url"))
        if not text or not url:
            return None
        digest = _text_fingerprint(item, fmap)
        if entity_lane and digest in seen:
            return None  # same review text already collected, on any entity or lane (e.g. a syndicated G2-family copy)
        raw_id = _clean(m.get("raw_id")) or hashlib.sha256(f"{url}|{text}".encode()).hexdigest()[:16]
        if parent:
            raw_id = f"{parent}/{raw_id}"
        context = list(m["context"])
        if entity_lane:
            context.insert(0, f"rating={_clean(m.get('rating')) or 'n/a'}")
        rec = build(
            source=source, source_url=url, query=query, customer_segment=customer_segment, hypothesis=hypothesis,
            text=text, author_context="; ".join(context), engagement=m["engagement"], raw_id=raw_id,
            published_at=_iso(m.get("published_at")), author_voice_status="unreviewed",
            sampling_frame=cfg["sampling_frame"], subject_entity_id=subject_entity_id if entity_lane else "",
            source_role_override=cfg.get("source_role") or None,
            source_intent_override="customer_feedback" if cfg.get("source_role") == "customer_review" else None,
        )
        finish(rec, parent)
        if entity_lane:
            seen.add(digest)
        return rec

    entity_lane = cfg["sampling_frame"] == "entity_led_feedback"
    for item in items:
        rec = emit(item, field_map, cfg["source"], None, entity_lane)
        if rec is None:
            continue
        if flag_field and item.get(flag_field):
            rec["signal_quality"] = {"authenticity": "incentivised"}
        records.append(rec)
        reply = _map(item, field_map).get("vendor_reply")
        if reply:
            sup = build(
                source=cfg["source"], source_url=rec["source_url"], query=query, customer_segment=customer_segment,
                hypothesis=hypothesis, text=str(reply).strip(), author_context=f"vendor reply to review {rec['source_record_id']}",
                raw_id=f"{rec['source_record_id']}:vendor-reply", source_role_override="competitor_context",
                source_intent_override="competitor_content", author_voice_status="supplier_context",
                sampling_frame=cfg["sampling_frame"], subject_entity_id=subject_entity_id if entity_lane else "",
                confidence_notes="Vendor reply attached to a review; retain as supplier context, never customer voice.",
            )
            records.append(finish(sup, rec["source_record_id"]))
        for child in cfg.get("children", []):
            for sub in item.get(child["path"]) or []:
                if isinstance(sub, dict):
                    crec = emit(sub, child["field_map"], child.get("source", cfg["source"]), rec["source_record_id"], False)
                    if crec:
                        records.append(crec)
    return records
