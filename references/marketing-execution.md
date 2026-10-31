# Marketing execution plan

Use `scripts/marketing/execution.py` with the optional `marketing/execution-plan.json` artifact bound in `workstream.json`; it validates and renders `execution-plan.md` and `owner-actions.md`. Publish changes with `publish_marketing_workstream()`. Do not create this artifact for a narrow copy edit.

## Ownership and completion

Turn a selected objective into small sequential actions owned by an `agent`, `owner` or `third_party`, each with `required_for_scope`. Reuse existing instructions and delegated authority for in-scope agent work; `commitment_state` is a resume record, not another approval checkpoint, and a proposal never becomes accepted on resume. `accepted` on an external action records the decision to pursue it, not a publisher's approval. Required actions stay incomplete until their own criterion is evidenced or an authorized scope change removes them; optional ideas never block. Never infer permission for a new send, payment, account connection or publication from an unrelated prior task.

Each owner or third-party packet contains the exact destination, current eligibility/rules, audience fit, ready text/assets, precise user step, fee, authorization basis, follow-up and observable completion criterion. Research targets and prepare materials before handing work to the owner; ask only for identity, private account access, first-hand facts or a material business choice.

For backlinks, verify the live source page, destination, redirects and anchor attributes after publication with `verify_links.py` / `link_observations.py`. A submitted pitch, directory form, favorable reply or response header is not a verified placement. Do not buy links, fabricate reviews, or claim ranking/uplift without observations. Version-2 placement evidence, `authorization_digest` binding and observation capture are enforced by `scripts/marketing/execution.py` and `link_observations.py`; a digest is a consistency record, not proof the user gave consent. No pitch or listing sender exists; the only external marketing write path is the approval-bound executor below.

## Measurement handoff

Use `scripts/marketing/observations.py` for supplied aggregate CSV/JSON exports. Never use lead names, emails, IDs or free-text bodies in the normalized view. Unknown and suppressed values stay distinct from zero; observed changes do not prove causality. With no export or account access, give the owner the exact setup/export steps and continue independent work.

## Executing approved actions

