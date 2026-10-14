# Local evaluation implementation evidence

2026-10-13. The local entrypoint is `scripts/evaluate.py`; operations are documented in `LOCAL-EVALUATION.md`. All three repositories carry the same standard-library result contract and regression suite without a shared runtime/service dependency. Existing runners and historical central evidence remain in place.

Implemented: delegated offline/full checks, bounded fresh Claude/Bubblewrap selected-skill trials, preserved original input hashes, grading-key exclusion, matched blind packets, independently attributed append-only quality reviews, integrity checks, and idempotent allowlisted local summary export. A result schema lives at `local-result.schema.json`. The native adapter uses Read/Bash with host hook/MCP discovery disabled; this is a selected-skill synthetic micro-trial, not full production-agent acceptance. Native network access is shared and reviewer independence is declared rather than OS-attested.

Verification: 33 regression tests pass in the staged identical module; the final installed suite is invoked by the repository validator. Local check and network-disabled Bubblewrap probe both passed. The isolation probe found no host home, grading key or review template and could not connect outbound. Offline result records:

- `evals/local-runs/20261014T081321Z-2bb1ae3a3564/result.json`: PASS, deterministic evidence only.

- `evals/local-runs/20261014T081343Z-8f44c95d57da/result.json`: PASS, deterministic evidence only.

Live pilot: `evals/local-runs/20261013T175516Z-8081cd7cbe45`. The existing OAuth session failed authentication before a model response. `classification-v1.json` corrects the initial execution-failure classification to INFRASTRUCTURE_ERROR without editing `result.json`. CLI-reported cost was USD 0 with no model usage; this is not a billing receipt. Three pilots were authorized at USD 1 each, total cap USD 3; no automatic retries occurred. Native tool-path qualification, independent quality grading, human calibration and baseline promotion remain pending authentication and observed execution. Rerun the documented explicit live command only under remaining/current authorization; do not generate credentials or silently use a paid fallback.

Full validation: `evals/local-runs/20261013T175613Z-1c6462544bc3/result.json`: FAIL. See bound check logs for individual failures.

Existing full-check failures: three skill entry line budgets and `test_competitor_plan_preserves_input_and_does_not_inject_english`; 1178 pytest tests passed and one failed. Existing WF-007/WF-008 track these failures.
