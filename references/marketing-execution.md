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

External-delivery authorization in v2 binds recipient, destination, action kind, intended result, materials and authorization basis with `authorization_digest`. Generate it with `authorization_digest(action)` only when actual authorization is established; a digest is a consistency record, not proof the user gave consent. Changing those fields invalidates the prepared delivery. Changing expected placement source/target invalidates its observation; rewriting unrelated pitch materials preserves historical placement evidence. No pitch or listing sender is implemented; the only external marketing write path is the approval-bound executor below.

## Executing approved actions

`scripts/marketing/execute.py` is the only code path for an external marketing write: schedule a Postiz post (`schedule_post`), create a Meta campaign (`create_campaign`, always `PAUSED`, positive `spend_cap` required), send a Resend broadcast (`send_broadcast`, defaults to a test email to the approval's `founder_email`; a full audience send needs `test_send: false`), or create a PostHog draft experiment (`create_experiment`, no `start_date`). The `meta-ads` and `postiz` MCP servers are for reading only: their write tools are in `permissions.deny` (see `ad-platform-connections.md`). The action file carries `id`, `action_kind` and the exact `provider_request`; `authorization_digest` binds `provider_request`, so any change after approval invalidates it.

Approvals are SSH signatures from the founder; the agent can prepare a request and read the public key but cannot sign.

0. One-time founder setup in their own terminal: create a DEDICATED, passphrase-protected key (`ssh-keygen -t ed25519 -f ~/.ssh/marketing_approval`), never add it to ssh-agent, keep it out of the repo, and add `<principal> namespaces="marketing-approval" <public key>` to `~/.config/business-strategist/allowed_signers` under the real home directory (fixed path, no environment override). The agent runs as your OS user, so it could edit a file you own. Real separation needs a root-owned signers file (`sudo chown root:root` and `sudo chmod 0644` on the file, a root-owned directory) or an immutable one (`sudo chattr +i`). A user-owned read-only file (`chmod 0444`, directory `0700`) is accepted but is weaker. Execution is refused when the file is missing (with these steps), owned by anyone other than you or root, group/world-writable (file or directory), or when the file or its directory is a symlink into the repo or a temp directory. Verification uses only a root-owned `/usr/bin/ssh-keygen` or `/bin/ssh-keygen`, never `$PATH`.
1. `python3 scripts/marketing/execute.py approval-request <action.json> --by <principal> --marketing-root <marketing dir> [--founder-email <own address>] [--valid-days N]` validates the action, shows it in plain language and writes the exact message `digest|scope|granted_at|valid_until|action_id|granted_by|marketing_root|founder_email` (validity 7 days by default, at most 14, chosen before signing and not extendable afterwards) plus the `ssh-keygen -Y sign -n marketing-approval` command. An agent may run this step.
2. The founder signs that file in their own terminal, then `execute.py attach-signature <action.json> <message>.sig` verifies it and writes `<action>.approval.json`.
3. `python3 scripts/marketing/execute.py run <action.json> --approval <approval.json> --marketing-root <marketing dir>` re-verifies the signature (`ssh-keygen -Y verify`) and prints exactly what would be sent (dry run, no network). `--execute` performs the send and verifies the signature again.

Agents must never sign approvals, edit approval files, receipts or the allowed_signers file, or name themselves as the principal. Residual risk: the agent runs as your OS user. With a user-owned signers file it could add its own key and sign; only a root-owned or immutable signers file plus a passphrase-protected approval key kept out of ssh-agent separates the founder from the agent. Project permission rules deny the obvious command and file paths, but they match command text only. Deleting receipts weakens repeat-send protection; it does not enable an unapproved send.

Execution refuses unless the digest matches, `granted_by` is a human (agent/tool identities are rejected), the current time is before the signed `valid_until` (window at most 14 days), `scope` equals `action_kind`, the approval names this action id and marketing root, and no prior executed, failed or uncertain attempt or unfinished claim exists for that action id. Each attempt writes `receipts/<action-id>-<timestamp>.json` with outcome, digest and provider ids, never credentials. An `uncertain` outcome (network failure mid-request) blocks retries: check the provider account and use a new action id and approval. Activating a paused campaign or launching an experiment remains a manual founder step. Credentials come from the environment (`POSTIZ_BASE_URL`, `POSTIZ_API_KEY`, `META_ACCESS_TOKEN`, `RESEND_API_KEY`, `POSTHOG_HOST`, `POSTHOG_PERSONAL_API_KEY`, `POSTHOG_PROJECT_ID`).

For page planning use `scripts/marketing/keyword_map.py` and the optional `public_resource` section of content briefs. Preserve source bindings, original-versus-compiled contribution, public-use suitability and maintenance responsibility. The publisher validates keyword maps and `content-brief.json` resource evidence within the same transaction. Imported resources use the `public_resource` purpose and explicit applicability review.

Known placements use `verify_links.py`; capture directories are immutable and may be nested using `--evidence-root`. Public fetching validates and pins DNS addresses and every redirect, with bounded responses. Untrusted browser fallback is disabled. Failure/access blocks stay unknown; a 200 response without the expected anchor is absent, and a provider snapshot is a separate observation.

Opportunity artifacts use `opportunity.json` or `opportunities.json` (optionally nested under earned-media). Publication and resume revalidate their source bindings alongside maps and resource briefs, including source-only updates. Restore missing or corrupted placement evidence by staging the original digest-matching bytes; alternate contents still require a new observation/capture path. Template descendants are inert and cannot establish a placement. Sensitive source/target URLs are rejected before any observation is created.

For question-led content and creative comparison, apply [question tracking](customer-question-tracking.md) and [creative analysis](comparative-creative-analysis.md). Publish optional `customer-questions.json` and `creative-evidence.json` with bound captures through Marketing; source-only changes/resume revalidate use. These artifacts neither establish demand nor authorize posting.
