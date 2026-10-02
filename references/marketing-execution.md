# Marketing execution plan

Use `scripts/marketing/execution.py` with the optional `marketing/execution-plan.json` artifact bound in `workstream.json`. The helper validates and renders `execution-plan.md` and `owner-actions.md`; publish artifact changes with `publish_marketing_workstream()` so artifact and hash binding advance together. Do not create this artifact for a narrow copy edit.

## Ownership and completion

Turn a selected objective into small sequential actions owned by an `agent`, `owner`, or `third_party`. Reuse existing user instructions and delegated authority for in-scope agent work; `commitment_state` is a resume record, not another approval checkpoint. For an external action, `accepted` records the decision to pursue it; it does not mean a publisher approved it.

Set `required_for_scope` for each action. Optional ideas do not block the selected deliverable. Required actions remain incomplete until their own criterion is evidenced, or an authorized scope change removes them. A user's send/post/account step can finish while a publisher review or placement remains pending. Keep `commitment_state` separate from `execution_status`; a proposal never becomes accepted on resume. Recheck hashes when prepared materials change and invalidate only affected verification. Never infer permission for a new send, payment, account connection, or publication from an unrelated prior task.

Each owner or third-party packet should contain the exact destination, current eligibility/rules, audience fit, ready text/assets, precise user step, fee, authorization basis, follow-up, and observable completion criterion. Research candidate targets and prepare the materials before handing work to the owner. Ask only for identity, private account access, first-hand facts, or a material business choice the agent cannot supply. Preserve unrelated accepted actions and existing authorization on update.

For backlinks, verify the live source page, destination, redirects and anchor attributes after publication. A submitted pitch, directory form, favorable reply, or response header is not a verified placement. Record publisher rejection and an evidence-based alternative. Do not buy links, fabricate reviews, or claim ranking/uplift without observations.

## Measurement handoff

Use `scripts/marketing/observations.py` for supplied local aggregate CSV/JSON exports. Explicitly map the fields and preserve property, source, window, timezone, metric/unit, availability, export date, optional denominator and input digest. Never use lead names, emails, IDs or free-text bodies in the normalized view. Unknown and suppressed values stay distinct from zero. `compare()` requires matching property, source, metric, dimensions, timezone and equal window duration; observed changes do not prove causality. `decision_record()` binds baseline and follow-up digests to an action, expected effect, applied change date, confounders, limitations and next decision. A changed export makes the prior record stale. See the synthetic, non-production example in `fixtures/marketing/demo-baseline.csv`, `demo-followup.csv`, and `demo-decision.json`; the matched change is not a business result. With no export or account access, give the owner the exact setup/export steps and continue independent work.

## Example action template

```json
{
  "id": "directory-review",
  "objective": "Submit a relevant, eligible business listing",
  "evidence": ["verified directory audience overlaps the target buyer"],
  "actor": "owner",
  "dependencies": [],
  "prepared_materials": [],
  "destination": "exact listing URL",
  "eligibility_checked_at": "YYYY-MM-DD",
  "audience_fit": "reason supported by evidence",
  "user_step": "sign in, review prepared copy, submit",
  "fee": null,
  "authorization_basis": "selected listing task",
  "follow_up": "check listing status after stated review period",
  "next_step": "submit prepared listing",
  "completion_criterion": "public listing page resolves and matches submitted destination",
  "commitment_state": "accepted",
  "execution_status": "awaiting_owner",
  "required_for_scope": false,
  "verification": null,
  "result": null,
  "outcome_review": null
}
```
