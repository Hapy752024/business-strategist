# Plan: close the 24 September implementation review gaps

Status: implemented and locally verified, with live-quality and host/runtime evidence still open. Scope is the findings in `../audits/2026-09-24-implementation-vs-plan-review.md` and remaining acceptance criteria they identify. Existing project research and unrelated working-tree changes were preserved.

## Order and acceptance

1. **Collection recovery (P1):** completed provider-batch recovery, merging accepted records and membership lineage by stable identity; attempt-in-progress markers expose interrupted operations. Tests pass. Per-query/raw-capture fault injection and exact reconciliation of remote provider billing remain open.
2. **Marketing destination and handoff lifecycle (P4/P6):** completed registered-path writes, hash-bound brief/import/output refs, path containment, explicit reviewed refresh/publication, and routing blocks for stale bindings. Scope/applicability is surfaced to the specialist for human review; no semantic auto-matcher exists.
3. **Evaluation scaffold (P0/P7):** validators now bind packet assets, outputs, traces, reviewer records and criteria; synthetic generation inputs and illustrative paired outputs are present. All manifests remain design-only until actual agent outputs receive independent blind review. No historic baseline is fabricated; comparison can be prospective.
4. **Compaction (P6):** completed explicit session selection persistence, case/module-aware resolution, and carry-forward of open questions and accepted decisions, with per-session isolation. Unit/regression coverage passes; live Claude host behavior is unverified.
5. **Change hypotheses (SaaS batch 5):** completed offline dated before/after contract with snapshot hashes, comparability checks, customer impact hypothesis, evidence roles, next verification, and limits. No schedule/provider integration.
6. **Intent consistency and routing (P6/SaaS batch 4):** foreign companies are optional comparables in founder-playbook research; user idea/problem validation remains the objective. Strategic module guidance is loaded for strategic tasks while focused/execution scope remains narrow.

Validation: **866 Python tests passed**; routing validation, eval structure, all four analysis-eval manifests, skill-authoring quick validation, and `git diff --check` passed. Structural checks do not prove improved customer-problem analysis. Actual paired outputs, independent blind ratings, human semantic review of Marketing applicability, provider-boundary fault injection, and live Claude compaction remain open.
