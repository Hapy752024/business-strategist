# To Be Improved

## 2026-06-21 - Flow Improvement Verification

- Public evidence remains mostly weak: the latest evidence run found 65/73 weak records and 8/73 medium records. The workflow now routes this to `user_review_plan.md`; next improvement would be a script that turns the selected evidence items into an interview screener and interview tracker.
- The flow now writes `research_plan.md`, `assumptions.md`, and `user_review_plan.md`, but competitor discovery and marketing analysis still only document their plans in skill instructions. Add script-generated `competitor_plan.md` and `marketing_plan.md` if those steps need the same audit trail.
- User involvement is now explicit, but still artifact-based. A future agent-facing improvement could enforce one-question-at-a-time interaction in the final response template, using the first unresolved question from `assumptions.md` or `user_review_plan.md`.
- Google Trends terms are expanded with broader German insurance demand phrases, but the expansion is still static. Add a small query-expansion registry by market/topic so layperson terms, trigger events, and competitor names can be updated without code edits.
- Source intent and known competitor data now use JSON registries. Add a lightweight registry validation script to catch malformed JSON, missing expected keys, and duplicate/conflicting domains before a research run.
- Reddit coverage is broader but still depends on global search syntax. A future polish pass could add per-subreddit API collection for `r/Finanzen`, `r/Versicherung`, `r/Krankenkassen`, `r/beamte`, and `r/germany`.
- Marketing price normalization works for common German and English separators, but it remains heuristic. Keep raw tokens in reports and treat normalized values as convenience fields when pages mix English copy with German number formats.
