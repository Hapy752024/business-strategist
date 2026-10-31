# Acceptance results: hybrid insurance advisor (DE), baseline vs after vs verify

Read this as a harness shakedown with n=1 per arm, not as proof the branch works.

## 1. What was run

- Scenario: `evals/acceptance/hybrid-insurance-advisor/scenario.md` (founder wants a hybrid insurance advisory business in Germany; five deliverables; no ad spend, no publishing, no contact; pain-first gate override requested after the gate blocks). Founder answers were fed by the harness.
- Runs (one each, same prompt, same harness): `baseline` at ref 486a7ae (pre-plan tree), `after` at 1139ecb, `verify` at 233cb09 (after the 7.4 fixes).
- Budgets: model 40 USD, provider data 25 USD per session. The runner records but does not enforce provider caps inside the tree under test.
- Scorecards: `evals/acceptance/runs/{baseline,after,verify}-2026-10-31/scorecard.json`. Transcripts and artifacts stay local (they contain third-party posts).

## 2. Checkpoints (current detectors, `4384169`)

| cp | check | baseline | after | verify |
|---|---|---|---|---|
| 01 | workspace shown before new project | pass | pass | fail |
| 02 | routing through the router and Skill envelope | fail | pass | fail |
| 03 | intake, one question per turn (proxy) | pass | pass | pass |
| 04 | topic-led and entity-led customer voice | fail | fail | fail |
| 05 | search-journey study | fail | fail | fail |
| 06 | desk research with official statistics | fail | fail | fail |
| 07 | international commercial precedent | pass | fail | fail |
| 08 | falsification and decision memo | fail | fail | fail |
| 09 | pain-first gate then override then downstream | pass | pass | pass |
| 10 | GTM bundle (keyword map, site gate, runbook, paused campaign) | fail | fail | fail |
| 11 | honest provider gaps | pass | pass | pass |
| | **total** | **5/11** | **5/11** | **3/11** |

Scorings changed: the first scorecards used earlier detectors. 7.4B (`c3b7f15`, `c62fe67`, `233cb09`) fixed detectors, a Bash guard and the precedent rule; 7.5 (`4384169`) made `--help` calls not count as workspace writes (cp01), required a number with a unit next to an official domain (cp06), added a near-miss label for an unsourced foreign comparable (cp07), excluded helper scripts from provider failures (cp11), and re-scored all runs. Numbers in older reports (for example after = 3/11) are superseded; do not compare across them. Detector fixes were made after seeing the runs, so the table is tuned to these transcripts.

The 7.4 audit judged verify as 3/11 on a strict reading (cp07 a near miss), and cp01 in verify is a genuine order violation (project created before the existing workspaces were named).

## 3. Blind grade of the deliverables

An independent blind grader scored baseline (A) and after (B) on eight criteria (1-5):

- A (baseline): 36/40. B (after): 31/40. Preference A, medium confidence. The verify run was not graded.
- What drove it: A applied the rule that one business cannot be both broker and fee-only adviser (§34d GewO para. 3) to the "hybrid" idea; B's model C implied the opposite. A shipped a dated, sourced competitor scan (16 entities, false positives listed) and a break-even and cash-need model; B had no competitor scan and one misattributed, undated test result. B was as good or better on quote-level URLs, unknown-versus-zero wording, and German outreach drafts.
- Shared weakness: `case_insights.md` was the empty template in both arms, and both customer-voice reports were unreviewed collector dumps. Neither arm broke a safety rule (no spend, no contact, no publication).
- Limits: the grader could not hide the arm perfectly (file set and style), and A's research notes contradict its own override statement.

## 4. Cost and time

| | model USD (max session total) | provider USD measured | wall time |
|---|---|---|---|
| baseline | 4.95 | 0.00 (incomplete) | 1138 s |
| after | 2.01 | 0.00 (incomplete; 2 SerpApi searches unpriced) | 642 s |
| verify | 5.11 | 0.22 (Apify 0.20, DataForSEO 0.022; incomplete) | 1280 s |

