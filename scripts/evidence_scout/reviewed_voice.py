"""One source/author decision contract for VoC, claims and interview consumers.

Automated classifications are suggestions, not immutable facts. Corrections need
located original content and author context; explicit supplier attribution cannot
be overridden. This validates review structure, not the reviewer's interpretation.
"""
from __future__ import annotations

VOICES = {
    "customer": "firsthand_customer", "former_customer": "firsthand_former_customer",
    "prospective_user": "firsthand_prospective_user", "nonadopter": "firsthand_nonadopter",
}
CUSTOMER_ROLES = {"customer_statement", "customer_review", "community_context"}
SUPPLIER_VOICES = {"supplier_context", "supplier", "company", "affiliate", "official_provider"}


def review_voice(record: dict, review: dict, segment: str) -> list[str]:
    errors = []
    if review.get("reviewed_segment") != segment:
        errors.append("reviewed_segment mismatch")
    if review.get("source_url") != record.get("source_url"):
        errors.append("source review URL mismatch")
    if review.get("segment_relation") not in {"target", "adjacent", "unresolved"}:
        errors.append("accepted review requires segment_relation")
    if not str(review.get("relevance_rationale") or "").strip():
        errors.append("accepted review requires relevance_rationale")
    voice = review.get("voice")
    if voice not in VOICES:
        return errors
    if review.get("author_relationship") != VOICES[voice]:
        errors.append(f"{voice} review requires author_relationship={VOICES[voice]}")
    if type(review.get("firsthand")) is not bool:
        errors.append("accepted review requires boolean firsthand")
    role = record.get("source_role")
    supplier = record.get("author_voice_status") in SUPPLIER_VOICES or record.get("classification_basis") == "explicit_supplier_identity"
    if supplier:
        errors.append("supplier/noncustomer record cannot become customer voice")
    local_review = review.get("reviewed_source_kind") in {"forum", "independent_review"} and bool(str(review.get("source_kind_rationale") or "").strip())
    heuristic_correction = record.get("classification_basis") == "heuristic" and local_review and role in {"search_result", "editorial_context", "competitor_context"}
    corrected = role not in CUSTOMER_ROLES or record.get("source_intent") in {"competitor_content", "editorial_content", "official_provider"}
    if corrected and not (role == "search_result" and local_review) and not heuristic_correction:
        errors.append("reviewed user voice contradicts original source_role without reviewed source correction")
    if heuristic_correction and corrected:
        passage = str(review.get("supporting_passage") or "")
        if not passage.strip() or passage not in str(record.get("text") or ""):
            errors.append("heuristic correction requires an exact supporting_passage in preserved text")
        if not str(review.get("author_context_basis") or "").strip():
            errors.append("heuristic correction requires author_context_basis")
    if record.get("capture_unit") == "document":
        errors.append("multi-speaker/unsegmented document must be split into source-linked experiences before voice acceptance")
    if record.get("content_completeness") in {"snippet", "search_snippet"}:
        errors.append("search snippet must be hydrated before voice acceptance")
    if any(record.get(key) == "irrelevant" for key in ("relevance", "evidence_type", "strength")):
        inherited_heuristic = record.get("original_classification", {}).get("classification_basis") == "heuristic"
        passage = str(review.get("supporting_passage") or "")
        located_correction = local_review and passage.strip() and passage in str(record.get("text") or "") and str(review.get("author_context_basis") or "").strip()
        if not ((heuristic_correction or inherited_heuristic) and located_correction and str(review.get("relevance_correction_rationale") or "").strip()):
            errors.append("accepted review contradicts explicit irrelevant label")
    if voice in {"prospective_user", "nonadopter"} and not str(review.get("decision_context") or "").strip():
        errors.append(f"{voice} review requires decision_context")
    return errors


def reviewed_view(record: dict, review: dict) -> dict:
    """Non-mutating view: keep original classification and review side by side."""
    return {**record, "_source_review": review,
            "analyst_review": {**review, "reason": review.get("relevance_rationale", "")}}


def reviewed_collection_locales(record: dict, review: dict) -> set[str]:
    """Resolve a country-only multilingual feed without rewriting its capture."""
    locale = str(record.get("collection_locale") or "")
    if not locale.endswith(":und"):
        return {locale} if locale else set()
    resolution = review.get("language_review", {})
    quote = resolution.get("supporting_passage")
    if not isinstance(quote, str) or not quote.strip() or quote not in record.get("text", "") or not resolution.get("rationale"):
        return set()
    language = resolution.get("language")
    return {item for item in record.get("requested_locales", [])
            if item.split(":", 1)[0] == locale.split(":", 1)[0] and item.split(":", 1)[1] == language}
