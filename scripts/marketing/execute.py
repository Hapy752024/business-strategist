#!/usr/bin/env python3
"""Approval-bound marketing execution: the only path for an external marketing write.

``execute()`` refuses unless a founder approval matches the exact action digest, carries a valid SSH signature from
a key in the founder's allowed_signers file (outside the repo), names a human, is unexpired, is scoped to the action
kind and bound to this receipt store, and the action has not already been attempted. Dry run is the default; a real
send needs ``dry_run=False`` (CLI: ``run ... --execute``). Every attempt writes a secret-free receipt under
``<marketing-root>/receipts/``.

Approval flow: ``approval-request`` (agent may prepare) -> founder runs the printed ``ssh-keygen -Y sign`` in their
own terminal with a dedicated passphrase-protected key -> ``attach-signature`` builds the approval. Agents must never
sign, never edit approval files or receipts, and never touch the allowed_signers file.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import pwd
import stat
import re
import subprocess
import sys
import tempfile
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
MAX_VALIDITY = timedelta(days=14)
VERIFIER_CANDIDATES = (Path("/usr/bin/ssh-keygen"), Path("/bin/ssh-keygen"))
CLOCK_SKEW = timedelta(minutes=5)
AGENT_IDENTITIES = {"claude", "agent", "assistant", "subagent", "tool", "bot", "llm", "model", "system",
                    "codex", "gpt", "chatgpt", "gemini", "copilot", "automation", "script"}
ACTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PRINCIPAL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@+-]{0,127}$")
FINAL_OUTCOMES = {"executed", "uncertain", "failed"}
NAMESPACE = "marketing-approval"
SIGNERS_RELATIVE = Path(".config/business-strategist/allowed_signers")
SETUP_STEPS = (
    "Founder setup (run in your own terminal, never via an agent): "
    "1) ssh-keygen -t ed25519 -f ~/.ssh/marketing_approval -C marketing-approval  (set a passphrase; do NOT ssh-add it); "
    "2) mkdir -p ~/.config/business-strategist && "
    "echo \"<your-principal> namespaces=\\\"marketing-approval\\\" $(cat ~/.ssh/marketing_approval.pub)\" "
    ">> ~/.config/business-strategist/allowed_signers ; "
    "3) recommended, because the agent runs as your OS user: sudo chown root:root ~/.config/business-strategist/allowed_signers "
    "&& sudo chmod 0644 ~/.config/business-strategist/allowed_signers (or sudo chattr +i it); "
    "<your-principal> is the --by value you will use (letters, digits, . _ @ + -).")


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


def canonical_root(marketing_root) -> str:
    return str(Path(marketing_root).expanduser().resolve())


def signed_message(approval: dict) -> str:
    """digest|scope|granted_at|valid_until|action_id|granted_by|marketing_root|founder_email — the signed bytes."""
    fields = [approval.get(k) or "" for k in ("digest", "scope", "granted_at", "valid_until", "action_id", "granted_by",
                                              "marketing_root", "founder_email")]
    for value in fields:
        if not isinstance(value, str) or "|" in value or "\n" in value or "\r" in value:
            raise ValueError("approval fields must be strings without '|' or newlines")
    return "|".join(fields)


def default_signers_path() -> Path:
    """Fixed location under the real home directory (passwd entry, not $HOME); no environment override."""
    return Path(pwd.getpwuid(os.getuid()).pw_dir) / SIGNERS_RELATIVE


def allowed_signers_path(override=None) -> Path:
    """``override`` exists only for in-process tests; the CLI never exposes it."""
    return Path(override) if override is not None else default_signers_path()


def _untrusted_locations() -> list[Path]:
    places = [ROOT, Path(tempfile.gettempdir()), Path("/tmp"), Path("/var/tmp"), Path("/dev/shm")]
    return [p.resolve() for p in places if p.exists()]


def _stat(path):
    return os.stat(path)


def _owner_mode_problems(candidate: Path, allowed_uids: set[int]) -> list[str]:
    try:
        info = _stat(candidate)
    except OSError:
        return [f"cannot stat {candidate}"]
    problems = []
    if info.st_uid not in allowed_uids:
        problems.append(f"{candidate} is not owned by " + ("root" if allowed_uids == {0} else "the current user or root"))
    if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        problems.append(f"{candidate} is group- or world-writable")
    return problems


def _inside_untrusted(target: Path) -> bool:
    return any(target == place or place in target.parents for place in _untrusted_locations())


def signers_file_problems(path: Path) -> list[str]:
    """StrictModes-like checks: owned by the current user or root, not group/world-writable, and neither the file
    nor its directory is a symlink into the repository or a temp directory."""
    if (path.is_symlink() or path.parent.is_symlink()) and _inside_untrusted(path.resolve()):
        return [f"allowed_signers {path} (or its directory) is a symlink into the repository or a temp directory; refusing"]
    if not path.is_file():
        return [f"no allowed_signers file at {path}; every execution is refused until the founder sets it up. {SETUP_STEPS}"]
    problems = []
    for candidate in dict.fromkeys([path, path.resolve(), path.parent, path.resolve().parent]):
        problems.extend(_owner_mode_problems(candidate, {os.getuid(), 0}))
    return [f"allowed_signers permissions are unsafe: {p}; use a root-owned file (sudo chown root:root, "
            "sudo chmod 0644) or a user-owned read-only one (chmod 0444, directory 0700)" for p in problems]


def verifier_path() -> tuple[Path | None, list[str]]:
    """Pinned ssh-keygen: fixed system locations only, root-owned and not group/world-writable. $PATH is never used."""
    problems = []
    for candidate in VERIFIER_CANDIDATES:
        if not candidate.exists():
            continue
        real = candidate.resolve()
        found = [p for c in dict.fromkeys([real, real.parent]) for p in _owner_mode_problems(c, {0})]
        if not found:
            return real, []
        problems.extend(found)
    return None, [f"no trusted ssh-keygen verifier ({', '.join(map(str, VERIFIER_CANDIDATES))}); refusing"
                  + (f": {'; '.join(problems)}" if problems else "")]


def verify_signature(approval: dict, *, allowed_signers=None) -> list[str]:
    signers = allowed_signers_path(allowed_signers)
    unsafe = signers_file_problems(signers)
    if unsafe:
        return unsafe
    signature = approval.get("signature")
    if not isinstance(signature, str) or "BEGIN SSH SIGNATURE" not in signature:
        return ["approval is not signed (an SSH signature from the founder's approval key is required)"]
    if not PRINCIPAL.match(str(approval.get("granted_by") or "")):
        return ["granted_by must be the founder's allowed_signers principal (letters, digits, . _ @ + -)"]
    try:
        message = signed_message(approval)
    except ValueError as exc:
        return [str(exc)]
    verifier, problems = verifier_path()
    if verifier is None:
        return problems
    with tempfile.TemporaryDirectory() as folder:
        sig = Path(folder) / "approval.sig"
        sig.write_text(signature, encoding="utf-8")
        try:
            proc = subprocess.run([str(verifier), "-Y", "verify", "-f", str(signers), "-I", approval["granted_by"],
                                   "-n", NAMESPACE, "-s", str(sig)], input=message.encode(), capture_output=True,
                                  timeout=30, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
        except (OSError, subprocess.TimeoutExpired) as exc:
            return [f"signature verification unavailable ({type(exc).__name__}); refusing"]
    if proc.returncode != 0:
        return ["approval signature is invalid for this signer, namespace or exact approval message"]
    return []


def bound_request(action: dict) -> dict:
    """Adapters only see the digest-bound provider request, so nothing unapproved can be sent."""
    request = action.get("provider_request")
    return json.loads(json.dumps(request)) if isinstance(request, dict) else {}


def check_approval(action: dict, approval: dict, *, now: datetime, marketing_root=None,
                   allowed_signers=None) -> list[str]:
    reasons = []
    if not isinstance(approval, dict):
        return ["approval is missing"]
    if not ACTION_ID.match(str(action.get("id") or "")):
        reasons.append("action id is missing or not a safe identifier")
    if approval.get("action_id") != action.get("id"):
        reasons.append("approval action_id does not match the action id")
    if marketing_root is None:
        reasons.append("a marketing root (receipt store) is required")
    elif approval.get("marketing_root") != canonical_root(marketing_root):
        reasons.append("approval is bound to a different marketing root (receipt store)")
    if not approval.get("digest") or not hmac.compare_digest(str(approval.get("digest")), authorization_digest(action)):
        reasons.append("approval digest does not match the exact action (changed after approval or never approved)")
    if is_agent_identity(approval.get("granted_by")):
        reasons.append("granted_by must name the human founder; agent/tool identities cannot approve")
    granted = _parse_time(approval.get("granted_at")) if approval.get("granted_at") else None
    if granted is None:
        reasons.append("approval granted_at is missing or invalid")
    elif granted > now + CLOCK_SKEW:
        reasons.append("approval granted_at is in the future")
    valid_until = _parse_time(approval.get("valid_until")) if approval.get("valid_until") else None
    if valid_until is None:
        reasons.append("approval valid_until is missing or invalid")
    elif granted is not None and not (granted < valid_until <= granted + MAX_VALIDITY):
        reasons.append(f"approval validity window must be positive and at most {MAX_VALIDITY.days} days")
    elif now > valid_until:
        reasons.append("approval expired (past its signed valid_until)")
    if approval.get("scope") != action.get("action_kind"):
        reasons.append(f"approval scope {approval.get('scope')!r} does not match action_kind {action.get('action_kind')!r}")
    if action.get("execution_status") in {"submitted", "verified"}:
        reasons.append("action is already executed according to its execution_status")
    reasons.extend(verify_signature(approval, allowed_signers=allowed_signers))
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
    for secret in sorted({s for s in secrets if s and len(s) >= 8 and not s.isdigit()}, key=len, reverse=True):
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


def _claim(marketing_root, action_id: str, now: datetime) -> dict | None:
    """Exclusive per-action claim (timestamp + pid) so repeated or concurrent real executions cannot both send.

    Returns None when the claim was taken, else the existing claim's contents. Claims are never released.
    """
    folder = _receipt_dir(marketing_root)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{action_id}.claim"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"claimed_at": None, "pid": None}
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"action_id": action_id, "claimed_at": now.isoformat(), "pid": os.getpid()}, handle)
    return None


def _existing_claim(marketing_root, action_id: str):
    folder = _receipt_dir(marketing_root)
    path = None if folder is None or not ACTION_ID.match(action_id or "") else folder / f"{action_id}.claim"
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"claimed_at": None, "pid": None}


def execute(action: dict, approval: dict, *, dry_run: bool = True, adapters=None, marketing_root=None, http=None,
            secret=None, now: datetime | None = None,
            allowed_signers=None) -> dict:
    """Validate the signed approval and either describe (dry run) or perform the single approved provider action."""
    now = now or datetime.now(timezone.utc)
    registry = adapters if adapters is not None else ADAPTERS
    secret = secret or get_secret
    action_id = str(action.get("id") or "")
    kind = action.get("action_kind")
    adapter = registry.get(kind)
    request = bound_request(action)
    approval = approval if isinstance(approval, dict) else {}
    reasons = check_approval(action, approval, now=now, marketing_root=marketing_root,
                             allowed_signers=allowed_signers)
    if adapter is None:
        reasons.append(f"no execution adapter for action_kind {kind!r}")
    elif not request:
        reasons.append("action has no provider_request")
    else:
        reasons.extend(adapter.validate(request, approval, now=now))
    if any(r.get("outcome") in FINAL_OUTCOMES for r in prior_attempts(marketing_root, action_id)):
        reasons.append("action was already executed or attempted (see receipts); a repeat needs a new action id")
    stale_claim = None
    if not reasons:
        stale_claim = _existing_claim(marketing_root, action_id)
    secrets_used: list[str] = []
    if not dry_run and not reasons and stale_claim is None:
        missing = [name for name in getattr(adapter, "REQUIRES_ENV", ()) if not secret(name)[1]]
        if missing:
            reasons.append(f"missing environment variables: {', '.join(missing)}")
        secrets_used = [secret(name)[1] for name in getattr(adapter, "REQUIRES_ENV", ()) if secret(name)[1]]
    receipt = {"action_id": action_id, "action_kind": kind, "attempted_at": now.isoformat(), "dry_run": dry_run,
               "digest": authorization_digest(action), "approval_digest": approval.get("digest"),
               "granted_by": approval.get("granted_by"), "granted_at": approval.get("granted_at"),
               "scope": approval.get("scope"), "provider": getattr(adapter, "__name__", type(adapter).__name__).rsplit(".", 1)[-1] if adapter else None}
    uncertain_claim = {"outcome": "uncertain", "provider_ids": {}, "reasons": [
        f"an execution claim exists without a final receipt (claimed_at {stale_claim.get('claimed_at') if stale_claim else None}, "
        f"pid {stale_claim.get('pid') if stale_claim else None}); the provider may have acted; check the account "
        "and use a new action id and approval"]}
    if reasons:
        result = {"outcome": "refused", "reasons": reasons, "provider_ids": {}}
    elif stale_claim is not None:
        result = uncertain_claim
    elif dry_run:
        result = {"outcome": "dry_run", "reasons": [], "provider_ids": {},
                  "would_send": adapter.describe(request, approval)}
    else:
        stale_claim = _claim(marketing_root, action_id, now)
        if stale_claim is not None:  # lost a race with a concurrent attempt
            result = {"outcome": "refused", "provider_ids": {},
                      "reasons": ["action was claimed by a concurrent execution attempt"]}
        else:
            try:
                response = adapter.run(request, approval, http=http or urllib_http, secret=secret)
                result = {"outcome": "executed", "reasons": [], "status": response.get("status"),
                          "provider_ids": response.get("provider_ids") or {}}
            except AdapterError as exc:
                result = {"outcome": "uncertain" if exc.uncertain else "failed", "reasons": [str(exc)],
                          "provider_ids": exc.provider_ids}
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
        lines.extend(f"Note: {note}" for note in meta_ads.notes(request))
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


def _validate_for_request(action: dict, approval: dict) -> list[str]:
    adapter = ADAPTERS.get(action.get("action_kind"))
    if adapter is None:
        return ["no execution adapter for this action_kind"]
    if not bound_request(action):
        return ["action has no provider_request"]
    problems = adapter.validate(bound_request(action), approval, now=datetime.now(timezone.utc))
    if is_agent_identity(approval.get("granted_by")) or not PRINCIPAL.match(approval.get("granted_by") or ""):
        problems.append("--by must be the founder's allowed_signers principal, not an agent or tool identity")
    if not ACTION_ID.match(str(action.get("id") or "")):
        problems.append("action id is missing or not a safe identifier")
    return problems


def cmd_approval_request(args) -> int:
    """Prepare (not grant) an approval: the founder signs the written message in their own terminal."""
    action_path = Path(args.action)
    action = json.loads(action_path.read_text(encoding="utf-8"))
    if not 1 <= args.valid_days <= MAX_VALIDITY.days:
        print(f"refused: --valid-days must be between 1 and {MAX_VALIDITY.days}", file=sys.stderr)
        return 2
    granted = datetime.now(timezone.utc)
    request = {"action_id": action.get("id"), "digest": authorization_digest(action), "scope": action.get("action_kind"),
               "granted_by": args.by.strip(), "granted_at": granted.isoformat(),
               "valid_until": (granted + timedelta(days=args.valid_days)).isoformat(),
               "marketing_root": canonical_root(args.marketing_root), "founder_email": args.founder_email or ""}
    problems = _validate_for_request(action, request)
    try:
        message = signed_message(request)
    except ValueError as exc:
        problems.append(str(exc))
    if problems:
        print("refused: " + "; ".join(problems), file=sys.stderr)
        return 2
    request_path = action_path.with_suffix(".approval-request.json")
    message_path = action_path.with_suffix(".approval-message.txt")
    request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    message_path.write_text(message, encoding="utf-8")
    print(describe_plainly(action))
    print(f"\nApproval valid until {request['valid_until']} (signed; cannot be extended after signing).")
    print(f"Approval message (exact bytes in {message_path}):\n{message}\n")
    print("Founder: review the action above, then run in YOUR OWN terminal (never through an agent):")
    print(f"  ssh-keygen -Y sign -f ~/.ssh/marketing_approval -n {NAMESPACE} {message_path}")
    print(f"then: python3 scripts/marketing/execute.py attach-signature {action_path} {message_path}.sig")
    if not allowed_signers_path().is_file():
        print(f"\nNote: {allowed_signers_path()} does not exist yet. {SETUP_STEPS}")
    return 0


def cmd_attach_signature(args) -> int:
    action_path = Path(args.action)
    action = json.loads(action_path.read_text(encoding="utf-8"))
    request_path = Path(args.request) if args.request else action_path.with_suffix(".approval-request.json")
    approval = json.loads(request_path.read_text(encoding="utf-8"))
    approval["signature"] = Path(args.signature).read_text(encoding="utf-8")
    problems = []
    if approval.get("digest") != authorization_digest(action) or approval.get("action_id") != action.get("id"):
        problems.append("the action changed since the approval request; prepare and sign a new request")
    problems.extend(verify_signature(approval))
    if problems:
        print("refused: " + "; ".join(problems), file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else action_path.with_suffix(".approval.json")
    out.write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"signed approval written: {out}")
    return 0


def cmd_run(args) -> int:
    action = json.loads(Path(args.action).read_text(encoding="utf-8"))
    approval = json.loads(Path(args.approval).read_text(encoding="utf-8"))
    result = execute(action, approval, dry_run=not args.execute, marketing_root=Path(args.marketing_root))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["outcome"] in {"dry_run", "executed"} else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("approval-request", help="prepare the exact message the founder signs")
    prepare.add_argument("action")
    prepare.add_argument("--by", required=True, help="the founder's allowed_signers principal")
    prepare.add_argument("--marketing-root", required=True, help="receipt store bound into the approval")
    prepare.add_argument("--founder-email", help="founder's own address for Resend test sends")
    prepare.add_argument("--valid-days", type=int, default=DEFAULT_VALIDITY.days,
                         help=f"approval validity the founder signs (1-{MAX_VALIDITY.days} days)")
    attach = sub.add_parser("attach-signature", help="build the approval from the founder's SSH signature")
    attach.add_argument("action")
    attach.add_argument("signature")
    attach.add_argument("--request")
    attach.add_argument("--out")
    run = sub.add_parser("run", help="validate and dry-run (default) or execute a signed, approved action")
    run.add_argument("action")
    run.add_argument("--approval", required=True)
    run.add_argument("--marketing-root", required=True)
    run.add_argument("--execute", action="store_true", help="perform the external write")
    args = parser.parse_args(argv)
    return {"approval-request": cmd_approval_request, "attach-signature": cmd_attach_signature,
            "run": cmd_run}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
