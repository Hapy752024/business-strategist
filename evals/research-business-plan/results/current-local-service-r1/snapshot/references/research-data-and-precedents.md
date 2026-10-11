# Decision-led data research and commercial precedents

Read for substantive Business research. Narrow factual questions retain their scope. Reuse the existing query plan's `research_design`: record the decision, questions, claim scope, customer population, geography/language, relevant source families and unresolved gaps. Iterate between provisional segments, official statistics/studies and customer experiences; do not infer a segment solely from available demographic columns.

## Sources and review

Select sources through `scripts/capability_lookup.py`. Official statistics can supply denominators and measured behavior where definitions match. Studies can explain mechanisms and prevalence where methods support it. Topic-led customer voice and independent entity feedback remain separate required sampling frames for substantive customer-input work. Supplier claims, investment signals and customer behavior retain their distinct roles.

Direct adapters live under `scripts/market_research/`: `fetch_eurostat.py`, `fetch_swiss_stats.py`, `search_opendata_swiss.py`, `fetch_census.py`, `fetch_bls.py`, `search_openalex.py`, `search_crossref.py`. Use `--help`, a fresh explicit `--out` directory inside the current run, and narrow dataset/dimension/query parameters. Discover dataset IDs and definitions before requesting observations. Public CORDIS, Eurofound, ARAMIS, KOF, regulator/ombudsman, association and university documents use existing search/extraction routes; do not claim dedicated API coverage where none was checked.

The adapters save `capture.json`, `research-facts.jsonl` and `summary.json`. Capture status does not certify findings. Facts retain original locators, dates, units, populations, flags and digests; unknown inputs stay unknown. Discovery metadata is not customer voice or a substantive paper finding. Read original study findings/methods; state abstract-only or inaccessible-full-text limitations.

Review facts with `scripts/market_research/research_facts.py --facts <run>/research-facts.jsonl --reviews <review.json> --out <run>/reviewed-facts.jsonl`. Each decision names the evidence ID, authored fact digest, status, reviewer, date and rationale. Accepted facts remain bound to their original capture. Retain the semantic review, contextual definitions and counterevidence; deterministic checks establish consistency, not truth. Publication references use `fact_binding`, `claim_scope` (`metadata` or `finding`) and an exact retained supporting passage. Bind both the fact file and its original capture through existing source-use bindings.

## International commercial evidence

For substantive chosen-idea validation, run a targeted international-comparables pass or record why it is inapplicable. Choose markets with an informative established category or comparable customer workflow; US/Japan are optional examples. Record the choice rationale. Search native-language sources as well as English using reviewed local keywords; `discover_competitors.py --analog-locale 'CC:language=local topic keywords'` preserves each query's locale.

Keep local competitors, similar companies and capability references in their existing lanes. The similar-company lane can support a commercial precedent, with observation strength increasing from existence to purchases, repeat/retained value and viable economics. Keep these findings separately sourced; unknown revenue/profit remains unknown. Check independent customer feedback and operator outcomes, not only company websites. Include relevant closures, pivots, failed expansion and unfunded successful companies to counter survivor bias.

Assess transfer conditions: customer job and buyer/payer, behavior, income/pricing, regulation, distribution, service/labor costs, trust and founder resources. State which mechanism is supported and the local evidence or test still needed. Foreign commercial evidence never changes local competitive counts merely because the company is similar.

## Investor activity and synthesis

Apply `vc-investment-signals.md` for venture-scale cases or an explicit request for this input. A small non-VC business can record financing irrelevance without failing business validation. Use investor activity to identify precedents, capital requirements, competing funded entrants and financing patterns; check material rounds and outcomes. Funding alone cannot support customer-purchase, retention, profit or local demand claims.

Merge all streams by claim and scope in current insights. Deduplicate studies by identity/DOI, statistics by their population/dataset, copied announcements by originating source and customer accounts by incident. Multiple providers or agreeing models are not independent observations. Reconcile segment differences, contrary evidence, numeric definitions and decision-changing gaps before appraisal and per-case planning. Publish coherent progress while stating unfinished work. Collection, reviewed research, case-plan publication and execution are different milestones.
