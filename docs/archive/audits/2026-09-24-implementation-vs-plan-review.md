# Implementation versus plan review

Reviewed 24 September 2026 against the current working tree, the analysis-quality implementation plan and the SaaS discovery approaches plan. This is a code and artifact review; no live retrieval, model comparison or host compaction was run. Existing unrelated changes were preserved.

## Verdict

The plans are partially implemented. The remaining work includes reproducible implementation defects and missing producers/consumers, not only independent evaluation. The previous full-suite result does not describe the latest files: the evaluation test fails after packet references were added.

## Findings, ordered by consequence

### 1. High — retrying partial providers can discard already captured evidence (P1; SaaS batch 2)

`scripts/evidence_scout/collect.py:4800-4806` restores records only for terminal/successful provider checkpoints. A partial provider is retried without loading its previous accepted records. At lines 4869-4874 its checkpoint is replaced with the new attempt's accepted records; despite its name, `append_jsonl` at lines 90-97 replaces the entire file. Final evidence assembly also replaces its output at line 4879.

Thus an initial partial response containing useful records followed by an empty or failed retry can remove those records from the current checkpoint and assembled evidence. If the persisted request allowance is exhausted, the provider is skipped and its partial records are still absent from assembled evidence. This is a code-path finding, not a live provider reproduction.

Required correction: restore durable accepted captures independently of provider completion; retry incomplete operations and merge stable records/memberships. Exercise partial-with-records followed by empty/failing retry, exhausted allowance, and interruption after normalized persistence. Query-level durability is also still missing: persistence happens after a provider returns.

### 2. High — downstream applicability and Marketing handoff consumption are not implemented (P4, P6; SaaS batch 2)

`scripts/evidence_scout/workspace.py:180-205` records geography, segment and limits, but `_receipt_current` checks case/revision and file hashes without comparing the intended downstream use to that scope. The router's pain gate does not take a destination segment/job/market or reviewed narrower applicability decision. Source freshness therefore does not establish that the new use is permitted by the finding's scope.

`scripts/subprojects.py:74-78` creates a Marketing workstream containing brief hash, artifact references and imported decisions. A repository search finds no script consumer of `workstream.json` or `imported_decisions` beyond this initializer. The schema describes a handoff, but there is no Marketing publication path maintaining the workstream or validating imported decisions/current source hashes. Calling the generic publication helper to initialize files is not this planned lifecycle.

Required correction: consume and revalidate scoped handoffs at routing/publication, preserve limitations, and require review on changed or broader inputs. Maintain Marketing workstream revisions and artifacts through the existing publication machinery. Test changed upstream input, reviewed narrower use, wider use, and stale/current scoped overrides.

### 3. High — registered Marketing destination is ignored when writing (P6.3; SaaS batch 2)

`scripts/subprojects.py:64` resolves the registered path, but line 68 resets the write prefix to `PATHS[name]`. The function then returns the registered path after writing elsewhere.

Isolated reproduction: initialized an umbrella project, registered Marketing at `custom-marketing`, then called `start(..., 'marketing')`. Result: returned `custom-marketing`; that directory did not exist; `marketing/workstream.json` existed instead. This can put authoritative outputs outside the destination the router tells the specialist to use.

Required correction: derive publication paths from the resolved registered destination and exercise initialization and continuation with custom paths.

### 4. High — evaluation packets and runner cannot yet perform the planned comparison (P0/P7; SaaS batch 6)

The packets are still scenario descriptions. For example, `evals/voc/packets/dev-multilingual.json:12` describes a Spanish post in English without the original Spanish span or translation pair. Its date conflicts with the date mentioned in the description. `dev-entity-feedback.json` labels a combined customer quote and supplier reply as one customer evidence item. Module packets such as `evals/modules/website/packets/website-form.json:5` assert that A lacks labels and B supports keyboard use, but provide no form, rendered fixture or saved outputs. Branding packets similarly omit the brief and assets required to judge consistency.

These are not yet frozen source/output packets suitable for independent judgment. Good/poor scenario summaries cannot establish that the agent itself produces better analysis or usable outputs. Acceptable interpretations are embedded beside inputs, so a future runner must keep reviewer guidance out of generation input.

`scripts/validate_analysis_eval.py` imports ratings, not paired outputs and their provenance. The score path bypasses manifest validation at lines 107-110. Readiness checks only test truthiness of purported hash fields at lines 81-86; there is no file/hash binding. `validate()` rejects every status except design-only, while `summarize()` permits comparison-ready, so there is no consistent validated transition. No comparison report, anchored per-dimension rubric, frozen adoption rule, or actual paired-output runner is present.

