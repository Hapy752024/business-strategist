# Comparative creative analysis

Use `schemas/creative-evidence.schema.json` and `fixtures/marketing/creative-evidence/`. Bind captured observable fields; record selection bias, publication/observation dates, distribution, metric availability/definitions. Hooks/pattern annotations remain analyst hypotheses. No scraping, posting or scheduling is implied.

Run `python3 scripts/marketing/creative_evidence.py <creative-evidence.json> --base <marketing-root>`. Saves/shares/comments per 1,000 views require available counts and positive views. Zero/missing denominators and numerical overflow stay undefined. Never sum overlapping engagement, substitute followers for creator baselines or infer retention/revenue from views.

Cohorts match platform, format, language, market, distribution, full elapsed observation days and metric definitions. Unknown distribution is excluded. Full-day buckets are coarse: inspect timing before interpretation. Replication needs distinct known creators. Small samples, outlier selection and unmeasured audience differences prohibit causal claims. Include weak counterexamples where captured. Optional `tests` records example/counterexample IDs, hypothesis, held conditions, metric and limitations; it does not run/fund an experiment. Publish through Marketing so changed source bytes invalidate dependent use.

## Paid creative tests

Platform allocation among ads is not random assignment. Record exposure/spend per variant, delivery method, audience overlap, observation/conversion lag and the outcome selected before looking at results. An ad receiving little delivery is insufficiently tested, not a demonstrated loser. Similar spend alone does not make audiences comparable; a causal comparison needs a suitable controlled design and enough outcome information. If the available budget cannot support it, keep the result directional and reduce the number of concepts rather than manufacture a winner.

Keep concept/angle, opening hook, demonstration/proof and CTA distinct in the existing creative brief. Use actual product experience and previous test learnings when preparing creator briefs; a strong hook with poor qualified conversion does not establish a winning ad. Avoid universal weekly production quotas and copying a popular format without its conditions. Record the next hypothesis, what stays fixed and what would change the decision. Check currently available platform testing tools before prescribing one; ordinary delivery, forced spend and native experiments are different designs.

Sources checked 2026-10-24: [Jon Loomer's creative testing walkthrough](https://www.jonloomer.com/meta-creative-testing/) (updated 2026-01-02; explains delivery allocation versus controlled tests) and [Savannah Sanchez's creative process](https://thesocialsavannah.com/services) (undated; first-hand use, prior tests and iterative creative briefs). Practitioner methods inform proposed tests; their reported success does not prove transfer to this campaign.
