# Open-source research for VoC and needs discovery

Checked: 2026-09-16. Scope: reusable research capability in this repository. Method: Firecrawl and web/GitHub discovery, primary repository documentation, GitHub API metadata, and selected source-code inspection. No shortlisted package was installed or executed, and no upstream performance claim was independently reproduced.

## Recommendation

Use complementary components and proven qualitative-research patterns. Among the inspected candidates, none establishes an end-to-end replacement for this agent's combination of open-market discovery, target-fit review, customer-needs interpretation and commercial-evidence boundaries. That is an assessment of this shortlist, not a claim that no such project exists.

Priority: test grounded extraction, adopt reversible source review and qualitative case comparison, and measure end-to-end research outputs. Keep existing paid discovery/capture routes. Defer a separate annotation UI or topic-modeling dependency until its benefit is demonstrated.

## Shortlist and disposition

GitHub `pushed_at` is an activity signal only, not a release date, stability claim or proof of maintenance quality. License names below come from repository metadata plus the inspected code header where indicated; adoption requires checking the selected version's license text.

| Project | Verified capability and concrete reference | License / latest repository push checked | Proposed use and limit |
|---|---|---|---|
| [Google LangExtract](https://github.com/google/langextract) | Structured extraction with source positions, chunking/multiple passes and review visualization. Inspected [data model](https://github.com/google/langextract/blob/main/langextract/core/data.py): `Extraction`, character intervals and exact/fuzzy alignment states; unmatched extraction can have no interval. | Apache-2.0; 2026-09-13 | Prototype episode/observation extraction. Reject ungrounded output as evidence; inspect fuzzy matches and separately review meaning, speaker and entity attribution. Grounding alone does not establish correctness. |
| [QualCoder](https://github.com/ccbogel/QualCoder) | Qualitative coding of text/media; inspected [codebook implementation](https://github.com/ccbogel/QualCoder/blob/master/src/qualcoder/codebook.py) with categories, nested codes, memos and frequencies; located [coded-segment reporting](https://github.com/ccbogel/QualCoder/blob/master/src/qualcoder/report_codes_by_segments.py). | Metadata LGPL-3.0; inspected header LGPL-3.0-or-later; 2026-09-14 | Model coded passages, context comparisons and analytic memos. Conceptual inspiration first; its desktop/PyQt runtime is unnecessary for this CLI agent. Code frequencies are not market prevalence. |
| [Taguette](https://github.com/remram44/taguette) | Text highlighting/tagging and exports; located [models](https://github.com/remram44/taguette/blob/master/taguette/database/models.py) and [exports](https://github.com/remram44/taguette/blob/master/taguette/export.py). GitHub is explicitly a mirror of [GitLab upstream](https://gitlab.com/remram44/taguette). | BSD-3-Clause; GitHub mirror push 2026-02-05 | Inspiration for a simple coded-excerpt review artifact and optional export. Check upstream before choosing a version; do not infer project inactivity from mirror timing. |
| [Argilla](https://github.com/argilla-io/argilla) | Reviewed datasets and model suggestions; inspected [suggestion schema](https://github.com/argilla-io/argilla/blob/develop/argilla-server/src/argilla_server/api/schemas/v1/suggestions.py), which identifies suggesting agent and score separately from response types. | Apache-2.0; 2026-09-14 | Adopt separation of model proposals and reviewed decisions in current sidecars. Optional UI only if review volume warrants it. A model score is not calibrated research confidence. |
| [Trafilatura](https://github.com/adbar/trafilatura) | HTML text, metadata and optional comment extraction; supports structured exports and local HTML inputs. | Apache-2.0; 2026-09-11 | Prototype content-recovery fallback using already fetched HTML. Benchmark against real forum/review fixtures: article extraction may discard important discussion structure. |
| [BERTopic](https://github.com/MaartenGr/BERTopic) | Embedding-based topic modeling; documented multilingual option and configurable representations. | MIT; 2026-09-09 | Optional grouping/navigation of reviewed observations at scale. Keep outliers and inspect merges; a topic is not automatically a customer need, and cluster size is not importance or demand. |
| [promptfoo](https://github.com/promptfoo/promptfoo) | Agent/prompt evaluation; official [assertions documentation](https://www.promptfoo.dev/docs/configuration/expected-outputs/) supports deterministic checks, custom Python/JavaScript and model-assisted rubrics. | MIT; 2026-09-16 | Candidate authoring-time evaluation runner for baseline/candidate comparisons. Calibrate semantic rubrics against source review; existing tests remain useful for deterministic mechanics. |
| [Rereflect](https://github.com/haqaliz/rereflect) | Self-hosted feedback intelligence; inspected [categorizer](https://github.com/haqaliz/rereflect/blob/master/services/analysis-engine/src/analyzer/categorizer.py). Its keyword taxonomy assigns preset severity and defaults unmatched text to `functionality_broken`, `major`, confidence `0.3`. | MIT; 2026-09-10 | Reference for feedback correction/evaluation workflow, not the needs-analysis core. Avoid importing its product-centric default categorization into exploratory discovery. README features beyond inspected code remain unverified claims. |

## Additional adapter references

- [Google Play Scraper](https://github.com/facundoolano/google-play-scraper#reviews): useful reference for explicit country/language, sort and pagination behavior. Inspect API limits and review/comment fields if the current paid app-store routes leave a demonstrated gap. No replacement is proposed solely because a free scraper exists.
- [Discourse API documentation](https://docs.discourse.org/): candidate for structured topic/post capture on compatible discovered forums. The documentation landing page was reachable but did not render endpoint details in this research tool; exact endpoint and pagination behavior must be verified before implementation. No capability is claimed tested from that landing page.

## Method references that influence the plan

- [GOV.UK: Learning about users and their needs](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs), updated 2017-03-23, checked 2026-09-16: supports investigating current behavior, context and problems, expressing needs independently of solutions, and tracing implementation back to needs. Applied to U/R separation, episode context and ongoing refinement.
- [GOV.UK: Plan user research for your service](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service), checked 2026-09-16: used as a reference for research questions, planning and method selection. Applied to choosing the next investigation from uncertainty rather than aggregate evidence strength.
- [GOV.UK: Analyse a research session](https://www.gov.uk/service-manual/user-research/analyse-a-research-session), checked during the preceding review on 2026-09-16: preserve observations separately from interpretation and subsequent action. Applied to the source-to-observation-to-need chain and review rubric.
- [Taguette primary project site](https://www.taguette.org/), checked 2026-09-16: establishes its qualitative text-coding purpose. Used with the repository rather than relying on third-party recommendation lists.

## Focused adoption experiments

1. **Extraction:** compare current normalization, a full-content structured extraction prompt, and a LangExtract adapter on identical frozen sources. Score episode recall, exact quote grounding, speaker attribution, negation/chronology and multilingual behavior. Pin version/model/settings. A positional match cannot compensate for incorrect meaning.
2. **Content recovery:** compare existing Firecrawl output and Trafilatura on the same source snapshots. Check whether post boundaries, replies, quoted text, dates and contradictory later comments survive. Retain a fallback only where it materially improves recovery.
3. **Review model:** implement proposal/review separation in the current file-based workflow, borrowing the Argilla distinction. Test correcting erroneous heuristic labels while preserving verified supplier attribution and original text.
4. **Qualitative synthesis:** build a codebook and case-by-context comparison from reviewed passages, inspired by QualCoder/Taguette. Evaluate whether distinct outcomes and successful alternatives remain visible and whether resulting U/R interpretations help answer the research questions.
5. **Evaluation:** compare the current structural checks with source-grounded assertions and independent semantic grading. Trial promptfoo only as an evaluation tool; continue with the existing runner if it provides the same repeatability with less integration work.

No dependency is selected by stars, recent commits, a README claim or a generic leaderboard. Integration is justified by measured research-quality improvement on this agent's actual workload.

## Retrieval limitations

The first sandboxed Firecrawl request failed DNS resolution. The approved retry using `FIRECRAWL_API_KEY_HGINVESTOR` succeeded and returned six discovery results. Primary GitHub/web retrieval supplied repository and code verification. No insufficient-credit response occurred.

Provider-doctor output contained stale prior checks for several unrelated providers and sandbox-limited optional probes. It is not a current outage assessment. This research did not exercise live Facebook, Trustpilot, Google Places or app-store collection and makes no new claim about their current operational coverage.
