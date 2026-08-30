# Strategy Draft Tournament — Workflow

Generate-and-judge protocol for consequential, under-determined deliverables: service definitions, pricing structures, GTM approaches, campaign concepts, packaging. The point is not volume — it is escaping the first-idea trap by forcing mechanism diversity, evidence-grounded challenge, and cross-pollination before committing.

## When To Use

- The deliverable is consequential (hard to reverse, expensive to execute, strategy-defining) AND the answer space is wide (several plausible mechanisms, not one obvious approach).
- The user asks to "explore options", "give me alternatives", or a first draft feels like it locked in assumptions too early.

Do NOT use when:

- A plan already exists and needs challenge → `startup-challenge-panel`.
- The deliverable is well-scoped and one draft with a quality checklist suffices → `marketing-strategy-builder`, `archetype-gtm-strategist`, `social-digital-marketing-planner`.
- Evidence about the customer/problem is still missing → run `evidence-scout` or `interview-bridge` first; a tournament over ungrounded drafts produces polished guesses.

Multi-agent cost must be proportional to decision value. Four drafting agents plus a judge is 5+ subagent runs — spend that on a pricing structure or GTM motion, not on a newsletter subject line.

## Step 1 — Frame The Decision

Before spawning anything, write down:

1. **Decision question** — one sentence: what exactly is being chosen (e.g. "which first-customer motion for a €2,400/yr expat tax service in Germany").
2. **Constraints** — budget, team, time, geography, regulatory exposure, existing assets and traction.
3. **Evidence pack** — paths to the topic workspace evidence (`evidence.jsonl`, `report.md`), competitor analysis, and interview results that drafts must respect. Drafts may not invent demand.
4. **Mandates** — 3-4 genuinely different mechanisms. Choose mandates that span the space, e.g. for a GTM motion: manual founder-led sales / product- or content-led / partnership-embedded / contrarian (the approach the founder is NOT considering). For pricing: staged diagnostic / transparent flat / outcome-linked / freemium-or-free-proof. Never spawn four variants of the same idea with different adjectives.

If the frame cannot be written, the decision is not ready for a tournament — clarify first (one focused question).

## Step 2 — Draft Round

Spawn one subagent per mandate in parallel. Each prompt includes: the decision question, constraints, evidence pack paths, its mandate, the requirement to state assumptions and name the riskiest one, and the output shape (mechanism in one line, then the draft, then self-identified weaknesses). Drafts must not see each other — independence is what buys diversity.

Cap each draft: one screen of mechanism and rationale, not a finished plan. Detail comes after selection.

## Step 3 — Judge Round

One judge agent (fresh context, not a drafter) receives all drafts plus `references/judge-lenses.md`. The judge:

1. Scores each draft on the rubric (evidence grounding, sequencing compliance, customer-trust compliance, constraint fit, testability) with a cited reason per score — a score without a cited lens or named assumption is invalid.
2. Names each draft's fatal flaw, if any.
3. Recommends: **select a winner**, **synthesize** (winner + grafted strengths from losers), or **feedback round** (no draft clears the bar).

The judge challenges; it does not approve by default. A round where every draft scores "good" is a judging failure.

## Step 4 — Feedback Round (Only When No Draft Clears The Bar)

Run at most 2 feedback rounds. Each drafter gets: its own draft, the judge's critique of it, and the **mechanisms of the other drafts** (cross-pollination — not the full texts, to force grafting rather than copying). The drafter revises, explicitly noting what it adopted from other mandates and what it rejects and why.

After round 2, if no winner emerges, stop and present the top 2 drafts with their scorecards and decisive tradeoffs to the user — the residual disagreement is a genuine strategic choice, not a drafting defect.

## Step 5 — Deliver

The final response contains:

- Decision frame (question, constraints, evidence used).
- Draft set: one line per mechanism.
- Judge scorecard and the decisive tradeoff.
- Selected or synthesized recommendation.
- What would falsify the pick, and the cheapest test that would run this week.
- Open evidence gaps routed back to `evidence-scout` or `interview-bridge`.

Save substantial tournament outputs under the topic workspace (`reviews/<timestamp>-<decision>/`) and record the event in the topic manifest.

## Anti-Patterns

- Drafts that differ in tone but share one mechanism — mandate diversity is the whole point.
- Judging from training memory instead of the evidence pack and registry lenses.
- Averaging scores or picking by majority; the judge decides on evidence weight, not votes.
- Feedback rounds without cross-pollination — that is iteration, not a tournament.
- Running the tournament to avoid telling the user an uncomfortable truth (e.g. all drafts fail because the segment has no reachable trigger — say that instead).
