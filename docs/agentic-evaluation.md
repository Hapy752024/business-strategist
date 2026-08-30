# Agentic process evaluation

Use two separate gates:

1. `python3 scripts/run_behavioral_evals.py --repeat 3` checks deterministic routing contracts and variance. It does not invoke an LLM.
2. `python3 scripts/benchmark_agentic_process.py --static-review` compares auditable repository contracts with the pre-brand-integration Git baseline and creates a review workspace plus static HTML.

Outputs under `eval-workspaces/` are intentionally ignored. The committed configuration fixes the baseline, scope, contract definitions, and an audited structural snapshot so a run is reproducible even in a shallow CI checkout. Full clones recompute the baseline from the fixed Git ref.

Neither gate establishes subjective design quality, model judgment, token efficiency, or business outcomes. Claim those only after a separately authorized repeated LLM benchmark and human review. Record model/provider, prompt, skill version, tokens, wall time, tool calls, errors, and reviewer feedback for both baseline and current configurations.
