# To Be Improved

## 2026-08-15 - Setup/Skill Improvement Batches Landed

Addressed from the 2026-06-21 list:

- Interview screener/tracker from selected evidence items → done: `interview-bridge` skill + `scripts/evidence_scout/build_interview_kit.py` (screener, guide, tracker under `<run>/interview/`).
- Script-generated `competitor_plan.md` / `marketing_plan.md` → done: both competitor scripts write plan artifacts at run start; skill workflows reference them.
- One-question-at-a-time enforcement → done: `collect.py` now writes an explicit closing-question rule into `assumptions.md`; evidence-scout, idea-grill, and market-problem-discovery templates pull the first unresolved item.
- Query-expansion registry → done: `scripts/evidence_scout/registries/query_expansion.json` (per-market trigger markers, reddit queries, target subreddits, phrase variants); `collect.py` reads it with in-code fallbacks.
- Registry validation script → done: `scripts/validate_registries.py`, wired into `validate_setup.sh` (and thereby CI).

Also landed: eval cases from canonical playbook cases (Socialcam, GetYourGuide pull-pivot, Xiaohongshu sequencing) for archetype-gtm-strategist plus gate evals for the two marketing skills; `references/evidence-registry.md` as the cross-skill distilled evidence base with sequencing and weak-evidence gates in `social-digital-marketing-planner` and `marketing-strategy-builder`; a standing `Reachability bias:` line-item enforced by the discovery finalize gate; a severity × frequency candidate-ranking rubric in market-problem-discovery; and the whitespace matrix scaffold (`build_whitespace_matrix.py`) wired into opportunity-risk-designer.

Still open from 2026-06-21: per-subreddit API collection (r/Finanzen, r/Versicherung, r/Krankenkassen, r/beamte, r/germany — the registry now lists them as `target_subreddits`, but collection still uses global search syntax); marketing price normalization heuristics.

## 2026-06-21 - Flow Improvement Verification

- Public evidence remains mostly weak: the latest evidence run found 65/73 weak records and 8/73 medium records. The workflow now routes this to `user_review_plan.md`; next improvement would be a script that turns the selected evidence items into an interview screener and interview tracker.
- The flow now writes `research_plan.md`, `assumptions.md`, and `user_review_plan.md`, but competitor discovery and marketing analysis still only document their plans in skill instructions. Add script-generated `competitor_plan.md` and `marketing_plan.md` if those steps need the same audit trail.
- User involvement is now explicit, but still artifact-based. A future agent-facing improvement could enforce one-question-at-a-time interaction in the final response template, using the first unresolved question from `assumptions.md` or `user_review_plan.md`.
- Google Trends terms are expanded with broader German insurance demand phrases, but the expansion is still static. Add a small query-expansion registry by market/topic so layperson terms, trigger events, and competitor names can be updated without code edits.
- Source intent and known competitor data now use JSON registries. Add a lightweight registry validation script to catch malformed JSON, missing expected keys, and duplicate/conflicting domains before a research run.
- Reddit coverage is broader but still depends on global search syntax. A future polish pass could add per-subreddit API collection for `r/Finanzen`, `r/Versicherung`, `r/Krankenkassen`, `r/beamte`, and `r/germany`.
- Marketing price normalization works for common German and English separators, but it remains heuristic. Keep raw tokens in reports and treat normalized values as convenience fields when pages mix English copy with German number formats.
