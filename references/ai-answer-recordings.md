# Recorded AI-answer observations (format 2)

The comparison below is offline: no credentials or network are needed. Recordings come either from manual capture or from the live collector (next section). Mention listening is a separate pending capability. Never synthesize model answers and label them collected observations.

1. Select the business question and subject name/domains. Prefer available authorized first-party measurements for the real search surface. Use recorded API/consumer answers only for questions those measurements cannot answer.
2. Copy the format example in `fixtures/monitoring/recorded-example/`; replace every synthetic field with actual provenance. A panel declares `schema_version: 2`, `panel_version`, `subject`, and `prompts` (id/version/type/text/source), plus explicit `targets` (engine/model/search_config/surface/locale/repetitions). Use precise model versions and effective tool settings. The prompt source explains the audience/search evidence used to select the question; model memory is not question demand.
3. Each recording retains the actual `prompt_text`, collection `timestamp` with timezone, target brand/URL, full answer, source locator/request ID and annotation method/reviewer. `citation_urls` and supplied citation annotations are preserved; confirm the correct entity and supporting citation rather than just matching a word. Failed rows have null mention/recommendation/citation flags and an explicit error reason. Record credit failures and top-up route, then rerun after a reported top-up. Retain retries in raw provider material; import one final outcome per target/prompt/repetition. Raw input is retained, so redact credentials and unnecessary personal information before import.
4. Use a **new** run directory. Existing destinations, including `.` and `..`, fail unchanged. A run contains panel, raw input, normalized rows, summary/report and a digest-bound `run.json` completion manifest. Interrupted output is incomplete diagnostic evidence; do not delete or replace older runs. Use `load_run` to verify completion and hashes before consuming a run. Process exit 0 means completed baseline/eligible descriptive comparison; exit 2 means completed partial/unmeasured/incomparable evidence; exit 1 means input/I/O failure. Always read the measurement status.

```bash
python3 scripts/monitoring/ai_answer_probe.py --panel fixtures/monitoring/recorded-example/panel.json --recorded fixtures/monitoring/recorded-example/prior.jsonl --out /tmp/unique-baseline-run
python3 scripts/monitoring/ai_answer_probe.py --panel fixtures/monitoring/recorded-example/panel.json --recorded fixtures/monitoring/recorded-example/current.jsonl --prior-run /tmp/unique-baseline-run --out /tmp/unique-followup-run
```

## Live collection (optional, spends provider credits)

`scripts/monitoring/ai_answer_collect.py` asks the declared targets live and writes format-2 rows that differ from manual ones only by `collection_method: api`, provider request ids, usage/cost and citation details. Engines: `openai` (Responses API, `web_search` tool), `gemini` (`generateContent` with `google_search` grounding), `xai` (Responses API, `web_search`), `anthropic` (Messages API, `web_search_20250305`), `perplexity` (Sonar), and Google surfaces via DataForSEO: `google-ai-mode` (surface `consumer`) and `google-ai-overview` (organic SERP with `load_async_ai_overview`, surface `ai_overview`). Use exact dated model ids. `search_config` must equal the effective settings; print them with `configs --locale de-DE`.

```bash
python3 scripts/monitoring/ai_answer_collect.py collect --panel <panel.json> --out <new-dir> --dry-run
python3 scripts/monitoring/ai_answer_collect.py collect --panel <panel.json> --out <new-dir> --max-calls 20
python3 scripts/monitoring/ai_answer_collect.py review --recorded <new-dir>/recorded.jsonl --decisions <decisions.json> --out <new-file>
```

- The planned call count and an assumed-price estimate print first; a plan above `--max-calls` (default 20) sends nothing. Repetitions are separate calls.
- Every target/prompt/repetition yields one row. Missing keys, quota/credit, HTTP and parse failures are failed rows with null flags and a reason, never dropped. An absent Google AI answer is `unsupported`, not a success.
- Rules annotate `brand_mentioned` (subject name or declared domain as a whole word in the answer, with evidence snippets) and `url_cited` (citation hostname exactly in `subject.domains`; declare `www.` and other hosts you want counted — subdomains are listed separately, not counted). Consulted search sources are kept apart from citations. When the subject is named, `recommended` stays null until a reviewer decides it with `review` (`{row_id: {recommended, reviewer, note}}`); only then can the file be imported.
- Raw provider responses are kept in `raw.jsonl`; keys travel only in headers and are redacted from every written file.

The example is synthetic and cannot establish real visibility. Replace the output paths with unused paths on every run. Format-1 recordings require explicit migration to declared subjects/targets/provenance; do not invent missing historical context. `--prior` plus `--prior-panel` supports separately supplied recordings; without the prior panel, observations remain incomparable. `--prior-run` is preferred because it verifies the saved artifacts.

Coverage is per declared prompt/target/repetition. Off-panel rows are diagnostics only. Trends require complete successful coverage, identical semantic panel content/context and strictly later nonoverlapping windows. Changed question text under reused version labels is incompatible. Rates are descriptive; repetition indices do not create paired subjects or prove causal/significant improvement.

Read the source answers, then consume the report through `references/search-visibility-decisions.md`. Missing collection, identity or account evidence is unknown, never absence. No scheduler, publication or outreach is started by this procedure.
