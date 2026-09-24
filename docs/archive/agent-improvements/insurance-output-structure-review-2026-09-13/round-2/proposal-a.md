# Finalist A — additive idea library, one scoped assessment authority

Round 2, 13 September 2026. Revised after the judge, B/C proposals and common source packet. Design only; insurance claims were not revalidated. Paths below are relative to the insurance project unless marked repository paths.

## Founder experience and taxonomy

Keep one venture and existing evidence destinations. Add an `ideas/` library: each investigated possibility has a readable current dossier, while the root README compares them directly. English, Chinese, motor and Arabic doctors each have their own root-table link: one click to the dossier, a second to supporting evidence. Parked alternatives remain visible with dated rationale and reopening conditions.

An **idea** has a separately decidable customer/job/value or economics hypothesis. A **facet** is language, profession, product, geography or channel. A **variant** is a facet combination actually investigated separately. An experiment tests an uncertainty; it is not automatically another idea. Facets permit overlap without multiplying all combinations.

```text
README.md                              # current umbrella narrative + derived table
ideas/
  index.json                           # identity, kinds, relations, paths ONLY
  personal-insurance-decisions/
    brief.md                           # health, BU, sickness-income; broad scope
    english-speaking-residents.md
    chinese-speaking-residents.md
    japanese-and-korean-comparisons.md
  professional-and-personal-cover/
    brief.md
    independent-it-consultants.md
    doctors.md
    arabic-speaking-doctors.md
    other-investigated-professions.md
  discounted-motor-cover/brief.md
  cyber-readiness-and-placement/brief.md
  retirement-decision-support/
    brief.md
    self-employed.md
    age-55-plus.md
  broker-portfolio-acquisition/brief.md
  related/surelius-and-simulation.md
  related/register-mail.md
market_research/
  manifest.json                       # existing state + idea_assessments[ID]
  customer_segments/…                 # existing and future stage outputs
  customer_journey/…
  pain_points/runs/…                  # frozen originals; new scoped runs here
  deep_dives/…                        # shared reports retained once
strategy/decisions/…                   # dated snapshots/correction narratives
```

Arabic doctors has one dossier cross-linked from language and professional views; its evidence is not copied. The personal parent explicitly preserves BU and sickness-income work, not merely GKV/PKV. A parked motor-MGA judgment concerns that implementation under recorded constraints, not every discounted-car-insurance concept. Surelius/simulation and register mail are typed related capability/channel entries unless a distinct commercial investigation justifies promotion. Broker acquisition remains discoverable as an operating path. Mentioned-only possibilities receive a list entry, not empty folders.

## Authority: no separately maintained card state

| Information | Single authoritative home | Derived readers |
|---|---|---|
| ID, kind, label, facets, related IDs, dossier path | `ideas/index.json` | Folder navigation and grouping |
| Disposition, conclusion, scoped narrative sections, next research action, review date | `market_research/manifest.json:idea_assessments[ID]` | Entire dossier and root comparison row |
| Readiness, segment/journey/pain coverage, evidence bindings and assessment revision | Same candidate record | Dossier status and admission result |
| Existing umbrella stage state and blockers | Existing fields of the research manifest | Controller summary through existing `next_actions` behavior |
| Prior decisions/corrections | Scoped append-only manifest events; linked immutable records in `strategy/decisions/` | Dossier history links |

Dossiers are generated Markdown, not a second editable authority. Canonical fields include `disposition`, `conclusion`, `findings_markdown`, `counter_evidence_markdown`, `next_action`, `review_state`, `readiness`, `bindings`, `revision`. Readiness concerns the **named scope**, never inherits a parent or umbrella pass. Root narrative remains the sole authored portfolio recommendation; it cannot override candidate state. Its comparison/status sections are derived, and contradictory portfolio prose fails substantive review before publication. Generated dossiers/table carry their input revision; resume compares it with authority and flags or rebuilds stale views after interrupted rendering.