`scripts/marketing/execute.py` is the only code path for an external marketing write: schedule a Postiz post (`schedule_post`), create a Meta campaign (`create_campaign`, always `PAUSED`, positive `spend_cap` required), send a Resend broadcast (`send_broadcast`, test email to the approval's `founder_email` by default), or create a PostHog draft experiment (`create_experiment`). The `meta-ads` and `postiz` MCP servers are for reading only: their write tools are in `permissions.deny` (see `ad-platform-connections.md`). `authorization_digest` binds the exact `provider_request`, so any change after approval invalidates it.

Approvals are SSH signatures from the founder; the agent can prepare a request and read the public key but cannot sign.

0. One-time founder setup in their own terminal: create a dedicated, passphrase-protected key (`ssh-keygen -t ed25519 -f ~/.ssh/marketing_approval`), never add it to ssh-agent, keep it outside the repository, and add `<principal> namespaces="marketing-approval" <public key>` to `~/.config/business-strategist/allowed_signers`. The file and its directory must be root-owned and not group/world-writable (`sudo chown root:root` both, `sudo chmod 0644` the file, `sudo chmod 0755` the directory); execution refuses otherwise.
1. `python3 scripts/marketing/execute.py approval-request <action.json> --by <principal> --marketing-root <dir> [--founder-email <addr>] [--valid-days N]` shows the action in plain language and prints the `ssh-keygen -Y sign -n marketing-approval` command (validity at most 14 days). An agent may run this step.
2. The founder signs in their own terminal; `execute.py attach-signature <action.json> <message>.sig` writes `<action>.approval.json`.
3. `execute.py run <action.json> --approval <approval.json> --marketing-root <dir>` re-verifies and prints exactly what would be sent (dry run). `--execute` performs the send.

Agents must never sign approvals, edit approval files, receipts or the allowed_signers file, or name themselves as the principal. Residual risk: the agent runs as your OS user; only the root-owned signers file plus a passphrase-protected key kept out of ssh-agent separates founder from agent. Refusal conditions and receipts: `execute.py --help`. An `uncertain` outcome blocks retries: check the provider account and use a new action id and approval. Activating a paused campaign or launching an experiment remains a manual founder step. Credentials come from the environment, never from files the agent writes.

For page planning use `scripts/marketing/keyword_map.py` and the `public_resource` section of content briefs. For question-led content and creative comparison apply [question tracking](customer-question-tracking.md) and [creative analysis](comparative-creative-analysis.md); these artifacts neither establish demand nor authorize posting.

## Owner-action contract

Use when a deliverable surfaces work only the owner can do or decide. Apply with references/task-scope.md: include only decisions and actions relevant to the requested deliverable; never append recurring programs to narrow copy or execution work.

States: `proposed` (agent suggestion), `accepted` (owner agreed), `deferred`, `completed`. Only `accepted` actions and genuine blockers persist; a `proposed` action never recurs on resume as if adopted. Persist accepted actions in the active track's manifest `next_action` as `Owner action: {JSON}` lines via `scripts/monitoring/owner_actions.py` (`update_action`, `accepted_actions`; it neither writes files nor grants acceptance), and render full rows in that track's owner-actions.md. Do not overwrite the umbrella or unrelated next steps.

Each row: stable ID, action, area, why only the owner can supply it, cadence, effort, review point, expected customer outcome, completion definition, stop/change rule, state. Acceptance of a human-owned action must come from the user or existing explicit authorization; agent-owned work inside the selected scope needs no further acceptance. Never silently replace accepted work with a new proposal; completing one occurrence of recurring work does not authorize a new cadence. On resume reconcile accepted rows before recommending action; reserve `open_blockers` for actual dependencies.

Ask the owner only for unavailable firsthand facts, changed commercial commitments (prices, policies, guarantees) and actual decisions (publishes, sends, platform applications, spend); recheck verifiable facts yourself. Preserve publication/send authorization already granted in the session; do not re-ask. Identity-gated approvals (merchant programs, business-profile verification) are always owner actions.

## Local campaign operations

Shared code operates on explicit projects and campaigns; each Marketing root owns its connection definitions, context, reports and execution plan. Account connections, protected collectors, publishing and spending beyond the executor are not implemented.

For campaign design and tracking apply [journey activation and measurement](journey-activation-and-measurement.md); for asset inventory, provider onboarding and monitoring apply [ad platform connections](ad-platform-connections.md). Resolve `projects/<slug>` through its manifest. Start Marketing through `scripts/subprojects.py` only when the user selected that project and supplied its brief.

Commands (each `--help` is the procedure):

- `scripts/marketing/campaign.py setup|task`: campaign configuration and task events (accept, decline, snooze, complete). Configuration does not authorize external activity; unknown facts stay missing. Owner attestation is labelled, not independent verification.
- `scripts/marketing/review_cycle.py prepare|finalize`: import an aggregate export with a preset from `scripts/marketing/import_presets.py`, then publish the reviewed report. Two files are the same source in comparable windows; different platforms do not form a before/after experiment. First or non-comparable reports require `collect_more_data`. Keep raw exports in an access-controlled inbox and delete them when the user-selected retention period ends.
- `scripts/marketing/connections.py probe <gsc|ga4|google_ads>` then `search_feedback.py`: post-launch search review; `unconnected` is a gap with owner steps, not a zero, and the output is a proposal a human applies.
- `scripts/marketing/claims.py`: checks `[[claim:<id>]]` markers against `approved-claims.json`; it cannot detect unmarked or misleading claims, so editorial review remains required.
- `scripts/marketing/demo.py --out <empty-dir>`: synthetic offline demonstration; fixture data proves only local behavior.

### Verify tracking before launch

After the site gate and before any spend, keep a tracking plan (`schemas/tracking-plan.schema.json`) and run `python3 scripts/marketing/verify_tracking.py <plan.json> --source ga4|posthog` (aggregate-export flags: `--help`). Only `ready` permits paid launch; `unknown`, consent-gated zeros and exports that cannot show required properties are `not_ready`, never counted as observed. Configuration alone is not evidence; fire the events from the real production site first (WF-025).

### Observe changes before proposing more

Before recommending another bid, budget, targeting, creative or landing-page change, inspect recent interventions and record in `campaign-context.md` and the execution plan: hypothesis, affected IDs, actual implementation time/evidence, baseline, expected qualified-customer effect, observation window, next review and rollback condition. Task completion alone does not prove a live change occurred. Avoid overlapping interventions that make the question unanswerable; label before/after associations as observational. Zero new tasks is valid: use `continue` with a no-change rationale or `collect_more_data`. Broken tracking, disapprovals or a breached spending boundary may need urgent action within existing authority. Frequent recommendations and owner approval are not evidence of improvement.

The generated `website-brief.md` hands off to the website builder. A plan or tracking installation does not prove deployment, delivery or marketing improvement.
