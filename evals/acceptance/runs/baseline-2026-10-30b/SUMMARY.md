# Baseline re-run on fixed harness (cdf3768), pre-plan tree 486a7ae, 2026-10-30

Default budgets (provider 25, model 40). 8 rounds, 681 s wall time, stop_reason completed. The agent ended with "journey complete".

## Checkpoints: 3 passed, 7 failed, 1 not exercised

| id | result | note |
|----|--------|------|
| cp01 workspace check first | pass | |
| cp02 routing before specialist work | fail | idea-grill Skill called without route envelope, hook denial (transcript line 11/14); no route_workflow call with --check-skill before specialist work |
| cp03 intake (proxy) | pass | answers fed and persisted |
| cp04 per-entity voice (proxy) | fail | no per-entity jsonl |
| cp05 SERP/landscape stages | fail | no stage json |
| cp06 official data (proxy) | pass | |
| cp07 (proxy) | fail | |
| cp08 falsification, decision memo, scores | fail | business-case.md exists, none of the required artifacts |
| cp09 pain-first gate sequence | fail | no blocked gated route observed (route calls 83-105 returned usage/errors; override then recorded via record_gate_override, lines 157/178) |
| cp10 GTM, keyword volumes, local site | fail | gtm-plan.md and a local site exist; keyword-map, site-gate, runbook and paused campaign json missing |
| cp11 provider-failure honesty (proxy) | not_exercised | no provider failure this time |

## Cost and spend
- Model: 3.30 USD true (session max). Provider spend measured 0.09 USD (apify delta, may include concurrent use), complete=false; agent reports 0 USD of the 25 USD evidence budget. over_budget null. SerpApi unpriced.

## Rounds and reply kinds
8 rounds: initial 1, answer 4 (gate_override on 3 of them, licence_status twice), intake_cap 2 (first_segment, gate_override), nudge 1. Hook denials: 1 (idea-grill without route envelope). Bash permission denials: lines 23, 103, 471, 490.

## Host changes
None (writes_outside_eval is empty), so no attributed or concurrent entries.

## Comparison with the first baseline (rescored: 3 passed, 4.29 USD)
Both runs pass three checkpoints, but for different reasons. The first run stalled at the pain-first gate for four rounds because the feeder never sent the override; it passed cp11 on a Brave 402. The re-run received the override, built a case, business-case.md, gtm-plan.md and a local website, and ended with "journey complete", but still lacks the structured artifacts of cp04, cp05, cp08 and cp10 and gains cp03 while cp11 is not exercised. Cost fell to 3.30 USD (first run true cost 4.29). So the pre-plan tree can drive the journey, but without the structured evidence outputs the plan adds.
