# Comparative creative analysis

Use `schemas/creative-evidence.schema.json` and `fixtures/marketing/creative-evidence/`. Bind captured observable fields; record selection bias, publication/observation dates, distribution, metric availability/definitions. Hooks/pattern annotations remain analyst hypotheses. No scraping, posting or scheduling is implied.

Run `python3 scripts/marketing/creative_evidence.py <creative-evidence.json> --base <marketing-root>`. Saves/shares/comments per 1,000 views require available counts and positive views. Zero/missing denominators and numerical overflow stay undefined. Never sum overlapping engagement, substitute followers for creator baselines or infer retention/revenue from views.

Cohorts match platform, format, language, market, distribution, full elapsed observation days and metric definitions. Unknown distribution is excluded. Full-day buckets are coarse: inspect timing before interpretation. Replication needs distinct known creators. Small samples, outlier selection and unmeasured audience differences prohibit causal claims. Include weak counterexamples where captured. Optional `tests` records example/counterexample IDs, hypothesis, held conditions, metric and limitations; it does not run/fund an experiment. Publish through Marketing so changed source bytes invalidate dependent use.
