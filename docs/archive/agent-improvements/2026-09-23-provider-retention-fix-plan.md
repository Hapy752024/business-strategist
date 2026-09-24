# Plan: preserve enrichment, balance sources and checkpoint research

Status: planned, not implemented. Scope is the two confirmed defects in `docs/audits/research-query-expansion-2026-09-23/review.md`, plus the requested source-agent and incremental-documentation approach.

## Design decision

The user's source-agent suggestion is design input, not an instruction to launch agents. Recommendation: implement deterministic source allocation and incremental persistence first. Consider optional separate agents for source families only when different retrieval methods or interpretation tasks justify the extra orchestration. If selected, each gets concise context, a source remit and its own output directory; a coordinator owns comparable coverage, deduplication and conclusions. A source means an evidence lane, not necessarily an API vendor: TikTok, Instagram and Threads are separate lanes even when one provider retrieves all three.

Agent separation helps attention, attribution and parallel retrieval, but cannot repair a collector that discards fetched data. Fix deterministic retention first. An agent must not silently compensate for a defective collector or claim coverage merely because a source worker completed.

## 1. YouTube transcript retention

- Persist each successfully fetched transcript immediately as a raw text/JSON sidecar with video ID, requested/actual language when available, retrieval time, status and content digest. Do this before record selection and before the next request.
- Treat requested transcript enrichment separately from search-result retention. Retain its normalized creator-voice record when successfully fetched within `--youtube-transcript-max`; do not subject it to the outer `found[:per_query_result_limit]` slice.
- Define allocation units explicitly: search/discovery selection, comment capture and transcript enrichment. Reuse existing caps where possible and show the units in preview/summary. Preserve the total HTTP request budget. Do not count transcripts as independent customer testimony.
- Track attempted, fetched, persisted, retained and omitted/failed enrichment separately. A fetched transcript that fails persistence cannot be reported as a clean completed capture. Preserve retry information and disclose partial coverage.
- Preserve the run-wide transcript cap across queries, deduplicate by video identity, and retain query memberships for rediscovered videos/transcripts.

Acceptance: the adversarial five-record example retains the exact transcript text in a raw artifact and its requested evidence record; metadata/comments cannot consume its allowance. Summary counts reconcile with files and record IDs. Also cover transcript failure, multiple queries finding the same video, interruption after persistence, and exhausted transcript/request budgets.

## 2. Social-source allocation and comment selection

- Plan TikTok, Instagram and Threads as distinct source lanes. Fetch within each endpoint's bound and persist its response immediately.
- Replace fixed-order consumption of the shared query allowance with explicit lane allocation or round-robin selection among valid candidates. Default to one from each available requested lane before additional records from any lane.
- If the allocation cannot cover every lane, expose that before execution and record exactly which lanes are omitted. Do not label full source coverage. Failed/empty lanes remain distinguishable from lanes excluded by allocation.
- Keep independent counts for returned, valid, retained, duplicate, excluded by allocation, and missing-text items. Remove the inference that zero new retained records means `items_without_text`.
- Schedule optional comments from the intended retained eligible parent lanes. Preserve all candidate/query memberships when a parent is rediscovered. Record parent selection and comments-cap exclusions explicitly.

Acceptance: the three-platform/three-record reproduction retains one valid post per available lane, schedules eligible Instagram comments when enabled, and reports actual allocation exclusions. Also cover source-order permutations, duplicate posts, empty/failed endpoints, smaller-than-lane-count allocations and exhausted comment/credit/request budgets.

## 3. Optional source agents with separate context

Each bounded worker receives only: the research questions and falsifiers; geography/languages; prior relevant source references; source-specific access instructions; allowed retrieval method; explicit allocation; its own output directory; and a required handoff format. Do not fork the entire conversation by default.

Workers must:

1. Save the query/source plan before retrieval, including vocabulary and alternative explanations.
2. Persist every useful capture or failed-access receipt when it arrives.
3. Append a candidate entry immediately; mark snippets as unreviewed leads.
4. Save a located experience once the original speaker/context is checked, with supporting and contrary evidence distinguished.
5. Notify the coordinator of material findings or lost source coverage while continuing independent work.

