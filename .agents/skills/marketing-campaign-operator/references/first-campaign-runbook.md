# First-campaign runbook

Ordered path from validated positioning to one organic post, one paused paid test and a week-1 review. Do the steps in order. A step is done only when its observable criterion holds; otherwise stop and report the blocker.

**What the agent can do:** research, draft, validate, build and prepare approval requests, and dry-run. **What it cannot do:** sign approvals, edit the signers file, receipts or approval files, activate a campaign, spend money, or publish without a signed approval. Founder terminal steps are marked `founder-in-own-terminal`.

Paths use `<mkt>` for the project's Marketing root. Run commands from the repo root.

## 0. One-time founder setup (founder-in-own-terminal)
- Goal: a signing key the agent cannot use, plus provider accounts.
- Do: `ssh-keygen -t ed25519 -f ~/.ssh/marketing_approval` (passphrase, never in ssh-agent). Add `<principal> namespaces="marketing-approval" <public key>` to `~/.config/business-strategist/allowed_signers`, then `sudo chown root:root` and `sudo chmod 0644` it and its directory (see `references/marketing-execution.md`).
- Accounts: Postiz (self-hosted; set `POSTIZ_BASE_URL`, `POSTIZ_API_KEY`); GA4 or PostHog with a read connection; Meta: the current `META_ACCESS_TOKEN` is expired, so renew it with write permission only when step 7 is approaching (`references/ad-platform-connections.md`).
- Done when: `python3 scripts/marketing/connections.py probe ga4` (or `gsc`) reports `connected`, and execution dry-runs stop complaining about the signers file.
- Blocked by: no root access (a user-owned 0444 file is accepted but weaker; say so), missing credentials.

## 1. Pain-first gate (agent)
- Run `python3 scripts/route_workflow.py "<request>" --project <slug> --intent <route>` for the marketing route.
- Done when: it does not return `gate_blocked`, or the founder explicitly chose `--override-gate --override-stage problem_validation`, recorded in the output.
- Blocked by: `problem_validation` missing. Route to `idea-grill` and evidence research; do not paper over it.

## 2. Positioning and product-marketing context (agent, founder reviews)
- Skills: `archetype-gtm-strategist` then `marketing-strategy-builder`; fill the product-marketing-context reference of `marketing-strategy-builder`.
- Input: reviewed segments, pains and journey from the case.
- Done when: every positioning claim cites an evidence ref and the founder confirmed segment, offer and one channel.
- Blocked by: unreviewed or contradicted evidence; unsupported claims are removed, not softened.

## 3. Content inputs and keyword map (agent, founder reviews)
- Run, as inputs exist: `python3 scripts/evidence_scout/search_journey.py --plan <plan> --run-dir <dir>`; `python3 scripts/evidence_scout/analyze_competitor_marketing.py --content-inventory ...`; `python3 scripts/marketing/social_topics.py --records <evidence> --out <dir>`; optional demand proxy `python3 scripts/marketing/keyword_volume.py --map <keyword-map.json> --location-code N --language-code xx --dry-run` (shows cost first).
- Then `python3 scripts/marketing/keyword_map.py <map.json> --base <dir>` and apply the seo-rule-pack reference.
- Done when: the map validates, each target page has one intent, and the founder accepted or rejected each proposal. Volumes are a demand proxy, not pain; null stays unknown.

## 4. Page built and site gate passes (agent)
- Skill: `brand-website-designer-builder` (and the `geo-audit` skill for answer-engine readiness).
- Run: `python3 -m scripts.brand.site_gate <served-origin> --site-dir <site-dir>`.
- Done when: the gate exits 0 with its evidence files written; a skipped check needs a stated reason.
- Deploy is a separate founder-authorized action. Only after it, `python3 scripts/brand/indexnow_ping.py <host> --key <key> --confirm-deployed`.

## 5. Tracking verified (agent runs, founder exports)
- Founder exports GA4 or PostHog event data (last 7 days) and passes the export metadata.
- Run: `python3 scripts/marketing/verify_tracking.py <tracking-plan> --source ga4 --export <file> --days 7`.
- Done when: the result is `ready` from observed events. No export or no events means unknown, and the campaign does not go live. Never treat missing as zero.

## 6. First organic post (agent prepares, founder signs)
- Agent writes `<mkt>/actions/post-1.json` (`action_kind: schedule_post`, exact `provider_request`, unique `id`) and runs `python3 scripts/marketing/execute.py approval-request <action.json> --by <principal> --marketing-root <mkt>`.
- Founder reviews the printed text, runs the printed `ssh-keygen -Y sign -n marketing-approval` command in their own terminal.
- Agent: `python3 scripts/marketing/execute.py attach-signature <action.json> <message>.sig`, then `python3 scripts/marketing/execute.py run <action.json> --approval <approval.json> --marketing-root <mkt>` (dry run). Only after the founder says go: add `--execute`.
- Done when: a receipt exists under `<mkt>/receipts/` with the Postiz post id and the founder sees the scheduled post in Postiz.
- Blocked by: no signature, expired approval (7 days default), changed request (new digest, new approval), an `uncertain` receipt (check Postiz, use a new action id).

## 7. First paid test, created PAUSED (agent prepares, founder activates)
- Prerequisites: steps 4 and 5 done, a renewed write-capable `META_ACCESS_TOKEN`, a founder-set test budget.
- Same flow as step 6 with `action_kind: create_campaign`, a positive `spend_cap` (Meta minimum is about 100 USD or local equivalent), created PAUSED.
- Founder reviews the campaign in Ads Manager and activates it there. The agent never activates, raises caps or edits it; any change needs a new action and approval.
- Done when: the receipt shows the paused campaign id and the founder recorded the activation date or a decision not to activate.

## 8. Week-1 review (agent, founder decides)
- Founder exports aggregate results for this week and, if available, a baseline of equal length. Store exports under the Marketing root.
- Run `python3 scripts/marketing/review_cycle.py prepare --project <slug> --campaign <id> --preset <preset> --current <export> --baseline <baseline> --period-start ... --period-end ...`, analyze the packet, then `review_cycle.py finalize --project <slug> --campaign <id> --packet <packet> --review-json <review.json>`. Optional: `python3 scripts/marketing/connections.py probe gsc` and `python3 scripts/marketing/search_feedback.py <keyword_map> <gsc_export>`.
- Rules: compare only equal windows and matching property, timezone and attribution; a missing export, suppressed value or immature conversion is **unknown, not zero**; with no baseline the answer is collect more data, not a winner.
- Done when: the review states continue, change, stop or collect_more_data with the evidence and at most three tasks. Accepting a task never authorizes posting or spending.
