# Local agent evaluation

Run from this repository. Domain cases, evidence and results stay local; no `~/agent-evals`, Langfuse, provider SDK or external evaluation service is required for offline operations.

```bash
python3 scripts/evaluate.py check
python3 scripts/evaluate.py check --full
python3 scripts/evaluate.py trial --case unsupported-demand --actor candidate-session
python3 scripts/evaluate.py report
```

`check` delegates to existing fixture/contract suites and the local result-contract regressions. `--full` retains the existing repository-wide checks, including known failures. `trial` without `--live` only prepares inputs; it does not invoke a model. Results are immutable `evals/local-runs/<run>/result.json`; logs, instruction snapshots, private rubric and a review template accompany each trial. Exit 1 means failed checks; exit 2 means infrastructure error or invalid operation. Prepared trials and completed ungraded native trials are UNVERIFIED and cannot establish quality.

## Native selected-skill trials

The first adapter is Claude Code in Bubblewrap. Linux, `bwrap` and a Node installation containing `bin/claude` are required. No unsandboxed fallback is permitted. Supply an explicitly authorized per-trial budget and the existing private OAuth file; credentials are never copied to results. The candidate sees only its writable trial workspace, read-only system/Node runtime and the selected OAuth file in an otherwise empty home. Source repositories, sibling runs and grading keys are absent. Native network access is shared for inference; external side effects and credential access by candidate tools are not isolated by this adapter. Do not use it for adversarial network/exfiltration cases. It clears inherited environment, disables host hook/MCP discovery, retains only Read/Bash, starts a fresh nonpersistent session and bounds time plus the CLI API budget. The CLI budget is not an authoritative billing receipt. Subscription usage is recorded only if emitted; missing cost/usage remain null.

```bash
python3 scripts/evaluate.py trial --case unsupported-demand --actor fresh-candidate-session --live \
  --model <authorized-model> --runtime-root <node-installation> \
  --auth-file <private-existing-claude-oauth-file> --budget-usd 1 --timeout 120
```

This evaluates selected instructions with fixed synthetic evidence, not the full production workflow, MCP stack, live research or rendered quality. Inspect runtime tool events to verify instructions were actually read. Supplied file hashes alone do not prove loaded context. An unavailable/expired runtime remains infrastructure failure, never quality PASS. `--fixture-command-json` is reserved for synthetic sandbox probes, network-disabled and permanently classified deterministic.

For baseline/current comparisons, use separate pinned checkouts via `--snapshot-root`, `--arm baseline|current`, fresh actors and two repetitions per case. Record configuration and runtime differences. Held-out cases require explicit `--split held_out`; do not tune skills on their judgments. This convention is not a secrecy boundary against a developer who can read the source repository.

## Independent review

```bash
python3 scripts/evaluate.py review-packet --baseline <baseline-run> --current <current-run> --out <new-packet-directory>
python3 scripts/evaluate.py review --run <trial-run> --ratings <completed-copy-of-review-template.json>
```

Give only the packet's `review/` directory to a fresh independent reviewer; retain `coordinator/` separately until ratings are locked. Random A/B labeling does not eliminate style clues. Keep failed attempts in comparison denominators. The reviewer fills every criterion with PASS/FAIL/UNVERIFIED, an exact output excerpt and rationale, records their identity/session, independence limits and human calibration evidence, and binds the answer SHA-256. Copy the template outside the sealed run before editing. Self-review and incomplete/changed evidence are rejected. Declared identity does not attest independent process execution. Reviews append separate immutable revisions; no command approves or overwrites a baseline. Quality grades apply only to that selected case; video visual claims additionally need actual frame/motion review in the existing production workflow.

## Optional reporting

```bash
python3 scripts/evaluate.py export --run <run-directory> --outbox <local-summary-directory>
```

Export writes an idempotent allowlisted JSON summary with result digest. It performs no network call and does not claim ingestion. A central collector may consume this outbox separately. Raw transcripts, tool output, rubric, credentials and instruction contents are excluded. Failed export leaves local evidence unchanged. Result digests detect accidental changes; they are not tamper-proof attestations against the same OS user.

## Workflow and promotion

After instruction/workflow changes, run affected checks and record a regression for a material failure in the existing improvement log. Before claiming improved model quality, run matched native trials and independent review; do not substitute structural passes or keyword matches. Keep the existing richer datasets and domain review protocols; the new three-case seed pack is a small diagnostic entrypoint. New hosts need their own isolated adapter and observed smoke before qualification. Review failed results, fix the cause and rerun the affected case without rewriting expectations to fit the answer.

## Runtime error corrections and file access

`reclassify --run <native-run>` appends a bound correction for runtime authentication/host errors; it preserves original records. Reports and exports retain historical verdicts alongside corrected infrastructure classification. Filesystem permissions 0700/0600 are requested; Windows mounts that ignore POSIX modes need appropriately restricted filesystem ACLs for sensitive runs. Raw logs remain local and gitignored, but that does not guarantee OS-user confidentiality.
