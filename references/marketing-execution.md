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

## Version 2 placement evidence

New earned-media actions use `schema_version: 2`, `action_kind` and `intended_result`. Kinds distinguish generic work, prepare_packet, submit_listing, send_pitch and verify_placement. A verified placement requires source_url, target_url and an `observation: {path, sha256}` binding. The observation contains a capture binding, actual anchors/rel attributes, method, URLs, redirects and checked_at. Both paths are relative to the Marketing root. `scripts/marketing/link_observations.py` re-parses the retained HTML/DOM and checks the exact source/target and digests; a positive reply or authored verification string cannot complete this action. Publication validates staged bytes before commit and persisted bytes on resume. A rootless structural check cannot certify placement completion.

Version-1 plans remain readable and render legacy verification explicitly. They are not automatically converted to verified backlinks. Preparation and submission can finish separately from a required public placement. Optional proposed opportunities do not block the selected scope.

External-delivery authorization in v2 binds recipient, destination, action kind, intended result, materials and authorization basis with `authorization_digest`. Generate it with `authorization_digest(action)` only when actual authorization is established; a digest is a consistency record, not proof the user gave consent. Changing those fields invalidates the prepared delivery. Changing expected placement source/target invalidates its observation; rewriting unrelated pitch materials preserves historical placement evidence. No sender is implemented.

For page planning use `scripts/marketing/keyword_map.py` and the optional `public_resource` section of content briefs. Preserve source bindings, original-versus-compiled contribution, public-use suitability and maintenance responsibility. The publisher validates keyword maps and `content-brief.json` resource evidence within the same transaction. Imported resources use the `public_resource` purpose and explicit applicability review.

Known placements use `verify_links.py`; capture directories are immutable and may be nested using `--evidence-root`. Public fetching validates and pins DNS addresses and every redirect, with bounded responses. Untrusted browser fallback is disabled. Failure/access blocks stay unknown; a 200 response without the expected anchor is absent, and a provider snapshot is a separate observation.

Opportunity artifacts use `opportunity.json` or `opportunities.json` (optionally nested under earned-media). Publication and resume revalidate their source bindings alongside maps and resource briefs, including source-only updates. Restore missing or corrupted placement evidence by staging the original digest-matching bytes; alternate contents still require a new observation/capture path. Template descendants are inert and cannot establish a placement. Sensitive source/target URLs are rejected before any observation is created.

For question-led content and creative comparison, apply [question tracking](customer-question-tracking.md) and [creative analysis](comparative-creative-analysis.md). Publish optional `customer-questions.json` and `creative-evidence.json` with bound captures through Marketing; source-only changes/resume revalidate use. These artifacts neither establish demand nor authorize posting.
