# Judge Lenses — Scoring Rubric For The Draft Tournament

The judge scores every draft 1-5 on five lenses. Every score must cite the specific evidence item, registry pattern, or named assumption behind it. A score without a citation is invalid; re-judge.

## Lens 1 — Evidence Grounding

Does the draft respect the topic workspace evidence (customer language, observed workarounds, competitor gaps, interview results)?

- 5: every load-bearing claim traces to evidence or an explicitly named assumption.
- 1: the draft invents demand, personas, or channel behavior from general knowledge.

Reference: the workspace's `evidence.jsonl` / `report.md`; the weak-evidence list in `references/evidence-registry.md` — drafts that rest on downloads, views, waitlists, press, or partnership announcements score low.

## Lens 2 — Sequencing Compliance

Does the draft respect manual learning → retained-value proof → one repeatable motion → scale?

- 5: the draft's first step is the cheapest learning move and every amplification step is gated on proof.
- 1: paid scale, broad channel checklists, or loops before single-user value and retention evidence.

Reference: the sequencing rule, product/referral loop gates, and channel/loop recommendation protocol in `references/evidence-registry.md`; Homejoy (discount scale before delivery consistency) and Socialcam (downloads without retention) are the canonical violations.

## Lens 3 — Customer-Trust Compliance

For consumer services: does the draft match uncertainty reducers to the service's risk level, and does it avoid dark patterns?

- 5: consequential/data-sensitive/hard-to-reverse services get precise scope, total price, credentials, human access, redress; commitment is staged where outcome variance is high; reviews and exit pathways are authentic and clear.
- 1: lifestyle promises for a high-risk service, nationality-persona personality claims, incentivized/fake reviews, hidden fees, obstructed cancellation, pressure selling.

Reference: the Service-Customer Decision and Trust section of `references/evidence-registry.md`.

## Lens 4 — Constraint Fit

Does the draft fit the founder's actual budget, team, credibility, geography, regulatory exposure, and assets?

- 5: the mechanism runs on resources the founder demonstrably has.
- 1: the mechanism secretly requires a founder advantage that does not exist here (dense network, prior audience, media access, regulatory license).

Reference: transfer limits in `references/evidence-registry.md` — Dropbox's technical-community fit, Stripe's YC access, Buffer's founder audience, Monzo's timing and media access are prerequisites, not tactics.

## Lens 5 — Testability

Does the draft name its riskiest assumption and the cheapest test that would falsify it, with a threshold and stop rule?

- 5: one named riskiest assumption, a ≤1-week test, a numeric threshold, and a stop/pivot condition.
- 1: success defined by attention metrics or by executing the full plan.

## Verdict Rules

- **Select a winner:** one draft leads on the lenses that are decisive for this decision (state which lenses were decisive and why).
- **Synthesize:** a winner plus grafted strengths from losers, when the grafts do not violate the winner's mechanism.
- **Feedback round:** no draft scores ≥4 on evidence grounding AND constraint fit.
- **Escalate to the user:** after 2 feedback rounds without a winner, or when the judge's real finding is that the decision lacks evidence — route the gap to `evidence-scout` or `interview-bridge` instead of picking the least-bad guess.