Migration starts candidate readiness at `not_assessed`; conflicting decisions become `needs_reconciliation`. A finished report, shortlisted option and passed validation are distinct. This adds structured authored narrative inside the existing JSON manifest, a real editing inconvenience accepted to eliminate duplicated mutable summaries. A small update command and rendering step are required; hand-editing projections is unsupported.

## Supported continuation and admission boundary

This option supports independently scoped **desk research, evidence review and recruitment planning**. It does not support independent full stage progression, live recruitment, launches or downstream execution merely because an assessment exists.

Minimum implementation includes an explicit `--idea <ID>` resolver, safe run destination allocation, locked revision-checked assessment updates, source-consumer invalidation and candidate-aware admission in routing and the shared stage-update boundary. Unknown/omitted ID for candidate work, stale bindings and attempted unscoped fallback fail. Assessment updates cannot call generic `update_stage` and overwrite umbrella stage/next-action fields. Candidate commitment and full stage transitions return `scoped_execution_unsupported`; this limitation is enforced, not left as a caution in prose. Existing user-authorized overrides must remain explicit and scoped, but cannot enable an unimplemented transition mechanism.

Full independent progression would additionally require candidate-keyed stage transitions, explicit scoped override history, downstream evidence snapshots/handoffs and operation-specific authorization. That is the upgrade boundary; B supplies a more complete long-term ownership model. This option deliberately implements scoped readiness and blocking now, while limiting what that readiness can authorize.

**Chinese-only resume:**

1. Resolve `personal-chinese` using the identity registry; read its assessment, current binding corrections, linked relevant source passages and common founder constraints. Read the umbrella manifest for global constraints, not to borrow its pass.
2. Plan a bounded follow-up using the candidate's own next action. A new evidence run writes `market_research/pain_points/runs/<timestamp>-personal-chinese/`; a scoped narrative may write `deep_dives/<date>-personal-chinese.md`. Run metadata identifies the ID. The collector must use a no-stage-transition path; existing collection behavior must be checked and adapted before enabling this mode.
3. Under the existing research-manifest lock, check the expected manifest and candidate revisions, merge only `idea_assessments[personal-chinese]`, add a scoped event, and advance the manifest revision. A stale writer must reread, not overwrite. Regenerate the Chinese dossier and root row.
4. Motor assessment, disposition, next action and run bytes remain identical. If new material could change a shared conclusion, open an explicit correction/review event; do not silently rewrite English or motor.

**Cyber admission:** a request to advance cyber cannot consume the historical root `problem_validation: passed/conditional_pass`. A missing/unreviewed cyber assessment produces `candidate_evidence_unassessed`; even a reviewed assessment cannot launch under this research-only contract. No project-wide reset or historical gate rewrite is needed.

## Shared-source correction: concrete trace

Suppose review finds an error in a claim from `customer_segments/surelius-and-language-segments.md` used by English and Chinese dossiers. This is a hypothetical correction workflow, not a newly discovered market error.

1. Preserve original bytes. Write `strategy/decisions/<date>-language-claim-correction.md` with source path, record/section selector, old claim, corrected interpretation, reason, reviewer and replacement-source locator if available. Append a correction event with a new correction revision.
2. Scan **all** candidate bindings for that source/claim. A binding stores source locator, selector, immutable artifact digest where appropriate, reviewed correction revision and applicability. Admission-relevant derived claims must declare original-source dependencies; otherwise invalidate all consumers of their affected report. The system does not infer semantic dependencies. Broad or unresolved selectors cause conservative stale marking; no reliance on changed bytes alone.
3. In the locked update, mark affected assessments `needs_review`, invalidate readiness and mark affected conclusions “under review.” Preserve their last disposition as a historical decision, visibly suspended as current guidance. Derived dossier banners and root rows refresh. Motor is untouched when it has no dependent binding.
4. The source-reviewing agent reassesses each affected scope separately, recording whether the correction changes or preserves its conclusion and why. Reopening requires all affected bindings reviewed at the current correction revision and explicit reassessment; restoring a hash or producing another report is insufficient. Selecting or launching still needs its own authority.

