"""Validate and render the optional, hash-bound Marketing execution plan."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from scripts.marketing import link_observations as links
except ModuleNotFoundError:
    from marketing import link_observations as links

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/marketing-execution.schema.json").read_text())


def authorization_digest(action: dict) -> str:
    """Bind external authorization to the exact prepared action, not a campaign."""
    payload = {key: action.get(key) for key in ('action_kind', 'recipient', 'destination',
               'intended_result', 'prepared_materials', 'authorization_basis')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def invalidate_changed_action(old: dict, action: dict) -> None:
    if not old:
        return
    if action.get('action_kind') == 'verify_placement':
        changed = any(old.get(k) != action.get(k) for k in ('source_url', 'target_url', 'action_kind'))
    else:
        changed = old.get('prepared_materials', []) != action.get('prepared_materials', []) or any(
            old.get(k) != action.get(k) for k in ('recipient', 'destination', 'intended_result', 'action_kind', 'authorization_basis'))
    if changed:
        for key in ('verification', 'result', 'outcome_review'):
            action[key] = None
        for key in ('observation', 'authorization_digest'):
            action.pop(key, None)
        action['execution_status'] = 'prepared'
        if action.get('commitment_state') == 'completed':
            action['commitment_state'] = 'accepted'


def validate(document: dict, base: Path | None = None, staged: dict | None = None) -> list[str]:
    errors = [e.message for e in Draft202012Validator(SCHEMA).iter_errors(document)]
    if errors:
        return errors
    actions = {a.get("id"): a for a in document.get("actions", []) if isinstance(a, dict)}
    if len(actions) != len(document.get("actions", [])):
        errors.append("action IDs must be unique")
    visiting, visited = set(), set()
    def visit(ident):
        if ident in visiting:
            errors.append(f"dependency cycle includes {ident}"); return
        if ident in visited or ident not in actions: return
        visiting.add(ident)
        for dep in actions[ident].get("dependencies", []): visit(dep)
        visiting.remove(ident); visited.add(ident)
    for ident in actions: visit(ident)
    for action in actions.values():
        for dependency in action.get("dependencies", []):
            if dependency not in actions:
                errors.append(f"{action.get('id')}: unknown dependency {dependency}")
        if action.get("commitment_state") == "completed" and action.get("execution_status") not in {"submitted", "verified", "failed"}:
            errors.append(f"{action.get('id')}: completed commitment needs a completed execution status")
        placement = document.get('schema_version') == 2 and action.get('action_kind') == 'verify_placement'
        if placement:
            for field in ('source_url', 'target_url'):
                try:
                    links.url_key(action.get(field, ''))
                except ValueError:
                    errors.append(f"{action['id']}: placement requires {field}")
            if action.get('execution_status') == 'verified':
                if not action.get('observation'):
                    errors.append(f"{action['id']}: placement requires captured observation")
                else:
                    errors.extend(f"{action['id']}: observation: {e}" for e in links.validate_binding(
                        action['observation'], base, staged, action.get('source_url', ''), action.get('target_url', '')))
        if action.get("execution_status") == "verified" and not placement and not action.get("verification"):
            errors.append(f"{action.get('id')}: verified status needs verification evidence")
        if document.get('schema_version') == 2 and action.get('action_kind') in {'send_pitch', 'submit_listing'}:
            if not action.get('recipient') or not action.get('prepared_materials'):
                errors.append(f"{action['id']}: external delivery needs recipient and prepared materials")
            if action.get('execution_status') in {'submitted', 'verified'} and action.get('authorization_digest') != authorization_digest(action):
                errors.append(f"{action['id']}: external delivery authorization is missing or changed")
        if action.get("actor") == "third_party" or action.get("destination"):
            required_packet_fields = ("destination", "eligibility_checked_at", "audience_fit", "authorization_basis", "follow_up")
            for field in required_packet_fields:
                if not str(action.get(field) or "").strip(): errors.append(f"{action.get('id')}: external action requires {field}")
            if action.get("actor") == "owner" and not str(action.get("user_step") or "").strip():
                errors.append(f"{action.get('id')}: owner platform action requires a precise user_step")
            if action.get("fee") is None:
                errors.append(f"{action.get('id')}: external action must record a fee or explicitly state none")
        for item in action.get("prepared_materials", []):
            if base is not None:
                try:
                    links.bound_bytes(item, base, staged)
                except (OSError, ValueError):
                    errors.append(f"{action.get('id')}: prepared material missing, changed or out of scope: {item['path']}")
    return errors


def scope_complete(document: dict, base: Path | None = None, staged: dict | None = None) -> bool:
    """Required action steps must have observed criteria; optional proposals do not block."""
    if validate(document, base, staged):
        return False
    actions = {action.get("id"): action for action in document.get("actions", [])}
    def dependency_complete(ident: str) -> bool:
        dependency = actions.get(ident, {})
        return (dependency.get("commitment_state") == "completed" and
                dependency.get("execution_status") in {"submitted", "verified"})
    return all(not action.get("required_for_scope") or
               (action.get("commitment_state") == "completed" and action.get("execution_status") == "verified" and
                bool(action.get("verification") or (document.get('schema_version') == 2 and action.get('action_kind') == 'verify_placement' and action.get('observation'))) and
                all(dependency_complete(ident) for ident in action.get("dependencies", [])))
               for action in document.get("actions", []))


def render(document: dict) -> tuple[str, str]:
    rows = ["# Marketing execution plan", "", f"Scope: {document['scope']}", ""]
    owners = ["# Owner actions", ""]
    actions = {action["id"]: action for action in document.get("actions", [])}
    for action in document.get("actions", []):
        dependencies = action.get("dependencies", [])
        blocked_by = [ident for ident in dependencies
                      if not (actions.get(ident, {}).get("commitment_state") == "completed" and
                              actions.get(ident, {}).get("execution_status") in {"submitted", "verified"})]
        rows += [f"## {action['id']} — {action['objective']}", "",
                 f"- Actor: {action['actor']}; commitment: {action['commitment_state']}; progress: {action['execution_status']}",
                 f"- Required for selected scope: {'yes' if action['required_for_scope'] else 'no'}",
                 f"- Next step: {action.get('next_step') or 'none'}",
                 f"- Completion: {action['completion_criterion']}"]
        if document.get('schema_version') == 1 and action.get('verification'):
            rows.append('- Evidence contract: legacy verification; not a captured backlink observation')
        if action.get('observation'):
            rows.append(f"- Placement observation: {action['observation']['path']} (SHA-256: {action['observation']['sha256']})")
        if action.get("prepared_materials"):
            rows.append("- Prepared materials:")
            rows.extend(f"  - [{Path(item['path']).name}]({item['path']}) (SHA-256: `{item['sha256']}`)"
                        for item in action["prepared_materials"])
        if blocked_by:
            rows.append("- Blocked until verified: " + ", ".join(blocked_by))
        for field, label in (("destination", "Destination"), ("eligibility_checked_at", "Eligibility checked"),
                             ("audience_fit", "Audience fit"), ("user_step", "User step"), ("fee", "Fee"),
                             ("authorization_basis", "Authorization"), ("follow_up", "Follow-up"), ("verification", "Verification"),
                             ("result", "Result"), ("outcome_review", "Outcome review")):
            if action.get(field): rows.append(f"- {label}: {action[field]}")
        rows.append("")
        if action["actor"] == "owner" and action["commitment_state"] == "accepted" and action["execution_status"] in {"awaiting_owner", "prepared"}:
            destination = f" Destination: {action['destination']}." if action.get("destination") else ""
            state = ("blocked by " + ", ".join(blocked_by)) if blocked_by else action["execution_status"]
            owners += [f"- [{action['id']}] {action['objective']} — {action.get('user_step') or action.get('next_step') or 'see execution plan'}; status: {state}.{destination}"]
            owners.extend(f"  - Prepared material: [{Path(item['path']).name}]({item['path']}) (SHA-256: `{item['sha256']}`)"
                          for item in action.get("prepared_materials", []))
    return "\n".join(rows), "\n".join(owners) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    document = json.loads(args.plan.read_text(encoding="utf-8"))
    errors = validate(document, args.base)
    if errors:
        parser.error("; ".join(errors))
    if args.out:
        execution, owner = render(document)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "execution-plan.md").write_text(execution, encoding="utf-8")
        (args.out / "owner-actions.md").write_text(owner, encoding="utf-8")
    print(json.dumps({"valid": True, "actions": len(document["actions"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
