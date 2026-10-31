# GTM hand-offs at the moment of use

Each stage below names the input to read or the skill and tool that owns the next step.

- Before positioning or channel choices, read the case's `case_insights.md` and
  `cases/<id>/market_research/decision_memo/decision_memo.md`
  (built by `scripts/evidence_scout/build_decision_memo.py`).
  If the memo is missing or stale, build it (draft basis via `--draft-claims` when no reviewed ledger exists)
  and say which basis it uses; never skip it.
  Claim-challenge order: export claims (`--draft-claims` or ledger) → claim-falsifier JSON verdicts →
  `apply_falsification.py` → (re)build the memo (route `claim-falsification`).
- Reuse the evidence-scout early desk steps: `content-opportunities.json` from `scripts/evidence_scout/search_journey.py`,
  `scripts/evidence_scout/analyze_competitor_marketing.py --content-inventory`,
  `scripts/marketing/keyword_volume.py` volumes and `scripts/marketing/social_topics.py`.
  If any is missing, run it now (state provider gaps); never skip it.
  Content planning goes to the marketing skill (seo-page-planning mode), merged by `scripts/marketing/keyword_map.py merge`.
- The website goes to brand-website-designer-builder:
  run `scripts/brand/site_gate.py` whenever a page has been built (no business prerequisite);
  the `geo-audit` route is an optional citability check.
- First campaign: follow
  `.agents/skills/marketing-campaign-operator/references/first-campaign-runbook.md`.
  The founder (or the router) invokes marketing-campaign-operator for execution.
  The agent may prepare action files and approval requests; it never signs, activates or spends.