Admission repeats the correction-revision comparison, so interrupted rendering cannot leave a stale candidate executable. A failed or unknown consumer scan blocks candidate admission until repaired. This is necessary new behavior, not a feature already established by external examples.

## Concrete migration treatments

| Actual existing material | Treatment and reader destination |
|---|---|
| `strategy/intake/ideas/idea-1-personal.md` | Keep dated original; broad personal dossier preserves health/BU/income scope. |
| `strategy/annex-a-personal-insurance.md`; `customer_segments/surelius-and-language-segments.md`; four-language run | Keep shared originals; bind relevant sections to EN/ZH/JP-KR; retain coverage inequalities. |
| `strategy/intake/ideas/idea-2-professionals.md`; profession analysis; self-employment journey | Shared originals remain; separate IT/doctors assessments, retaining combined cover. |
| `strategy/arabic-brokerage-assessment.md` | Keep original; dedicated Arabic-doctor dossier and cross-links. |
| `strategy/annex-b-motor-mga.md`; motor pain run | Bind motor dossier; preserve specific historical stop/park scope. |
| September 11 multi-topic deep dives | Keep once; section bindings feed cyber, retirement, 55+ and related entries. |
| `strategy/annex-c-broker-succession.md` | Bind visible broker-acquisition operating-path dossier. |
| `README.md`; `strategy/current-recommendation.md`; current-looking annex banners | Snapshot originals before edits. Rewrite root current synthesis; add dated superseded banners and correct direct-entry links in old narratives. |
| June multilingual GTM/app/social files | Historical proposals linked from relevant dossiers; no current execution approval imported. |

Abbreviated research paths above are under `market_research/`. No original source/run is moved. Dossiers are **new synthesis**, not renamed originals. Ambiguous attribution goes into a migration exception list until reviewed; no unsupported claim receives a precise candidate assignment. Inventory remaining professional/related mentions before asserting coverage completeness.

Back up local-only files outside the active tree; record additions, modified narratives/manifests and protected hashes. Validate the existing nine sampled broken links and then full local targets/anchors, candidate coverage, projections and correction scenarios. Rollback restores backed-up mutable files and removes only mapped additions; unchanged evidence is verified. This review authorizes no migration.

## Cross-pollination, grounding and trade-off

| Source idea | Borrowed or rejected | Reason |
|---|---|---|
| C: idea/facet/variant and candidate assessment | Borrowed | Honest overlap and scoped evidence coverage. |
| B: identity-only registry | Borrowed | Prevent status/next-action duplication. |
| B: nested case manifests/future case storage | Rejected here | Changes more execution/storage contracts than narrow follow-ups require. |
| A Round 1: defer scoped readiness; mutable index + cards | Rejected | Would preserve unsafe inheritance and authority drift. |
| Judge: corrections, supersession, resume | Incorporated | References alone cannot invalidate dependent conclusions. |

[Spec Kit scope/decomposition](https://github.com/github/spec-kit/blob/main/docs/concepts/spec-of-specs.md) supports explicit units while warning about independent-cycle overhead. [BMad proportional planning](https://docs.bmad-method.org/cs/plan/choose-a-planning-path/) supports limited scaffolding. [GPT Researcher](https://github.com/assafelovic/gpt-researcher/blob/main/README.md) supports preserving reports separately from current decisions. Common packet retrieved 2026-09-13; these are bounded analogies, not proof of correction propagation or this folder design.

Compared with B, one research manifest, existing stage destinations and no child lifecycle/handoff machinery remain. Costs still include rendering, scoped updates/admission and correction review. A central manifest serializes updates and can grow; summaries do not make raw files physically self-contained by idea. Choose this when understanding and bounded follow-ups dominate. Separate ventures require an explicitly selected independent operating lifecycle/ownership, budgets and delivery—not merely another language or independently reviewed evidence.
