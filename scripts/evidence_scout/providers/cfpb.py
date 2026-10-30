"""CFPB Consumer Complaint Database (official public API, no key).

Narratives are CC0 and carry CFPB's own "XXXX" redaction markers, kept as-is.
Only state-level geography is retained; ZIP codes are dropped. The company
named in a complaint is the *entity* complained about, not a voice.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "validate_apis"
if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))

from common import http_get, status_from_response, with_query  # noqa: E402

ENDPOINT = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
COMPLAINT_URL = ENDPOINT.split("/search/")[0] + "/search/detail/{}"
SAMPLING_NOTE = ("CFPB complaint database, relevance-ranked; consumers who file complaints are a self-selected "
                 "subset; narratives are published only with consumer consent; not a representative sample.")
NARRATIVE_FIELD = "complaint_what_happened"


def fetch(query: str, size: int, timeout: int = 30) -> tuple[dict, dict]:
    # field=all: the live API no longer accepts field=complaint_what_happened (only company|all).
    # has_narrative is sent for forward compatibility; the live API currently ignores it.
    url = with_query(ENDPOINT, {"search_term": query, "field": "all", "size": size,
                                "has_narrative": "true", "no_aggs": "true", "sort": "relevance_desc"})
    response = http_get(url, timeout=timeout, max_text_chars=2_000_000)
    return (response.get("body") if isinstance(response.get("body"), dict) else {}), {
        "status": status_from_response(response), "response": response}


def _default_builder() -> Callable[..., dict[str, Any]]:
    from collect import normalize_record  # lazy: collect imports this module
    return normalize_record


def to_records(body: dict, query: str, retrieved_at: str, build: Callable[..., dict[str, Any]] | None = None,
               customer_segment: str = "", hypothesis: str = "") -> list[dict]:
    build = build or _default_builder()
    hits = (body.get("hits") or {}).get("hits") if isinstance(body.get("hits"), dict) else []
    records: list[dict] = []
    for hit in hits or []:
        src = hit.get("_source") if isinstance(hit, dict) else None
        if not isinstance(src, dict):
            continue
        text = str(src.get(NARRATIVE_FIELD) or "").strip()
        cid = str(src.get("complaint_id") or hit.get("_id") or "")
        if not text or not cid:
            continue
        context = "; ".join(f"{label}={src[key]}" for label, key in
                            (("product", "product"), ("issue", "issue"), ("company_complained_about", "company"),
                             ("state", "state")) if src.get(key))
        rec = build(source="cfpb_complaint", source_url=COMPLAINT_URL.format(cid), query=query,
                    customer_segment=customer_segment, hypothesis=hypothesis, text=text,
                    author_context="Consumer complaint to CFPB; " + context, raw_id=cid,
                    published_at=(src.get("date_received") or "")[:10] or None,
                    evidence_type="pain", source_role_override="customer_statement",
                    author_voice_status="unreviewed",
                    confidence_notes="Firsthand consumer complaint narrative (CC0) filed with the CFPB; "
                                     "the named company is the subject of the complaint, not the speaker. Review required.")
        rec["retrieved_at"] = retrieved_at
        rec["collection_method"] = "official_api"
        rec["retrieval_backend"] = "cfpb_complaints"
        rec["sampling_metadata"]["subset_limitations"] = SAMPLING_NOTE
        records.append(rec)
    return records
