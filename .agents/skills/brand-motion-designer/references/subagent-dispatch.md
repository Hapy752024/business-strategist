# Subagent Dispatch

Dispatch a fresh subagent (Agent tool) for any of these:

- **Three demo variants per pillar or element.** One subagent per variant (Snappy / Smooth / Bouncy), each producing one `option-N.html`. Run the three in parallel — they write to disjoint files. The controller collects the three HTML paths and presents them to the user.
- **Per-pillar token tuning.** When two pillars are being tuned in the same iteration round, dispatch one subagent per pillar. Each writes to `stages/motion/pillars/<pillar-name>/tokens.{css,ts}` — disjoint paths, safe to parallelize.
- **Per-element spec drafting.** When the user has approved 4+ element categories, dispatch one subagent per category to draft specs into `stages/motion/elements/<category>.md`. Disjoint files; parallelize.
- **Coherence review.** After element specs are drafted, dispatch one critic subagent (Explore or general-purpose) to read all `stages/motion/elements/*.md` and report any pillar reference that does not exist in `motion/motion-tokens.ts`. The subagent does not see this skill's reasoning — it reviews cold.
- **Benchmark lookup.** When the user names a new reference product mid-loop, dispatch a research subagent (WebFetch / Brave search) to extract 2-3 named motion patterns from that product and append them to `references/benchmarks.md`.

Never parallelize subagents that touch the same file. Never dispatch a subagent for a single-variant task — do that inline. Always pass the subagent the exact paths, the pillar names, and the token filenames it should use; do not paste this skill's conversation history.