The coordinator deduplicates canonical URLs and source-local speaker/episode identities across workers. One person, cross-post or quoted passage is not multiple independent observations. A worker's finished status does not establish complete coverage or demand. If a source lane is unavailable, retain that gap and use an authorized fallback without silently changing its claimed sample.

## 4. Incremental artifacts and recovery

Prefer the existing run folders and JSON/JSONL helpers over a new storage system. Give each worker exclusive ownership of its source directory; only the coordinator writes shared synthesis/index artifacts.

Persist in this order:

1. Raw response/capture (or failure receipt), written atomically.
2. Source index entry with URL, retrieval/publication dates, language, digest, status and raw path.
3. Candidate or located-episode entry with hypothesis IDs, exact locator, short quotation/paraphrase, speaker role, geography basis, relevance, limitations and review state.
4. Running findings note with separate observation, interpretation, counter-evidence and open question.

Use stable source/capture IDs and append-only events for corrections. Mark incomplete writes/captures explicitly; a restart must inspect completed artifacts and avoid unnecessary refetching. Do not promote an unreviewed candidate merely because it was persisted. Existing signed community/entity capture controls still apply.

Acceptance: interrupt after the first useful source, resume, and verify that its capture, locator, hypothesis association and review state remain available, duplicates are not double-counted, and failed capture is not reported as complete. Test two workers writing distinct source directories and coordinator merge without shared-file races.

## Implementation sequence and review

1. Turn the two saved adversarial reproductions into failing regression assertions.
2. Implement transcript persistence and separate enrichment retention.
3. Implement balanced social-lane selection and truthful dispositions/comment scheduling.
4. Add incremental checkpoints to these changed capture paths; document allocation units and recovery.
5. Document source-worker guidance as an optional execution pattern. Exercise incremental capture in a bounded research task; do not require or launch a worker per source merely to fix these bugs.
6. Run focused execution/schema/capture-gate checks, then repository validation. Have an independent reviewer rerun the adversarial cases against saved output artifacts before closing either defect.

The subsequent German insurance research will exercise incremental documentation using web/forum retrieval without relying on the two affected capture paths. No source agents are launched based on the suggestion. That practical exercise does not mark the collector defects fixed or validate willingness to pay.

## Web research supporting the design

Official documentation retrieved 23 September 2026:

| Source | What it supports | Application and limit |
|---|---|---|
| [Python itertools recipes](https://docs.python.org/3/library/itertools.html#itertools-recipes) | Round-robin iteration takes turns across input iterables and removes exhausted inputs. | Use source queues to prevent fixed-order starvation. Choosing one per platform is our sampling decision, not proof of representativeness. |
| [Python os.replace](https://docs.python.org/3/library/os.html#os.replace) | Successful replacement is atomic; cross-filesystem replacement can fail. | Write a temporary capture beside its destination and replace it on the same filesystem. Atomic visibility is not a claim of power-loss durability; flush/fsync requirements should be explicit if that guarantee is needed. |
| [Scrapy feed exports](https://docs.scrapy.org/en/latest/topics/feed-exports.html#delayed-file-delivery) | Some storage backends deliver only at crawl end; batch exports allow earlier delivery. JSON Lines is supported. | Save local captures immediately and checkpoint item batches instead of waiting for final synthesis. This is a pattern reference, not a recommendation to migrate collectors to Scrapy. |
| [Scrapy job persistence](https://docs.scrapy.org/en/latest/topics/jobs.html) | Persistent jobs can resume after a clean stop; distinct jobs must not share their job directory. | Use separate run/source directories and explicit restart tests. Do not claim arbitrary crash recovery solely from this example. |
| [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) | Checkpointing preserves graph state across execution steps. | Persist capture and review state at useful boundaries; no new framework is required for the existing scripts. |
| [LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents) | Isolated subagents can receive focused context; a supervisor controls context passed in and results returned. | Supports the user's context-isolation idea. It does not prevent a shared collector's destructive slice, ensure fair platform retention or make returned summaries a substitute for saved source artifacts. |

These sources support established implementation patterns. The diagnosis and acceptance conditions come from this repository's reproduced failures; the recommended combination is an engineering judgment, not an externally validated fix for this code.
