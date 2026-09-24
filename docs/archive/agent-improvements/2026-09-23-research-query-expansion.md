# Research query improvements beyond customer pain

Implemented 23 September 2026, following the German/English customer-pain pilot and the user's authorization to extend the method to the five deferred research areas.

## Delivered behavior

| Area | Change |
|---|---|
| Other collection providers | HN, GitHub, autocomplete, YouTube, X, xAI discovery and ScrapeCreators keyword searches now consume scheduled query candidates. Short plans no longer rely on fixed indexes. Per-query allocations, attempted/failed/skipped statuses, raw requests and duplicate candidate memberships remain inspectable. Social vocabulary is no longer silently truncated to three terms. |
| Market-problem discovery | Forwards topic/audience vocabulary, exact query plans, query/result allocations, request budgets and preview controls. Workflow now requires vocabulary/source brainstorming and analyst review before broad collection, followed by source-derived refinement. |
| Founder/operator research | Replaces the long English search sentence and hardcoded English keywords with separate local situations. Built-in vocabulary covers English, German, French, Spanish and Italian; other languages accept explicit operator vocabulary or exact plans. Non-English generated plans require local topic keywords. Preview validates the collector command before project writes. |
| Competitor discovery | Local category/audience seeds and localized provider/substitute terms; exact plans bind query candidates to competition, analog or capability lanes. Both search providers execute selected queries independently of shortlist size. Firecrawl no longer truncates to four queries. The audit retains all discovered candidates before shortlisting. Known-company lookup no longer injects German insurance terms into unrelated research. |
| Community discovery | Adds a preview without signing keys or project writes and optional analyst review metadata with revision, parent digest and source-derived seed locators. Existing complete locale/source coverage checks and signed capture controls remain in force. |

The shared method is documented in `references/research-query-calibration.md` and applied by the four affected skills. It separates research briefs from local query vocabulary, reviews source locations before collection, and measures fresh useful sources separately from rediscovered seed pages. Customer testimony, operator accounts, supplier claims and community leads retain different evidence standards.

## Contracts and implementation choices

- Reused `schemas/pain-query-plan.schema.json` rather than introducing an incompatible second exact-plan format. The shared schema now supports additional providers, operator/competitor intents and optional competitor lane fields. Competitor execution requires those lane bindings.
- Exact collector plans retain the existing explicit locale/provider match and sufficient total result allocation requirement. Source-derived seeds require source locators. Revision notes and parent digests record lineage, not authenticated evidence approval.
- HN/GitHub/autocomplete/YouTube/X/xAI adapters run one scheduled candidate at a time and retain per-candidate raw captures. Deduplication uses source-record identity, keeping multiple query memberships. HN samples story and comment lanes within a query's allocation.
- YouTube allocations count retained records, including metadata, comments and transcripts. Raw responses preserve larger result sets; transcript limits remain shared across queries. Failed enrichment is disclosed as partial coverage.
- ScrapeCreators records each keyword endpoint's outcome. Optional comments and requested entity/community targets keep their own controls. Duplicate-parent query memberships propagate to captured comments. No new Facebook capture authorization is implied.
- GitHub appends issue/date filters and X appends language/retweet filters; raw requests show these transformations. xAI gets one seed in its prompt, but its underlying queries are not observable and are not claimed as exact execution.
- Competitor query limits apply per provider per lane. Result depth and shortlist size are separate. Exact competitor plans do not trigger additional implicit known-company lookup queries. Country hints do not verify original source language or audience residence.
- Operator default providers are now `serper_search,youtube,hn`; alternatives are explicit. Generated operator plans require explicit country/language. The command reference was updated accordingly.
- Community query-review notes supplement the signed discovery audit; they neither replace source verification nor authorize capture. Reviewed seed/locale pairs must match the actual plan.

No project evidence, business selection or validation status was advanced. Existing unrelated website/search-visibility changes were preserved.

## Validation

- `bash scripts/validate_setup.sh`: **833 repository tests passed**, setup **0 errors** and one existing `town-db-curator` checklist warning. The sandbox run hit unrelated local-socket/website-process restrictions; the successful run used the approved unrestricted execution.
- After adding four final regression cases, the focused suite passed **206 tests**, including all **61 new research-expansion cases**, existing pain-plan tests, entity collectors, community controls and competitive-landscape pipeline tests.
- `python3 scripts/evidence_scout/test_classification.py`: **17 passed**.
- `python3 scripts/run_evals.py`: **170 skill cases**, **31 routing cases**, **0 structural errors**; existing missing town-db-curator eval warning.
- Skill-creator validation: all four changed skills structurally valid. Shared guidance is explicitly a repository dependency, consistent with the existing script/reference dependencies.
- Real CLI previews exercised French market/operator discovery and German competitor discovery. Japanese community preview required neither signing credentials nor project writes. Regression cases also cover Japanese and source-linked refinements.
- Python compilation and `git diff --check` passed.

Tests verify actual outbound query payloads using synthetic provider responses, including full first responses, duplicate results, missing credentials, request exhaustion, credit failures, empty success, and partial enrichment. They also verify lane attribution, preview side effects, original plan preservation and parent/seed metadata.

These checks establish local execution/provenance behavior. They do not establish live provider yields, representative research coverage, native-language query quality or runtime behavior on other agent hosts. No new live market/operator/competitor/community research benchmark was run in this implementation turn. Review was inline, not independent or blind.
