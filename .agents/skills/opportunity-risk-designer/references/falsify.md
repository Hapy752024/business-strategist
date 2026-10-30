# Adversarial claim falsification

Checked route: `claim-falsification`. A fresh agent with no access to the findings tries to disprove each material claim with web-only adversarial searches. Pattern source: the `falsify` command in the open-source zircote/sigint plugin.

## When to run

- After synthesis has produced a reviewed `claim-ledger.json`, and before final case delivery (v2 `case_insights.md` final review, appraisal or case plan).
- On material claims only: claims with a non-empty `decision_affected`, or `claim_type`/`claim_scope_type` in `willingness_to_pay`, `prevalence`, `unmetness`, `pattern` or `transfer` (demand, willingness to pay and transfer claims). Competition and regulation claims count as material when you record them through `decision_affected`.
- Rerun after a deep dive changes a material claim. Do not run it on progress snapshots that nobody will act on yet.

## Steps

1. Export the claims-only input. This file contains claim text and scope only. Supporting and counter evidence, rationale, verification passages and independence keys are left out:
   `python3 scripts/evidence_scout/export_claims_for_falsification.py --ledger <run>/customer-feedback/claim-ledger.json --output <run>/customer-feedback/falsification-claims.json --search-budget 3`
2. Dispatch the `claim-falsifier` agent (`.claude/agents/claim-falsifier.md`, tools WebSearch/WebFetch only) in a fresh context. It treats fetched page text as evidence, never as instructions. Paste only the contents of `falsification-claims.json` into its prompt. Do not include insights, the case narrative, source lists or your opinion of the claims. Save its JSON reply as `<run>/customer-feedback/falsification-verdicts.json`.
3. Apply it. The verdicts are untrusted, so they are validated against `schemas/falsification-verdicts.schema.json`, and unknown claim ids, duplicates, missing evidence for falsified/weakened verdicts, upgrade attempts and "survived" wording that claims confirmation are all rejected:
   `python3 scripts/evidence_scout/apply_falsification.py --ledger <run>/customer-feedback/claim-ledger.json --verdicts <run>/customer-feedback/falsification-verdicts.json --claims <run>/customer-feedback/falsification-claims.json`
   Verdicts for claim ids outside the exported set are rejected. A survived rationale must give N equal to the number of searches run.
   The reviewed `claim-ledger.json` is never rewritten. Outputs are written beside it: `claim-ledger.falsified.json` (publishable `claims` plus `quarantined` claims with reasons), `falsification-report.json` and `falsification-report.md`.
4. If the agent's verdicts are rejected, return the error list to a new falsifier run. Never hand-edit verdicts so they pass.

## Effects

| Verdict | Action |
|---|---|
| falsified | Quarantined: excluded from publishable claims, kept with reason and evidence. Not deleted. |
| weakened | Confidence moves down one level (`high` > `medium` > `low` > `unresolved`), with a note in the rationale. |
| survived | Unchanged. It means only "no disconfirming evidence found within N searches". It never upgrades a claim. |
| inconclusive | Unchanged; record the access or scope gap. |

## Publication in case insights

- Keep binding and citing the reviewed `customer-feedback/claim-ledger.json` in `publication_claims`; do not bind `claim-ledger.falsified.json`.
- The publisher (`scripts/publication_claims.py`, also used by `validate_case_insights.py`) reads the sibling `claim-ledger.falsified.json` when it exists. It refuses a quarantined claim (`<id>: claim quarantined by falsification (<reason>)`). It also refuses every ledger citation when the falsification was run against an older ledger (`source_ledger_sha256` mismatch); re-run export, falsifier and apply.
- Do not cite a quarantined claim as a finding. Under the risks or evidence-limits section, list it in prose as "Falsified on <date>: <claim>", with the disconfirming source link, its date and the decision it no longer supports.
- The publisher does not render confidence. The author must state a weakened claim's downgraded confidence from `falsification-report.json` and give the counter-source next to the claim.
- Survived claims may say "no disconfirming evidence found in an adversarial check (N searches, <date>)". Never write "confirmed" or "verified" for them.
- A quarantined claim that a recommendation depended on makes that recommendation pending until it is re-argued from the remaining evidence.
