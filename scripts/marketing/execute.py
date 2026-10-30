#!/usr/bin/env python3
"""Approval-bound marketing execution: the only path for an external marketing write.

``execute()`` refuses unless a founder approval matches the exact action digest, names a human, is unexpired, is
scoped to the action kind and the action has not already been attempted. Dry run is the default; a real send needs
``dry_run=False`` (CLI: ``run ... --execute``). Every attempt writes a secret-free receipt under
``<marketing-root>/receipts/``. ``approve`` creates approvals only for an interactive human (or with the founder PIN).
Agents must never run ``approve`` or ``run --execute``, and must never set ``MARKETING_APPROVAL_PIN``.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.marketing.execution import authorization_digest  # noqa: E402
from scripts.marketing.adapters import AdapterError, meta_ads, posthog, postiz, resend, urllib_http  # noqa: E402
from scripts.validate_apis.common import get_secret, redact_sensitive  # noqa: E402

ADAPTERS = {"schedule_post": postiz, "create_campaign": meta_ads, "send_broadcast": resend,
            "create_experiment": posthog}
DEFAULT_VALIDITY = timedelta(days=7)
CLOCK_SKEW = timedelta(minutes=5)
AGENT_IDENTITIES = {"claude", "agent", "assistant", "subagent", "tool", "ai", "bot", "llm", "model", "system",
                    "codex", "gpt", "chatgpt", "gemini", "copilot", "automation", "script"}
ACTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
BLOCKING_OUTCOMES = {"executed", "uncertain", "failed"}
PIN_ENV = "MARKETING_APPROVAL_PIN"


def is_agent_identity(name) -> bool:
    text = str(name or "").strip().lower()
    if not text:
        return True
    tokens = {t for t in re.split(r"[^a-z0-9]+", text) if t}
    return bool(tokens & AGENT_IDENTITIES) or "claude" in text or "anthropic" in text


def _parse_time(value) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def bound_request(action: dict) -> dict:
    """Adapters only see the digest-bound provider request, so nothing unapproved can be sent."""
    request = action.get("provider_request")
    return json.loads(json.dumps(request)) if isinstance(request, dict) else {}


def check_approval(action: dict, approval: dict, *, now: datetime, validity: timedelta) -> list[str]:
    reasons = []
    if not isinstance(approval, dict):
        return ["approval is missing"]
    if not ACTION_ID.match(str(action.get("id") or "")):
        reasons.append("action id is missing or not a safe identifier")
    if approval.get("action_id") not in (None, action.get("id")):
        reasons.append("approval is for a different action id")
    if not approval.get("digest") or not hmac.compare_digest(str(approval.get("digest")), authorization_digest(action)):
        reasons.append("approval digest does not match the exact action (changed after approval or never approved)")
    if is_agent_identity(approval.get("granted_by")):
        reasons.append("granted_by must name the human founder; agent/tool identities cannot approve")
    granted = _parse_time(approval.get("granted_at")) if approval.get("granted_at") else None
    if granted is None:
        reasons.append("approval granted_at is missing or invalid")
    elif granted > now + CLOCK_SKEW:
        reasons.append("approval granted_at is in the future")
    elif now - granted > validity:
        reasons.append(f"approval expired (older than {validity.days} days)")
    if approval.get("scope") != action.get("action_kind"):
        reasons.append(f"approval scope {approval.get('scope')!r} does not match action_kind {action.get('action_kind')!r}")
    if action.get("execution_status") in {"submitted", "verified"}:
        reasons.append("action is already executed according to its execution_status")
    return reasons


def _receipt_dir(marketing_root) -> Path | None:
    return None if marketing_root is None else Path(marketing_root) / "receipts"


def prior_attempts(marketing_root, action_id: str) -> list[dict]:
    folder = _receipt_dir(marketing_root)
    if folder is None or not folder.is_dir() or not ACTION_ID.match(action_id or ""):
        return []
    found = []
    for path in folder.glob(f"{action_id}-*.json"):
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if receipt.get("action_id") == action_id:
            found.append(receipt)
    return found


def _scrub(value, secrets: list[str]):
    text = json.dumps(redact_sensitive(value), sort_keys=True, default=str)
    for secret in sorted({s for s in secrets if s and len(s) >= 4}, key=len, reverse=True):
        text = text.replace(json.dumps(secret)[1:-1], "***")
    return json.loads(text)


def write_receipt(marketing_root, action_id: str, receipt: dict, secrets: list[str]) -> Path | None:
    folder = _receipt_dir(marketing_root)
    if folder is None or not ACTION_ID.match(action_id or ""):
        return None
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for n in range(1000):
        path = folder / f"{action_id}-{stamp}{'' if n == 0 else f'-{n}'}.json"
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(_scrub(receipt, secrets), handle, indent=2, sort_keys=True)
        return path
    raise RuntimeError("could not allocate a receipt path")


def _claim(marketing_root, action_id: str) -> bool:
    """Exclusive per-action claim so concurrent or repeated real executions cannot both send."""
    folder = _receipt_dir(marketing_root)
    folder.mkdir(parents=True, exist_ok=True)
    try:
        os.close(os.open(folder / f"{action_id}.claim", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        return True
    except FileExistsError:
        return False


def _release(marketing_root, action_id: str) -> None:
    (_receipt_dir(marketing_root) / f"{action_id}.claim").unlink(missing_ok=True)


def execute(action: dict, approval: dict, *, dry_run: bool = True, adapters=None, marketing_root=None, http=None,
            secret=None, now: datetime | None = None, validity: timedelta = DEFAULT_VALIDITY) -> dict:
    """Validate the approval and either describe (dry run) or perform the single approved provider action."""
    now = now or datetime.now(timezone.utc)
    registry = adapters if adapters is not None else ADAPTERS
    secret = secret or get_secret
    action_id = str(action.get("id") or "")
    kind = action.get("action_kind")
    adapter = registry.get(kind)
    request = bound_request(action)
    approval = approval if isinstance(approval, dict) else {}
    reasons = check_approval(action, approval, now=now, validity=validity)
    if adapter is None:
        reasons.append(f"no execution adapter for action_kind {kind!r}")
    elif not request:
        reasons.append("action has no provider_request")
    else:
        reasons.extend(adapter.validate(request, approval))
    if any(r.get("outcome") in BLOCKING_OUTCOMES for r in prior_attempts(marketing_root, action_id)):
        reasons.append("action was already executed or attempted (see receipts); a repeat needs a new action id")
    if not dry_run and marketing_root is None:
        reasons.append("real execution requires a marketing root for receipts and idempotency")
    secrets_used: list[str] = []
    if not dry_run and not reasons:
        missing = [name for name in getattr(adapter, "REQUIRES_ENV", ()) if not secret(name)[1]]
        if missing:
            reasons.append(f"missing environment variables: {', '.join(missing)}")
        secrets_used = [secret(name)[1] for name in getattr(adapter, "REQUIRES_ENV", ()) if secret(name)[1]]
    receipt = {"action_id": action_id, "action_kind": kind, "attempted_at": now.isoformat(), "dry_run": dry_run,
               "digest": authorization_digest(action), "approval_digest": approval.get("digest"),
               "granted_by": approval.get("granted_by"), "granted_at": approval.get("granted_at"),
               "scope": approval.get("scope"), "provider": getattr(adapter, "__name__", type(adapter).__name__).rsplit(".", 1)[-1] if adapter else None}
    if reasons:
        result = {"outcome": "refused", "reasons": reasons, "provider_ids": {}}
    elif dry_run:
        result = {"outcome": "dry_run", "reasons": [], "provider_ids": {},
                  "would_send": adapter.describe(request, approval)}
    elif not _claim(marketing_root, action_id):
        result = {"outcome": "refused", "reasons": ["action is already claimed by another execution attempt"],
                  "provider_ids": {}}
    else:
        try:
            response = adapter.run(request, approval, http=http or urllib_http, secret=secret)
            result = {"outcome": "executed", "reasons": [], "status": response.get("status"),
                      "provider_ids": response.get("provider_ids") or {}}
        except AdapterError as exc:
            result = {"outcome": "failed", "reasons": [str(exc)], "provider_ids": {}}
        except Exception as exc:  # network or unknown failure: the provider may have acted
            result = {"outcome": "uncertain", "provider_ids": {},
                      "reasons": [f"{type(exc).__name__}: {exc}", "provider may have acted; check the account before any new action"]}
    receipt.update(result)
    path = write_receipt(marketing_root, action_id, receipt, secrets_used)
    result = _scrub(result, secrets_used)
    if path is not None:
        result["receipt"] = str(path)
    return result


# --------------------------------------------------------------------------- CLI

def describe_plainly(action: dict) -> str:
    request = action.get("provider_request") or {}
    kind = action.get("action_kind")
    lines = [f"Action {action.get('id')}: {kind}", f"Intended result: {action.get('intended_result')}",
             f"Destination: {action.get('destination')}", f"Authorization basis: {action.get('authorization_basis')}"]
    if kind == "create_campaign":
        lines.append(f"Creates Meta campaign '{request.get('name')}' in ad account {request.get('ad_account_id')} with status "
                     f"PAUSED (never active) and spend cap {request.get('spend_cap')} (currency subunits).")
    elif kind == "schedule_post":
        channels = [(p.get("integration") or {}).get("id") for p in request.get("posts", []) if isinstance(p, dict)]
        lines.append(f"Schedules a Postiz post for {request.get('date')} on channels {channels}.")
    elif kind == "send_broadcast":
        target = "a TEST email to the founder address only" if request.get("test_send", True) is not False else \
            f"the FULL audience {request.get('audience_id')}"
        lines.append(f"Sends Resend email '{request.get('subject')}' from {request.get('from')} to {target}.")
    elif kind == "create_experiment":
        lines.append(f"Creates PostHog draft experiment '{request.get('name')}' with flag {request.get('feature_flag_key')}.")
    lines.append("Exact provider request:")
    lines.append(json.dumps(request, indent=2, sort_keys=True))
    return "\n".join(lines)


def cmd_approve(args) -> int:
    action = json.loads(Path(args.action).read_text(encoding="utf-8"))
    if is_agent_identity(args.by):
        print("refused: --by must be the founder's name, not an agent or tool identity", file=sys.stderr)
        return 2
    interactive = sys.stdin.isatty()
    if not interactive:
        expected = os.environ.get(PIN_ENV, "")
        if not (args.i_am_the_founder and expected and args.pin and hmac.compare_digest(args.pin, expected)):
            print("refused: approvals can only be created interactively by the founder (or with --i-am-the-founder "
                  f"and a --pin matching {PIN_ENV}, which agents must never set)", file=sys.stderr)
            return 2
    adapter = ADAPTERS.get(action.get("action_kind"))
    problems = ["no execution adapter for this action_kind"] if adapter is None else (
        ["action has no provider_request"] if not bound_request(action) else
        adapter.validate(bound_request(action), {"founder_email": args.founder_email}))
    if problems:
        print("refused: the action cannot be executed as written: " + "; ".join(problems), file=sys.stderr)
        return 2
    print(describe_plainly(action))
    digest = authorization_digest(action)
    print(f"\nDigest: {digest}")
    if interactive:
        answer = input(f"Type 'approve' to authorize exactly this {action.get('action_kind')} action: ").strip().lower()
        if answer != "approve":
            print("not approved", file=sys.stderr)
            return 1
    approval = {"action_id": action.get("id"), "digest": digest, "scope": action.get("action_kind"),
                "granted_by": args.by.strip(), "granted_at": datetime.now(timezone.utc).isoformat(),
                "method": "interactive" if interactive else "founder_pin"}
    if args.founder_email:
        approval["founder_email"] = args.founder_email
    out = Path(args.out) if args.out else Path(args.action).with_suffix(".approval.json")
    out.write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"approval written: {out}")
    return 0


def cmd_run(args) -> int:
    action = json.loads(Path(args.action).read_text(encoding="utf-8"))
    approval = json.loads(Path(args.approval).read_text(encoding="utf-8"))
    result = execute(action, approval, dry_run=not args.execute, marketing_root=Path(args.marketing_root),
                     validity=timedelta(days=args.validity_days))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["outcome"] in {"dry_run", "executed"} else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    approve = sub.add_parser("approve", help="founder only: approve one exact action")
    approve.add_argument("action")
    approve.add_argument("--by", required=True, help="the founder's name")
    approve.add_argument("--founder-email", help="founder's own address for Resend test sends")
    approve.add_argument("--out")
    approve.add_argument("--i-am-the-founder", action="store_true")
    approve.add_argument("--pin")
    run = sub.add_parser("run", help="validate and dry-run (default) or execute an approved action")
    run.add_argument("action")
    run.add_argument("--approval", required=True)
    run.add_argument("--marketing-root", required=True)
    run.add_argument("--execute", action="store_true", help="perform the external write (founder only)")
    run.add_argument("--validity-days", type=int, default=DEFAULT_VALIDITY.days)
    args = parser.parse_args(argv)
    return cmd_approve(args) if args.command == "approve" else cmd_run(args)


if __name__ == "__main__":
    raise SystemExit(main())
