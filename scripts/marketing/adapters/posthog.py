"""PostHog: create an experiment (and its feature flag) in draft state.

Endpoint: POST {POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/experiments/ with a personal API key as Bearer
token (https://posthog.com/docs/api/experiments). An experiment without ``start_date`` stays a draft; PostHog
creates the feature flag for a new ``feature_flag_key``. Launching is a manual founder step.
"""
from __future__ import annotations

from . import first_id, require_secret

REQUIRES_ENV = ("POSTHOG_HOST", "POSTHOG_PERSONAL_API_KEY", "POSTHOG_PROJECT_ID")
ALLOWED = {"name", "description", "feature_flag_key", "parameters", "filters", "metrics", "metrics_secondary"}


def validate(request: dict, approval: dict, now=None) -> list[str]:
    errors = [f"posthog experiment requires {f}" for f in ("name", "feature_flag_key")
              if not str(request.get(f) or "").strip()]
    if request.get("start_date") or request.get("launch"):
        errors.append("posthog experiments are only created as drafts; launching is a manual founder step")
    unknown = set(request) - ALLOWED - {"start_date", "launch"}
    if unknown:
        errors.append(f"posthog experiment has unsupported fields: {sorted(unknown)}")
    return errors


def _body(request: dict) -> dict:
    return {k: v for k, v in request.items() if k in ALLOWED}


def describe(request: dict, approval: dict) -> list[dict]:
    return [{"method": "POST", "url": "{POSTHOG_HOST}/api/projects/{POSTHOG_PROJECT_ID}/experiments/",
             "body": _body(request)}]


def run(request: dict, approval: dict, *, http, secret) -> dict:
    host = require_secret(secret, "POSTHOG_HOST").rstrip("/")
    key = require_secret(secret, "POSTHOG_PERSONAL_API_KEY")
    project = require_secret(secret, "POSTHOG_PROJECT_ID")
    response = http("POST", f"{host}/api/projects/{project}/experiments/", {"Authorization": f"Bearer {key}"},
                    _body(request))
    return {"status": "draft_created",
            "provider_ids": {"experiment_id": first_id(response, "id"),
                             "feature_flag_id": first_id((response or {}).get("feature_flag") if isinstance(response, dict) else None, "id")}}
