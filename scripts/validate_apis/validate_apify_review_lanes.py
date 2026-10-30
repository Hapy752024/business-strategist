#!/usr/bin/env python3
"""Free check of the Apify review lanes: token, plan limits, and each lane's actor id.

Default mode makes only free GET calls (account limits, actor metadata) and
never runs an actor. ``--live LANE`` runs that lane once with its smallest input
and refuses when this month's Apify usage is 3 USD or more.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import finish, get_secret, http_get, http_post, missing_credentials, status_from_response

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evidence_scout"))
from providers import apify_actor  # noqa: E402

PROVIDER = "apify_review_lanes"
USAGE_STOP_USD = 3.0
SMALLEST = {  # lane -> (placeholders, items requested); actor minimums apply (G2 returns >= 10)
    "software_reviews": ({"entity_url": "https://www.trustradius.com/products/slack/reviews", "max_items": 3}, 3),
    "g2_reviews": ({"entity_url": "https://www.g2.com/products/notion/reviews", "max_items": 10}, 10),
    "shopify_app_reviews": ({"entity_url": "klaviyo-email-marketing", "max_items": 3}, 3),
    "quora": ({"query": "unpaid invoices freelancer", "max_items": 3}, 3),
    "facebook_public_groups": ({"group_url": "https://www.facebook.com/groups/63181993057/", "max_items": 2}, 2),
}


def monthly_usage(headers: dict) -> float | None:
    resp = http_get("https://api.apify.com/v2/users/me/limits", headers=headers)
    body = resp.get("body")
    try:
        return float(body["data"]["current"]["monthlyUsageUsd"])
    except (TypeError, KeyError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", choices=sorted(SMALLEST), help="Run one lane once with its smallest input.")
    args = parser.parse_args()
    key_name, token = get_secret("APIFY_TOKEN")
    if not token:
        return missing_credentials(PROVIDER, ["APIFY_TOKEN"], [
            "Create or log in at https://console.apify.com/",
            "Open Settings -> Integrations -> API token",
            "Set it with: export APIFY_TOKEN='your_token'",
        ])
    headers = {"Authorization": f"Bearer {token}"}
    lanes = apify_actor.load_config()["lanes"]
    usage = monthly_usage(headers)
    actors = {}
    for lane, cfg in lanes.items():
        resp = http_get(f"https://api.apify.com/v2/acts/{cfg['actor_id'].replace('/', '~')}", headers=headers)
        actors[lane] = "ok" if status_from_response(resp) == "ok" else status_from_response(resp)
    summary = {"status": "ok" if all(v == "ok" for v in actors.values()) else "failed", "credential_source": key_name,
               "monthly_usage_usd": usage, "actors": actors, "live_stop_usd": USAGE_STOP_USD,
               "cost_note": "Default mode runs no actor and costs nothing."}
    response = {"ok": True, "status_code": 200, "body": None}
    if args.live:
        if usage is None or usage >= USAGE_STOP_USD:
            summary.update({"status": "request_budget_exhausted", "live": args.live,
                            "reason": f"Apify monthly usage {usage} USD is at or above {USAGE_STOP_USD} USD; live check refused."})
        else:
            cfg = lanes[args.live]
            values, count = SMALLEST[args.live]
            run = http_post(apify_actor.RUN_URL.format(actor=cfg["actor_id"].replace("/", "~")) +
                            f"?timeout=150&memory=512&maxTotalChargeUsd={apify_actor.charge_cap_usd(cfg, count)}",
                            headers=headers, timeout=180, data=apify_actor.render_input(cfg["input_template"], values))
            body = run.get("body")
            ok = status_from_response(run) == "ok" and isinstance(body, list) and bool(body)
            summary.update({"live": args.live, "live_status": "ok" if ok else "failed", "items_returned": len(body) if isinstance(body, list) else 0,
                            "usage_after_usd": monthly_usage(headers)})
            if not ok:
                summary["status"] = "failed"
            response = run
    return finish(PROVIDER, summary, response)


if __name__ == "__main__":
    raise SystemExit(main())
