# Baseline acceptance run, pre-plan tree 486a7ae (2026-10-30)

> Superseded: rescored on the fixed harness (cdf3768). Corrected numbers: 3 passed (cp11 now counted as a provider-gap pass via the Brave 402 result), model cost 4.29 USD, hook denials deduplicated. The tables below are the original pre-fix readings; see baseline-2026-10-30b for the re-run.

Scenario: hybrid-insurance-advisor. Harness: scripts/run_acceptance.py at 7eea34e-era HEAD, default budgets (provider 25, model 40).
Run: 5 rounds (1 initial + 4 nudges, nudges exhausted), 639 s wall time, stop_reason `completed`.

## Checkpoints: 2 passed, 8 failed, 1 not exercised

| id | result | note |
|----|--------|------|
| cp01 workspace check before new work | pass | |
| cp02 routing before specialist work | fail | the agent never ran route_workflow.py; one hook denial (idea-grill without route envelope) |
| cp03 intake (proxy) | fail | no answered intake turns: the feeder never answered |
| cp04 per-entity voice (proxy) | fail | no per-entity jsonl |
| cp05 SERP/landscape stages | fail | no stage json |
| cp06 official data (proxy) | pass | |
| cp07 (proxy) | fail | |
| cp08 falsification/decision memo/scores | fail | step 3 never reached |
| cp09 pain-first gate sequence | fail | detector saw no blocked route call; the agent self-gated from documents |
| cp10 GTM, keyword volumes, local site | fail | step 3 never reached |
| cp11 provider-failure honesty (proxy) | not_exercised | no run summary.json |

## Cost
- Scorecard model_usd: 35.52 (OVERSTATED). `total_cost_usd` is cumulative per session and repeats across several result events per round, and the harness sums them. The last result event gives the true figure: 4.29 USD.
- Provider spend measured: 0 USD (apify 0, dataforseo 0, serpapi 0 searches; complete=false). Agent self-reported about 1.3 USD of the 25 USD evidence budget. Brave Search returned 402 (monthly limit).
- over_budget: null. Serpapi left unpriced (no per-search price in the account response).

## Hook and permission events
- 2 hook-denial entries (one denial, counted twice): Skill idea-grill called without a JSON route envelope (transcript line 13/18). It recovered.
- Bash permission denials at lines 21, 212, 461, 506 (curl, awk and a for-loop were not allowed).
- 18 host: entries in writes_outside_eval, all under projects/us-retirees-italy/web-site. They come from a concurrent user session and next dev, not the agent (no transcript reference).

## Friction (transcript.jsonl line numbers, local only)
1. Skill dispatch without envelope denied by hook (13, 18).
2. Brave Search 402 usage limit (79-85); agent switched to firecrawl.
3. Reddit unreachable: firecrawl rejects reddit.com (336-348), Dialog MCP unreadable.
4. Oversized tool results: 12 Read errors above 25000 tokens (119-551); the agent delegated to 7 Agent subagents.
5. Agent stopped at the pain-first gate and asked 4 times for the override (rounds 1-4). The feeder sent a generic nudge each time, because its matcher only reads question sentences and the agent's options list had none. Downstream steps (cp08, cp10) are therefore unmeasured for this tree.
6. Agent never invoked route_workflow.py; cp02 and cp09 depend on it.

## Caveats
- The model cost figure and the feeder miss are harness issues; consider fixing and re-running the baseline before comparing against the post-plan run.
