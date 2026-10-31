# GTM hand-offs at the moment of use

Each stage below names the input to read or the skill and tool that owns the next step.

- Before positioning or channel choices, read the case's `case_insights.md` and
  `cases/<id>/market_research/decision_memo/decision_memo.md`
  (built by `scripts/evidence_scout/build_decision_memo.py`).
  If either is missing or stale, say so and route back to opportunity-risk-designer.
- Content planning goes to marketing-strategy-builder with the inputs that exist:
  `content-opportunities.json` from `scripts/evidence_scout/search_journey.py`,
  `scripts/evidence_scout/analyze_competitor_marketing.py --content-inventory`,
  `scripts/marketing/social_topics.py`, merged by `scripts/marketing/keyword_map.py merge`.
- The website goes to brand-website-designer-builder:
  launch needs `scripts/brand/site_gate.py`; the `geo-audit` route is an optional citability check.
- First campaign: follow
  `.agents/skills/marketing-campaign-operator/references/first-campaign-runbook.md`.
  The founder (or the router) invokes marketing-campaign-operator for execution.
  The agent may prepare action files and approval requests; it never signs, activates or spends.
