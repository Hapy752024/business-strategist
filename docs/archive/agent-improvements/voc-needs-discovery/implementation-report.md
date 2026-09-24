# VoC / customer-needs capability implementation

Date: 2026-09-16. Core implementation delivered. Final fresh code/content review:
**0 Blocker / 0 Significant** within the audited paths. Full research-quality
release acceptance is **not yet demonstrated**.

## Delivered

The plan was reviewed by a fresh agent before coding, then implemented with
independent collection and coverage work. Later reviewers found substantive
integration defects, which were corrected and tested. A final new reviewer
inspected the resulting implementation without editing it and found no relevant
remaining defect. No venture workspace or funeral-case research was changed.

| Original gap | Implemented closure |
| --- | --- |
| F1: heuristic editorial/provider labels exclude genuine local voices | Shared `reviewed_voice.py` permits located source/author corrections while preserving original labels; explicit supplier identity remains excluded. Corrections survive episode extraction and claim/interview consumers. |
| F2: generic entity capture lacks bindings | Exact reviewed URL capture through ordinary Firecrawl collector options writes entity, locale, lane and locator before extraction; broad entity search cannot masquerade as reviewed capture. |
| F3: missing market hidden by global topic counts | Topic coverage cells retain requested locale/job/role/source/intent; synthesis verifies cell-to-record locale provenance and every entity binding. |
| F4: one blocked platform suppresses useful findings | Invalid data blocks; unavailable/pending sources produce explicit gaps. Supported scoped findings remain possible; zero accepted voice yields insufficient evidence. |
| F5: pain-first interview truncation drops counterexamples | Selection preserves reviewed material counterexamples, then distinct perspectives, stages, jobs, alternatives and outcomes. Selection/omission reasons are written. |
| F6: fixed counts automatically validate/refute | Removed contradictory confirmation/refutation rules and blanket confidence thresholds. Claims require scoped, type-specific assessments. |
| F7: weak/strong label chooses research method | All three skills choose discovery/interviews/observation/behavioral tests from the named unanswered question. |

Broader capability work:

- Full Firecrawl page content replaces the 1,500-character truncation; snippets
  and unsegmented documents cannot directly become accepted customer voice.
- `build_experience_ledger.py` validates exact source spans, separates speakers,
  supplier replies and quoted others, and preserves original wording/translation
  and context proposals for later review. It is not an automatic semantic judge.
- Balanced Firecrawl/Serper query execution includes successful alternatives,
  non-adoption, switching, forums and Facebook. Native templates cover English,
  German, French, Spanish, Italian and Chinese; other languages preserve supplied
  native seeds and need runtime expansion rather than English-default coverage.
- Source sampling metadata records known choices and unknown limits. Apple RSS
  uses path pagination, detects repeated pages, preserves product version and
  exposes country-only language scope. Reviewed language resolution does not
  rewrite the original capture.
- Version-2 U/R synthesis requires contextual assessments, codebook links,
  bounded scope, contrary cases/search scope and question-driven follow-up.
  Supplier counterclaims cannot be counted as customer counter-evidence.
- Broad discovery now loads the same customer-voice method and finalizes against
  an actual reviewed v2 research pack, not headings alone. Candidate support
  must link to U IDs. Legacy artifacts remain visibly unassessed, not silently
  upgraded.

The skill-creator review influenced generic runtime inputs, direct method links,
preservation of original evidence and outcome-based evaluation. No new service,
database, package installation, advertising or outreach was introduced.

## Verification

- Pre-change focused baseline: 103 tests passed; baseline source archive retained
  at `/tmp/voc-implementation-baseline/research-code.tgz` (temporary, not a durable
  release artifact).
- Final focused implementation suite: **133 tests passed**, including ordinary reviewed forum
  capture → source-linked experience → coverage finalization → CLI synthesis,
  without manual repair of capture binding fields. These use synthetic provider
  payloads and do not measure open-web recall or semantic accuracy.
- `bash scripts/validate_setup.sh`: passed with **0 errors / 1 existing warning**
  after an approved outside-sandbox retry. The first sandbox run had nine
  unrelated Node subprocess/local-socket permission failures; no research code
  change was used to suppress those tests.
- `python3 scripts/validate_skill_routes.py`: passed.
- `python3 scripts/run_evals.py`: 150 case definitions, 0 structural errors;
  this validates evaluation structure, not model behavior. Existing unrelated
  town-db-curator evaluation/checklist warning remains.
- Skill-creator structural checks passed for evidence-scout,
  market-problem-discovery and interview-bridge. Live cross-host equivalence
  was not tested.
- Live development corpus integrity passed: three source-study sets, twelve
  exercises, six inspected source pages, four languages and two supplier controls.
  [Live evidence and limitations](live-evaluation.md) and
  [fixtures](../../../evals/voc/live/cases.json).

Repeat the focused checks:

```bash
python3 -m pytest -q tests/test_voc_research_quality.py tests/test_voc_collection_quality.py tests/test_voc_scoped_coverage.py tests/test_customer_feedback_plan.py tests/test_customer_feedback_completion.py tests/test_entity_review_collectors.py tests/test_interview_source_review.py tests/test_customer_voice_routing.py scripts/evidence_scout/test_market_discovery.py scripts/evidence_scout/test_interview_bridge.py scripts/evidence_scout/test_classification.py
python3 evals/voc/live/check_fixtures.py
```

## What remains before claiming research-quality release

The implementation is usable, but the entire original plan is not finished:

1. Complete the frozen twelve-study, roughly 240–360-source-unit corpus with
   development/held-out separation. The current twelve exercises are not twelve
   independent studies and must not be rebranded as holdout.
2. Independently adjudicate critical need/context concepts and contrary cases;
   run identical baseline/candidate inputs with blind comparison, per-language
   episode/need recall and assertion support scores. No numerical quality gain
   is claimed from the current unit tests or agent annotations.
3. Run complete live topic-led plus entity-led studies through the upgraded
   pipeline. The current live retrieval exercises deliberately disclose missing
   topic passes, entity verification, current local experiences and Facebook
   access; they do not satisfy those full-study criteria.
4. Prototype LangExtract/Trafilatura against a frozen baseline only if they can
   demonstrate a gain. Conceptual patterns were adopted; neither dependency was
   installed or benchmarked. BERTopic/UI deployments remain optional, not
   prerequisites or implied improvements.

The next substantial task is evaluation, not more architectural hardening or
minor edge-case optimization. Source review and semantic claim judgment remain
agent/analyst work: the new validators enforce traceability and scope but cannot
prove a motive or need merely because the JSON is well formed.

## Sources and review evidence

Checked 2026-09-16: [GOV.UK research analysis](https://www.gov.uk/service-manual/user-research/analyse-a-research-session),
[GOV.UK question-driven planning](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service),
[LangExtract](https://github.com/google/langextract),
[Apple review pagination implementation](https://github.com/facundoolano/app-store-scraper/blob/master/lib/reviews.js),
[Google Play review sampling](https://github.com/facundoolano/google-play-scraper#reviews).
Earlier repository/license research and adoption boundaries:
[open-source-research.md](open-source-research.md).
