"""Resend: broadcast to an audience (segment), defaulting to a test send to the founder only.

Docs: https://resend.com/docs/api-reference/broadcasts/create-broadcast ,
https://resend.com/docs/api-reference/broadcasts/send-broadcast , https://resend.com/docs/api-reference/emails/send-email
Test send: POST https://api.resend.com/emails to the founder address recorded in the approval.
Full send (only when ``test_send`` is explicitly false): POST /broadcasts with ``send: false``, then
POST /broadcasts/{id}/send. Resend renamed audiences to segments; ``audience_id`` is sent as ``segment_id``.
"""
from __future__ import annotations

from . import AdapterError, first_id, require_secret

REQUIRES_ENV = ("RESEND_API_KEY",)
API = "https://api.resend.com"


def _test_send(request: dict) -> bool:
    return request.get("test_send", True) is not False


def validate(request: dict, approval: dict, now=None) -> list[str]:
    errors = [f"resend broadcast requires {f}" for f in ("audience_id", "from", "subject", "html")
              if not str(request.get(f) or "").strip()]
    if "test_send" in request and not isinstance(request["test_send"], bool):
        errors.append("resend test_send must be a boolean")
    if _test_send(request) and "@" not in str(approval.get("founder_email") or ""):
        errors.append("resend test send requires the founder's own address (founder_email) in the approval")
    if request.get("scheduled_at"):
        errors.append("resend scheduled_at is not supported by this adapter; schedule manually")
    return errors


def describe(request: dict, approval: dict) -> list[dict]:
    if _test_send(request):
        return [{"method": "POST", "url": f"{API}/emails",
                 "body": {"from": request["from"], "to": [approval["founder_email"]], "subject": f"[TEST] {request['subject']}",
                          "html": request["html"]}}]
    create = {"segment_id": request["audience_id"], "from": request["from"], "subject": request["subject"],
              "html": request["html"], "send": False}
    if request.get("name"):
        create["name"] = request["name"]
    return [{"method": "POST", "url": f"{API}/broadcasts", "body": create},
            {"method": "POST", "url": f"{API}/broadcasts/{{broadcast_id}}/send", "body": {}}]


def run(request: dict, approval: dict, *, http, secret) -> dict:
    headers = {"Authorization": f"Bearer {require_secret(secret, 'RESEND_API_KEY')}"}
    steps = describe(request, approval)
    if _test_send(request):
        response = http("POST", steps[0]["url"], headers, steps[0]["body"])
        return {"status": "test_sent", "provider_ids": {"email_id": first_id(response, "id")}}
    created = http("POST", steps[0]["url"], headers, steps[0]["body"])
    broadcast_id = first_id(created, "id")
    if not broadcast_id:
        raise AdapterError("resend broadcast creation returned no id; nothing was sent")
    try:
        http("POST", f"{API}/broadcasts/{broadcast_id}/send", headers, {})
    except Exception as exc:  # the draft exists; keep its id in the receipt
        raise AdapterError(f"resend send failed after draft broadcast creation ({type(exc).__name__})",
                           provider_ids={"draft_broadcast_id": broadcast_id}, uncertain=True) from None
    return {"status": "broadcast_sent", "provider_ids": {"broadcast_id": broadcast_id}}
