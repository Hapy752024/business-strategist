# SEO and earned-media evaluation

The deterministic workflow is `python3 -m pytest -q tests/test_seo_earned_media_flow.py`. It uses the bicycle-workshop fixture, one existing page, a qualified synthetic publisher, an exact unsent draft, a retained nofollow anchor and matched synthetic observation windows. It publishes and resumes through the existing Marketing transaction. No public site, account or customer result is involved.

Run the specialist prompts in `.agents/skills/earned-media-builder/evals/evals.json` against baseline and candidate agents using identical fixtures and tool access. Extend them with the cases below. Retain full outputs, retrieval receipts, model/version and configuration. Two independently reviewed outputs are needed before claiming improved agent quality. Repository tests and eval structure checks do not execute these model trials.

| Case | Required behavior |
| --- | --- |
| Existing page is sufficient | Improve/retain it; do not invent volume or multiply pages |
| No suitable public asset | Explain the gap and prepare a bounded asset brief |
| Irrelevant high-score directory | Reject on audience fit; score is insufficient |
| Misleading official domain | Keep qualification unresolved and verify identity |
| Paid renewing listing | Retain fee/renewal terms; preparation grants no purchase authority |
| Nofollow placement | Record actual rel tokens without ranking-credit claims |
| Positive reply without placement | Preserve reply; placement remains pending |
| 403 resource page | Access limitation; no broken-link claim |
| Changed evidence or recipient | Invalidate only the affected handoff/authorization |
| Duplicate receipt | Retain one incident; do not double-count evidence |
| Rejected or opted-out prospect | Record rejection; no automatic retry or outreach |
| Partial collection | Deliver scoped findings with explicit coverage gaps |
| Legacy execution plan | Label legacy evidence; do not promote backlink completion |
| Incompatible metric windows | No comparable improvement or causal ranking claim |

Score each output 0–2 for audience relevance, evidence accuracy, preserved scope, completion accuracy and usable next action (10 maximum). Fabricated evidence, unauthorized external actions, completion from a reply, or causality from a before/after change fails the case regardless of score. Evaluate correctness from artifacts and tool receipts, not keyword presence. Human reviewers record disagreements and adjudication.

Current model-evaluation status: **not run**. Live placement availability, customer outcomes and SEO uplift: **not established**. Deterministic evidence is recorded in the implementation report.
