"""Meta Marketing API: create a campaign, always PAUSED, only with a spend limit.

Docs: https://developers.facebook.com/docs/marketing-api/reference/ad-account/campaigns/
POST https://graph.facebook.com/{version}/act_{ad_account_id}/campaigns (status may be ACTIVE or PAUSED at creation;
this adapter only ever sends PAUSED). ``spend_cap`` is in currency subunits. Without a campaign budget Meta expects an
explicit ``is_adset_budget_sharing_enabled`` (the documented example sends ``0``); the adapter defaults it to ``False``.
Graph API v26.0 is the latest version (introduced 2026-07-29, checked 2026-10-31 on the Graph API changelog).
Reporting goes through the read-only ``meta-ads`` MCP; this adapter is the only campaign write path.
Meta documents a minimum ``spend_cap`` of about 100 USD or the local equivalent (campaign reference above); the adapter
cannot see the ad account's currency, so a cap below 10000 subunits produces a dry-run note instead of a refusal.
Sending ``is_adset_budget_sharing_enabled`` together with a campaign-level budget is unverified and refused.
"""
from __future__ import annotations

from . import first_id, require_secret

REQUIRES_ENV = ("META_ACCESS_TOKEN",)
GRAPH = "https://graph.facebook.com"
VERSION = "v26.0"
MIN_SPEND_CAP_HINT = 10000  # 100.00 in a two-decimal currency; Meta: "minimum value of $100 USD (or approximate local equivalent)"
ALLOWED = {"ad_account_id", "name", "objective", "special_ad_categories", "spend_cap", "daily_budget",
           "lifetime_budget", "status", "buying_type", "bid_strategy", "is_adset_budget_sharing_enabled"}


def validate(request: dict, approval: dict, now=None) -> list[str]:
    errors = []
    for field in ("ad_account_id", "name", "objective"):
        if not str(request.get(field) or "").strip():
            errors.append(f"meta campaign requires {field}")
    if not str(request.get("ad_account_id") or "").replace("act_", "").isdigit():
        errors.append("meta ad_account_id must be numeric")
    cap = request.get("spend_cap")
    if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0 or cap >= 922337203685478:
        errors.append("meta campaign requires a positive integer spend_cap (spend limit in currency subunits)")
    sharing = request.get("is_adset_budget_sharing_enabled", False)
    if not isinstance(sharing, bool):
        errors.append("meta is_adset_budget_sharing_enabled must be true or false")
    if "is_adset_budget_sharing_enabled" in request and ("daily_budget" in request or "lifetime_budget" in request):
        errors.append("meta is_adset_budget_sharing_enabled with a campaign-level daily_budget/lifetime_budget is unverified; "
                      "send one or the other")
    if request.get("status", "PAUSED") != "PAUSED":
        errors.append("meta campaigns are only ever created PAUSED; activation is a manual founder step")
    unknown = set(request) - ALLOWED
    if unknown:
        errors.append(f"meta campaign has unsupported fields: {sorted(unknown)}")
    return errors


def _body(request: dict) -> dict:
    body = {k: v for k, v in request.items() if k != "ad_account_id"}
    body.setdefault("special_ad_categories", [])
    if "daily_budget" not in body and "lifetime_budget" not in body:
        body.setdefault("is_adset_budget_sharing_enabled", False)
    body["status"] = "PAUSED"  # enforced regardless of input
    return body


def _url(request: dict) -> str:
    account = str(request["ad_account_id"]).replace("act_", "")
    return f"{GRAPH}/{VERSION}/act_{account}/campaigns"


def notes(request: dict) -> list[str]:
    cap = request.get("spend_cap")
    if isinstance(cap, int) and not isinstance(cap, bool) and cap < MIN_SPEND_CAP_HINT:
        return [f"spend_cap {cap} subunits may be below Meta's documented minimum (about 100 USD or local equivalent); "
                "Meta rejects a lower cap. Check the ad account currency before approving."]
    return []


def describe(request: dict, approval: dict) -> list[dict]:
    call = {"method": "POST", "url": _url(request), "body": _body(request)}
    if notes(request):
        call["notes"] = notes(request)
    return [call]


def run(request: dict, approval: dict, *, http, secret) -> dict:
    token = require_secret(secret, "META_ACCESS_TOKEN")
    body = _body(request)
    assert body["status"] == "PAUSED"
    response = http("POST", _url(request), {"Authorization": f"Bearer {token}"}, body)
    return {"status": "created_paused", "provider_ids": {"campaign_id": first_id(response, "id")}}
