# Multilingual pain discovery: live test and scoped improvements

Searches began 21 September 2026; source hydration continued 22–23 September and refinement was executed 23 September. Exact retrieval times are retained in the raw runs and capture receipts.

See the [full live pilot and evidence](../../projects/german-insurance-opportunity/business-analysis/cases/personal-decision-service/market_research/pain_points/runs/20260921-multilingual-calibration/report.md).

| Search strategy | Query-result slots | Unique URLs | Captured pages | Confirmed target-language episode pages | New confirmed pages after round 1 |
|---|---:|---:|---:|---:|---:|
| German: current automatic queries | 20 | 16 | 4 | 3 | — |
| German: deliberate episode/source queries | 20 | 20 | 14 | 5 | — |
| German: historical mixed-language replay | 13 | 13 | 2 | 0 | — |
| German: source-derived refinement | 15 | 15 | 10 | 6 | 5 |
| English: current automatic queries | 20 | 19 | 3 | 1 | — |
| English: deliberate episode/source queries | 20 | 18 | 17 | 10 | — |
| English: source-derived refinement | 15 | 14 | 13 | 6 | 3 |

Counts are confirmed lower bounds over partially reviewed convenience samples, not precision/recall or market prevalence. German/English are separate sampling lanes; refinement occurred later.

Implementation: `scripts/evidence_scout/collect.py` now retains missed English insurance wording, handles BU next to punctuation, distinguishes ambiguous brokers from real-estate context, and does not use a German/English lexicon to reject matching other-language leads. `tests/test_multilingual_pain_live_regressions.py` reproduces the material failures with synthetic phrases.

The evidence-scout calibration reference now covers semantic disambiguation, episode/source diversity, original versus translated language, immutable automatic baselines, rejected-lead review, substantive hydration checks, API fallback, original speaker attribution, separate denominators, dated evidence and fresh discoveries. No unrelated provider or discovery-wrapper changes were made.

All five wider improvement areas are deferred until the user is satisfied with this customer-pain workflow. The project assessment and business execution selection were not advanced. No commit, push, outreach or deployment.

Validation details are retained in the pilot's `validation.json`. Live proof is limited to German and English in this insurance context; French, Arabic and Japanese are mechanical regression cases only. Review was inline, not independently blinded.
