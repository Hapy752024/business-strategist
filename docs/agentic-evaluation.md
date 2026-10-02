# Agentic process evaluation

Use two separate gates:

1. `python3 scripts/run_behavioral_evals.py --repeat 3` checks deterministic routing contracts and variance. It does not invoke an LLM.
2. `python3 scripts/benchmark_agentic_process.py --static-review` compares auditable repository contracts with the pre-brand-integration Git baseline and creates a review workspace plus static HTML.

Outputs under `eval-workspaces/` are intentionally ignored. The committed configuration fixes the baseline, scope, contract definitions, and an audited structural snapshot so a run is reproducible even in a shallow CI checkout. Full clones recompute the baseline from the fixed Git ref.

Neither gate establishes subjective design quality, model judgment, token efficiency, or business outcomes. Claim those only after a separately authorized repeated LLM benchmark and human review. Record model/provider, prompt, skill version, tokens, wall time, tool calls, errors, and reviewer feedback for both baseline and current configurations.

For the frozen cross-workflow task set, validate `evals/workflow-quality/manifest.json` with `python3 scripts/run_analysis_evals.py --validate-only`. Run with `--arm baseline` or `current`, `--command-json '<JSON argv>'`, `--model-id <id>`, and a fresh `--out <directory>`; use two repetitions. The runner copies only task input to each fresh trial directory and never loads reference judgments. The configured command must enforce OS-level filesystem/network isolation, use the matching code/skill snapshot and record tool calls in stderr; the runner itself is not a sandbox. Keep held-out tasks out of development runs. Live comparison, human calibration, usage and billing remain unknown until measured; failed invocations stay in the denominator.

After paired runs, create a blinded packet with `python3 scripts/prepare_blinded_eval.py --baseline <baseline-dir> --current <current-dir> --split development --seed <integer> --out <new-dir>` for calibration, then a separate `--split held_out` packet. The human reviewer receives task inputs, outputs, rubric and an empty ratings template. The arm mapping is written only under `coordinator/`; do not share that directory with reviewers. Random labels can still be guessed from answer style, so record that limitation.