Required correction: build complete source/brief/rendered fixtures, separate reviewer keys, bind saved outputs/model settings/source hashes, validate scoring inputs, and run a prospective comparison. The absence of a saved historical baseline prevents a historical improvement claim; it does not prevent the plan's explicitly allowed new baseline or single-approach versus complementary-approach comparison.

### 5. Medium — latest evaluation test fails (P0/P7 acceptance and CI)

Reproduced with `python3 -m pytest -q tests/test_analysis_eval.py`: **1 failed, 4 passed**. `test_manifest_remains_explicitly_design_only` receives 12 packet-missing errors.

`scripts/validate_analysis_eval.py:24` requires the private `_manifest_dir` field that only the CLI injects. Existing callers using `validate(json.loads(MANIFEST.read_text()))` break after packet references are added. CLI validation succeeds, masking the broken API/test path. The earlier 856-test pass preceded this last edit.

Required correction: make the manifest base path an explicit consistent API input and rerun the affected checks after the final edit.

### 6. Medium — compaction restores the wrong case or no workspace in supported layouts (P6.9)

`.claude/hooks/compaction_state.py:55-57` returns no workspace for repo-root CWD, even if the session is working on a selected project. Its resolver reconstructs paths instead of using the existing workspace controllers. It recognizes case manifests only under `business-analysis/cases` (line 86), then falls back to shared research. Run-manifest lookup is hardcoded to the legacy root pain-points path (line 105). Branding/Marketing/Website can inherit Business research state because candidate selection is not module-specific.

Isolated reproduction: with CWD `projects/legacy/cases/chosen/market_research`, the snapshot retained `case_id=chosen` but bound `projects/legacy/market_research/manifest.json` and restored the shared, unrelated next action. Repo-root CWD produced `null` workspace. Two-session isolation passes its fixture but does not cover these cases. Accepted decisions and open questions are not persisted as the plan requires.

Required correction: persist explicit selected scope per session, resolve registered layouts/modules through existing controllers, and refuse to substitute shared state for a requested case. Cover root-launched sessions, legacy cases, custom paths, selected runs and independent modules.

### 7. Medium — monitored-change hypothesis work remains undelivered (SaaS batch 5)

The competitor-monitoring workflow still provides general snapshot/diff instructions. No implemented event contract/producer was found for comparable old/new facts, exposed customers, contrary/corroborating customer evidence and the next verification step. The current monitoring Python package contains AI-answer observations and owner-action support, which do not implement product/pricing/closure events.

Required correction: add the scoped event-to-hypothesis output and comparisons promised by batch 5, including monthly/annual normalization, baseline-only captures, cosmetic edits, closure uncertainty and modeled app revenue limits. No recurring scheduler or new paid adapter is needed to implement these local contracts.

## Other coverage limitations

- P2/P3/P5 have substantial schema/instruction support, but the claimed analytical gains remain unmeasured. The new source packets do not exercise the actual multilingual/contradictory interpretation requirements yet.
- Module and quality references appear as optional router metadata (`scripts/route_workflow.py:319-324`), rather than the `required_references` dispatch contract. The plan's substantive-module guidance loading is therefore not assured. Focused requests should keep their narrow loading rule.
- `AGENTS.md:50` and the archetype research workflow still encourage foreign examples as sources of venture ideas; the newer intent-preservation instruction constrains this, but specialist wording should be aligned so the user correction is applied consistently.
- Global curator removal and project ownership are visible, including ignore exceptions and scoped files. Live discovery in each harness remains unverified; this review found no reason to undo the relocation.
- P8 provider extraction was explicitly optional. Its deferral is justified and is not a completion defect.

## Verification performed

- Read both plans, the implementation record, relevant collector/gate/router/workstream/hook/evaluation code and fixture files.
- Ran the targeted existing evaluation tests: 1 failed, 4 passed.
- Reproduced registered-path mispublication and legacy-case misbinding in disposable temporary projects; repo-root checkpoint returned null.
- Did not rerun the full suite after finding a deterministic targeted failure, modify implementation, migrate project data, run live providers, or invoke models.

Recommended repair order: preserve partial captures; implement scoped downstream consumption and correct destination writes; fix the evaluation regression; construct executable evaluation fixtures/runner; repair compaction resolution; finish the change-hypothesis contract. Re-evaluate completion against producer/consumer behavior and the declared acceptance criteria.