Provider spend is an account-usage delta and misses unpriced and lagging usage. The verify run roughly doubled model cost against after; asynchronous subagents re-waking the session is a hypothesis, not isolated (WF-044).

## 5. Findings

Process did improve:
- The agent used the Skill tool for every repository skill in the verify run, with route packets injected; no SKILL.md was read by hand.
- Subagent Bash: 43 calls and 0 denials in verify after `233cb09`.
- Router and gate behavior worked in after and verify (cp09 pass), including a structured block and override.

Outcomes did not improve:
- The new capabilities (search journey, VOC table, decision memo, falsification, keyword map, site gate, first-campaign runbook) never ran in after or verify. Their instructions reached the agent at the point of use; it read them and did not execute them. Their prerequisites (source review, synthesis, claim ledger) were never produced, and nothing blocks writing the downstream documents without them (WF-037).
- Entity-led feedback ran for one of five planned entities in verify; the entity worker failed (WF-041).
- Required references in route packets were mostly not read (WF-043); official-statistics evidence was lost to a denied PDF extraction (WF-042).

Defects found and fixed: 7.4A `2d90eb5` (new capabilities wired into the stages that use them); 7.4B `c3b7f15`, `c62fe67`, `233cb09` (detectors, Bash guard, subagent command allowlist, one command per call); 7.5 `4384169` (router crash on missing strategy plan WF-039, duplicate override records WF-040, worker set-up error and instruction WF-041, detector and scorecard fixes). These are verified by tests, not by a new live run.

Open: WF-033 Brave quota, WF-034 first Skill call without envelope (recurred in verify), WF-035 router usability, WF-036 large tool results, WF-037, WF-038, WF-042 to WF-045 (plugin trigger suite below its 0.8 gate: case-appraisal 0/3, competitor-discovery 1/3). See `evals/workflow-improvements.md`.

## 6. Conclusion

Three single runs. The pre-plan tree scored 5/11 and the best deliverables; the branch scored 5/11 then 3/11, and its deliverables were graded lower. There is no evidence yet that the branch improves research outcomes. What it shows is better process control (routing, packets, commands) and a set of capabilities that the agent does not reach unprompted. Variance between runs is unmeasured, so the 5-versus-3 and the 36-versus-31 may partly be noise.

The next run (at the current head, with the 4384169 fixes) should check: whether the agent produces a source review and claim ledger before the business case; whether the entity-led frame covers at least three entities; whether the main agent can extract PDF statistics; and whether the first Skill call carries the envelope. Run at least two per arm and grade the verify deliverables blind before drawing any conclusion.

## 7. Addendum: loosened workflow run (ref f8fe94d, Task 8)

After the founder judged the setup too strict, Task 8 made four desk steps (search journey, competitor content inventory, keyword volumes, social topics) default early steps, added labelled fallbacks (unreviewed VOC table, draft-claims challenge and memo), and kept one hard rule: no final recommendation without a current claim challenge.

Run `evals/acceptance/runs/loosened-2026-10-31/`: 2/11 strict (cp02, cp09); cp03 and cp11 not exercised; 4/11 on a lenient reading (cp06 sources named without URLs, cp08 draft challenge and memo exist). Model 4.69 USD, provider 0.09 USD, 887 s.

- Ran: keyword volumes (after the gate override, before GTM), draft-claims memo with its label, the claim-falsifier agent, a broad competitor map (about 17 entities), the strongest regulatory analysis of any run (court rulings, §34d adviser licence) and the first real statistics.
- Did not run: the search-journey study, the VOC table and social topics (skipped without stated reason); the competitor content inventory (the agent told its own subagent not to write files); `apply_falsification.py` (verdicts copied by hand, memo built before the challenge so it still says "not run"); no international precedent pass. Customer voice was the thinnest of all runs (topic-led only).
- Harness fault found: the feeder answered the agent's licence question with the gate-override answer (cue matched anywhere in the message), so intake was not exercised. Fix pending.

Conclusion unchanged: making steps default in the instructions is not enough; the agent still skips steps nothing checks. n=1.
