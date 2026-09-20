# Search-Visibility Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the revised digital-marketing optimization plan: wire AEO/GEO/DEO procedures into the real agent entry points, add an owner-action contract persisted in existing manifest fields, register new observation providers, extend routing/evals, and ship a read-only AI-answer observation pilot script.

**Architecture:** Documentation/instruction changes to existing skills (no new skills, no orchestration layer), config parity updates (routes + catalog + evals), and one new offline-testable Python script (`scripts/monitoring/ai_answer_probe.py`) following the `scripts/brand/check_lighthouse.py` CLI pattern. All observation providers are dry-run/recorded mode by default; live API calls are out of scope for this plan.

**Tech Stack:** Python 3 (stdlib only), JSON config, Markdown skill references, pytest.

**Spec:** `docs/digital-marketing-optimization-plan.md` (revised 2026-09-20) — the plan argues from this spec; read it first. Review record: `docs/digital-marketing-optimization-plan-adversarial-review.md`. This plan was itself gap-reviewed by a fresh subagent on 2026-09-20 (verdict NEEDS-FIXES); all 6 must-fix and 7 should-fix findings are incorporated below.

## Global Constraints

- The working tree contains ~360 pre-existing modified files unrelated to this work. **Never `git add -A` or `git commit -a`. Stage only the exact files listed in each task.**
- Skills live at `.agents/skills/<name>/` (symlinked to `.claude/skills/`); edit the `.agents` path.
- Primary shell is bash; scripts run with `python3` from repo root.
- CI gates that must stay green after every task: `bash scripts/validate_setup.sh`, `python3 scripts/run_evals.py`, `python3 scripts/validate_skill_routes.py` (config tasks), `python3 -m pytest tests/ -q`.
- Every `evals.json` in this repo is an object `{"skill_name": ..., "evals": [...]}` — new entries go into the `"evals"` array, never at file root.
- Evidence discipline: agent-facing text must not promise AI citations, must not quote "4–9x AI conversion", must not attribute a "90/10 rule" to Reddit policy, and must describe `Google-Extended` as a product token (training + Gemini/Vertex grounding), not an HTTP user agent. Binding claims live in spec §1.
- DEO content is conditional: commerce/comparable-offer businesses only; no MCP scaffolding, discovery files (`llms.txt`, `/.well-known`), or schema launch-contract migration in this plan.
- Model responses are observation data, never customer-demand evidence. Failed/credit-blocked probes are coverage gaps (`unknown`), never absence of mention.
- Tasks 1 and 3 forward-reference `scripts/monitoring/ai_answer_probe.py`, which Task 5 creates. Land tasks in order, or accept a dangling path until Task 5.

---

### Task 1: Website-skill visibility references and entry-point wiring

**Files:**
- Create: `.agents/skills/brand-website-designer-builder/references/aeo-geo-visibility.md`
- Create: `.agents/skills/brand-website-designer-builder/references/deo-agent-readiness.md`
- Modify: `.agents/skills/brand-website-designer-builder/references/maintenance.md` (add one paragraph after line 3)
- Modify: `.agents/skills/brand-website-designer-builder/references/seo-performance.md` (replace the LLM-EO paragraph, line 9)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: reference filenames `aeo-geo-visibility.md` and `deo-agent-readiness.md` that Task 2's workflow edits and Task 5's script output report will point to. Both files forward-reference `scripts/monitoring/ai_answer_probe.py` (created in Task 5) and `references/owner-actions.md` (created in Task 2); land tasks in order.

- [x] **Step 1: Create `references/aeo-geo-visibility.md`**

```markdown
# AEO/GEO visibility procedure

Apply for answer/generative-engine visibility audits and content work on existing or new sites. Load from maintenance.md for existing-site audits. Eligibility work never guarantees citations; quote only the binding evidence table in docs/digital-marketing-optimization-plan.md §1.

Question mining: derive questions from actual audience evidence — People Also Ask APIs, Search Console question-regex pulls (`^(who|what|when|where|why|how|is|are|can|do|does|should)\b`), reviewed community sources — and produce a clustered question→URL map. Never invent question demand from model memory.

Answer structure: draft answer-first capsules (≈40–60 words after a question-shaped heading), comparison tables and self-contained passages as testable hypotheses, not universal rules. Inject named-source citations, verifiable statistics and real expert quotations where the owner can supply them. The owner verifies owner-only facts (prices, guarantees, firsthand claims) before publication; agent-recheckable facts are verified against current authoritative sources or an approved source record.

Schema: generate and validate markup for currently supported features only; markup must match visible facts. Google deprecated HowTo rich results (2023) and FAQ rich results (May 2026); do not present FAQ/HowTo markup as a rich-result or citation lever. JSON-LD showed no measurable citation improvement in Ahrefs' matched sample (May 2026); keep it for entity clarity and rich results.

Freshness: flag comparison/pricing pages past 60–90 days and evergreen pages past ~6 months; propose substantive updates (stats, dates, prices), never date-bumping without real revision.

Entity consistency: audit Organization/Person `sameAs`, profiles and directories; maintain Wikidata where eligible. Wikipedia requires earned notability — never force an article. Map which sources AI answers actually cite for the category's competitive prompts, so missed earned-media targets are visible rather than guessed.

First-party observation: where the site is verified, pull Bing Webmaster Tools AI Performance data — it is the only first-party AI citation feed available.

AI-answer observation: use `scripts/monitoring/ai_answer_probe.py` under its measurement contract (surface labels, prompt-type labels, model/config recording, success/error/unsupported states, compatible-window comparison, coverage reporting). Start with a narrow panel of 15–30 prompts drawn from customer questions and search evidence; expand only when findings change a decision, and never present this as a replacement for commercial visibility tools. Model responses are observations, not customer-demand evidence. A failed or credit-blocked engine is a recorded coverage gap, never absence of mention.

Message match: the AI-referrer analytics channel does not reveal the conversation or recommendation that sent a visit. Compare observed probe contexts or legitimately supplied conversations against landing pages as a diagnostic only — never as the actual context of individual AI-referred visits. Observable conversions and attribution limits follow the campaign measurement contract in `references/campaign-tracking.md`.

Crawler/access policy: describe each vendor control's real effect before implementing. `Google-Extended` is a product token (no HTTP user agent) covering training plus Gemini Apps grounding and Grounding with Google Search on Vertex AI; it cannot be observed in user-agent logs. OpenAI/Anthropic training and search/retrieval bots are independent. The owner selects per-vendor policy; also check CDN defaults (Cloudflare has blocked AI crawlers by default for new domains since Jul 2025). Never allow every AI bot by default. llms.txt is deprioritized: no measured impact in available studies, and Google states it is unused.

Sources checked 2026-09-20: [Google AI features](https://developers.google.com/search/docs/appearance/ai-features), [Google-Extended](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers#google-extended), [HowTo/FAQ changes](https://developers.google.com/search/blog/2023/08/howto-faq-changes), [Search updates](https://developers.google.com/search/updates), [Ahrefs schema study](https://ahrefs.com/blog/schema-ai-citations/), [Ahrefs brand correlations](https://ahrefs.com/blog/ai-brand-visibility-correlations/). Refresh before consequential claims.
```

- [x] **Step 2: Create `references/deo-agent-readiness.md`**

```markdown
# Decision-engine (agent) readiness — conditional

Apply only for businesses with commerce or comparable offers, after the marketing bottleneck diagnosis justifies it. DEO is an emergent label (coined 2026-09); the mechanics (product feeds, agentic commerce protocols) are real but recommendation→transaction conversion has almost no public data. Present as conditional infrastructure, never a promised channel.

Machine-comparable attributes: pricing in crawlable plain HTML (never JS-only or "contact sales" for eligible tiers), Product/Offer markup with identifiers (GTIN/MPN/SKU/brand), price, availability and aggregateRating encoded only from owner-confirmed facts, Organization-level MerchantReturnPolicy and OfferShippingDetails matching the visible policy text exactly. Inaccurate markup is penalized harder than absent markup; the agent encodes, the owner supplies truth.

Owner-gated approvals (identity-bound, cannot be delegated): OpenAI merchant application, Google Merchant Center/UCP onboarding, Google Business Profile verification, review-platform profiles. Record these as owner actions (references/owner-actions.md at repo root).

Feed publication requires the feed contract before any scheduled push: named authoritative inventory/price source with a freshness limit (stale input fails closed); replacement/deletion semantics so removed products are withdrawn, not merely not-updated; delivery reconciliation (acknowledgements, rejections, retries) with operator alerts; acceptance tests covering stale input, removed products, rejected updates and delayed retries.

Reputation: reviews come from real customers on independent platforms (G2, Capterra, Trustpilot, Google). The agent audits presence and drafts owner-approved review requests; fake reviews are fraud and never an option.

Measurement: track decision-stage prompts ("which X with A and B under price P") separately from educational prompts using the `prompt_type` label under the ai_answer_probe measurement contract.

Deferred until a selected integration needs them: MCP commerce servers, `/.well-known` discovery files, llms.txt.

Sources: living documents checked in-session 2026-09-19 — the OpenAI product-feed specification, Google Merchant Center/UCP onboarding guides and OpenAI shopping help. Re-fetch them before implementation; do not quote their details from memory, and add them to the spec §7 register when they inform a binding claim.
```

- [x] **Step 3: Add the conditional load instruction to `maintenance.md`**

Insert after the first paragraph (after line 3):

```markdown
For AEO/GEO/AI-visibility audits of existing sites, also load `references/aeo-geo-visibility.md`; for businesses with commerce or comparable offers add `references/deo-agent-readiness.md`. Observation and measurement follow their contracts; visibility findings are intermediate measures, not business outcomes.
```

- [x] **Step 4: Replace the LLM-EO paragraph in `seo-performance.md` (line 9)**

Old (exact current text):
```markdown
LLM-EO/GEO/AEO means discoverable, understandable, source-supported content: clear entities, useful sections, self-contained answers, visible authorship/sources and honest update dates. Keep human/crawler content consistent. Eligibility cannot guarantee citations. llms.txt is optional experimental documentation requiring an owner/update process, not a launch prerequisite or substitute for SEO. Decide search versus training bot access explicitly using current vendor docs; never allow every AI bot by default.
```

New:
```markdown
LLM-EO/GEO/AEO means discoverable, understandable, source-supported content: clear entities, useful sections, self-contained answers, visible authorship/sources and honest update dates. Keep human/crawler content consistent. Eligibility cannot guarantee citations. For audits and content procedure load `references/aeo-geo-visibility.md`; for commerce/agent readiness `references/deo-agent-readiness.md`. llms.txt is deprioritized (no measured impact in available studies; Google states it is unused); if used it requires an owner/update process and is never a launch prerequisite or substitute for SEO. Decide search versus training versus grounding access per vendor using current docs — `Google-Extended` is a product token that also controls Gemini/Vertex grounding, not a separate crawler — and never allow every AI bot by default.
```

- [x] **Step 5: Verify**

Run: `bash scripts/validate_setup.sh`
Expected: `0 errors` (skill structure and symlinks still valid).
Run: `test -f .agents/skills/brand-website-designer-builder/references/aeo-geo-visibility.md && test -f .agents/skills/brand-website-designer-builder/references/deo-agent-readiness.md && grep -q 'aeo-geo-visibility' .agents/skills/brand-website-designer-builder/references/maintenance.md && grep -q 'Google-Extended.*product token' .agents/skills/brand-website-designer-builder/references/seo-performance.md && echo OK`
Expected: `OK`

- [x] **Step 6: Commit**

```bash
git add .agents/skills/brand-website-designer-builder/references/aeo-geo-visibility.md .agents/skills/brand-website-designer-builder/references/deo-agent-readiness.md .agents/skills/brand-website-designer-builder/references/maintenance.md .agents/skills/brand-website-designer-builder/references/seo-performance.md
git commit -m "Add AEO/GEO and agent-readiness procedures to website skill entry points"
```

---

### Task 2: Owner-action contract and marketing/social selection rules

**Files:**
- Create: `references/owner-actions.md`
- Modify: `.agents/skills/marketing-strategy-builder/references/workflow.md` (append one subsection after the channel-selection paragraph ending "...name the evidence that unlocks more.", line 143)
- Modify: `.agents/skills/social-digital-marketing-planner/references/workflow.md` (append one paragraph after the paragraph ending "...explicitly defer the rest.", line 111)

**Interfaces:**
- Consumes: Task 1 reference filenames (`aeo-geo-visibility.md`, `deo-agent-readiness.md`).
- Produces: shared contract `references/owner-actions.md` (repo root) that `deo-agent-readiness.md` already points to and Task 5's report template cites.

- [x] **Step 1: Create `references/owner-actions.md`**

```markdown
# Owner-action contract

Use when a deliverable surfaces work only the owner can do or decide. Apply with references/task-scope.md: include only decisions and actions relevant to the requested deliverable; never append recurring programs to narrow copy or execution work.

States: `proposed` (agent suggestion, not adopted), `accepted` (owner agreed), `deferred` (explicitly postponed), `completed`. Only `accepted` actions and genuine blockers persist; a `proposed` action never recurs on resume as if adopted.

Persistence: write accepted actions and blockers into the project manifest's existing `next_action` and `open_blockers` fields — these are what the workspace-lifecycle resume flow reads, and they are the source of truth. A human-readable `owner-actions.md` inside the project may render the same rows but never replaces manifest updates.

Each row: action, layer or area it feeds, cadence (one-off/weekly/monthly/quarterly), rough effort, expected evidence payoff, state. Cadence is a proposal until `accepted`.

Owner-only vs agent-verifiable: ask the owner only for unavailable firsthand facts, changed commercial commitments (prices, policies, guarantees) and actual decisions (publishes, sends, platform applications, spend). Facts verifiable against current authoritative sources or an approved source record are rechecked by the agent without asking.

Preserve publication/send authorization already granted in the session; do not re-ask. Identity-gated approvals (merchant programs, business-profile verification) are always owner actions.

Example rows (illustrative, not defaults):
- Publish one founder post per week from the listening-driven topic queue | SMO→GEO corroboration | weekly | 1h | earned-mention growth | proposed
- Provide real return-window terms for policy markup | DEO trust inputs | one-off | 15min | accurate Offer/Policy encoding | accepted
- Fact-check 12 drafted answer capsules on /pricing and /compare | AEO accuracy | one-off | 45min | safe publication | proposed
```

- [x] **Step 2: Add the visibility selection rule to the marketing workflow**

Append after the channel-selection paragraph (the line ending "...name the evidence that unlocks more.", line 143) in `.agents/skills/marketing-strategy-builder/references/workflow.md`:

```markdown
AI answer engines and agent/comparison surfaces are channel jobs (discovery, demand capture), not a default work program. Before prescribing AEO/GEO/DEO work or visibility monitoring, state the observed bottleneck, relevant buyer behavior, available assets and owner capacity, and select the smallest intervention with a named business outcome and stop rule; visibility metrics are intermediate measures. Run the selected work as a feedback loop — observation → proposed change → expected business effect → result → next decision — reusing `references/experimentation.md` and the campaign measurement contract. Hand off on-site answer/agent-readiness work to the website skill (`aeo-geo-visibility.md`, `deo-agent-readiness.md`, via its maintenance path) and recurring observation to a monitoring run that applies competitor-monitoring's watchlist/snapshot/diff conventions to the user's own brand. Surface owner-only work through `references/owner-actions.md`.
```

- [x] **Step 3: Add the same rule to the social planner workflow**

Append after the paragraph ending "...explicitly defer the rest." (line 111) in `.agents/skills/social-digital-marketing-planner/references/workflow.md`:

```markdown
Treat AI-answer visibility and brand-mention observation as inputs that require the same bottleneck justification as any channel; do not append monitoring or recurring posting programs to focused requests. Own-brand mention watch hands off to a monitoring run that applies competitor-monitoring's watchlist/snapshot conventions to the user's own brand; on-site answer-structure work hands off to the website skill. Surface owner-only work (authentic posting, community participation, creator outreach) through `references/owner-actions.md`. Ownership of an authentic viewpoint is non-delegable, while the mechanics of publishing an owner-approved post may be delegated where the platform permits. Human posting is the repository's selected operating policy; compliant disclosed automation is a per-platform, per-use-case check — never claim a blanket external prohibition.
```

- [x] **Step 4: Verify**

Run: `bash scripts/validate_setup.sh`
Expected: `0 errors`.
Run: `grep -q 'owner-actions.md' .agents/skills/marketing-strategy-builder/references/workflow.md && grep -q 'owner-actions.md' .agents/skills/social-digital-marketing-planner/references/workflow.md && grep -q 'proposed' references/owner-actions.md && echo OK`
Expected: `OK`

- [x] **Step 5: Commit**

```bash
git add references/owner-actions.md .agents/skills/marketing-strategy-builder/references/workflow.md .agents/skills/social-digital-marketing-planner/references/workflow.md
git commit -m "Add owner-action contract and bottleneck-gated visibility handoffs"
```

---

### Task 3: Register observation providers

**Files:**
- Modify: `config/source-capabilities.json` (append two entries to `capabilities`)
- Modify: `.agents/skills/evidence-scout/references/provider-policy.md` (append one section)

**Interfaces:**
- Consumes: nothing.
- Produces: capability IDs `ai_answer_engines` and `brand_mention_listening`; env var names `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `PERPLEXITY_API_KEY` that Task 5's script reads. The `ai_answer_engines` entry forward-references `scripts/monitoring/ai_answer_probe.py` (Task 5).

- [x] **Step 1: Add capability entries to `config/source-capabilities.json`**

Append to the `capabilities` array (mirror the existing entry shape exactly):

```json
{
  "id": "ai_answer_engines",
  "family": "visibility_observation",
  "label": "AI answer-engine observation panels",
  "description": "Fixed prompt panels against LLM APIs producing normalized mention/recommendation/citation observations under a strict measurement contract; read-only pilot via scripts/monitoring/ai_answer_probe.py.",
  "use_when": [
    "AI citation tracking",
    "AI visibility monitoring",
    "answer engine visibility",
    "share of model"
  ],
  "avoid_when": [
    "customer demand evidence",
    "market-wide visibility share claims",
    "representative prevalence estimate"
  ],
  "evidence_strength": "observation_only_not_demand_evidence",
  "collector_provider": "ai_answer_probe.py",
  "provider_aliases": [],
  "validation_providers": [],
  "requires_env": [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "PERPLEXITY_API_KEY"
  ],
  "approval_required": false,
  "authorization_policy": "standing_authorized_no_cap_with_cadence_note",
  "status_check": "python3 scripts/evidence_scout/provider_doctor.py --json",
  "example": "python3 scripts/monitoring/ai_answer_probe.py --panel panel.json --recorded observations.jsonl --out runs/<run>/",
  "caveat": "Measures the configured API experience, not consumer products. Failed or credit-blocked engines are coverage gaps (unknown), never absence of mention. Recurring panels x engines x repetitions need a recorded cadence/cost note."
}
```

```json
{
  "id": "brand_mention_listening",
  "family": "visibility_observation",
  "label": "Own-brand mention watch",
  "description": "Licensed-API mention monitoring for the user's own brand with sentiment and earned/owned/paid source classification; applies competitor-monitoring watchlist/snapshot conventions to the user's own brand.",
  "use_when": [
    "brand mentions",
    "social listening",
    "own-brand monitoring"
  ],
  "avoid_when": [
    "competitor teardown",
    "ToS-violating scraping"
  ],
  "evidence_strength": "observation_only_sampled",
  "collector_provider": "pending_pilot",
  "provider_aliases": [],
  "validation_providers": [
    "serper_search",
    "brave_search"
  ],
  "requires_env": [],
  "approval_required": false,
  "authorization_policy": "licensed_apis_only",
  "status_check": "python3 scripts/evidence_scout/provider_doctor.py --json",
  "example": "pending pilot; apply competitor-monitoring watchlist/snapshot conventions to own-brand rows",
  "caveat": "Listening coverage is API-gated (Meta/LinkedIn/TikTok limited). Samples are not market-wide share."
}
```

- [x] **Step 2: Verify JSON and lookup still work**

Run: `python3 -c "import json; json.load(open('config/source-capabilities.json')); print('valid')"`
Expected: `valid`
Run: `python3 scripts/capability_lookup.py --question "AI citation tracking" --compact`
Expected: output includes `ai_answer_engines` (the lookup indexes `use_when`); at minimum exits 0.

- [x] **Step 3: Append the provider-policy section**

Append to `.agents/skills/evidence-scout/references/provider-policy.md` (complements the existing Insufficient Credits Protocol section):

```markdown
## AI answer-engine probing and brand-mention listening

Observation providers (OpenAI, Anthropic, Gemini, Perplexity APIs for answer panels; licensed listening APIs for own-brand mentions) produce visibility observations, never customer-demand evidence. Saved model answers retain their surface label, prompt-type label, model/version, search/tool configuration, locale, timestamp, prompt version and collection status (success/error/unsupported).

If a provider reports `insufficient_credits`/`billing_required`, record a coverage gap for that engine, notify the user with the lost coverage and top-up route, and continue with remaining engines. A credit-blocked or failed engine is never evidence of absence of mentions; after a reported top-up, re-validate and re-run that engine's panel.

Recurring panels multiply cost (prompts x engines x repetitions x cadence): record the cadence and a cost note in the run's `summary.json` before scheduling, even under the standing pre-authorized spend policy. Publishing, posting and outreach remain separately authorized; observation providers are read-only.
```

- [x] **Step 4: Verify**

Run: `bash scripts/validate_setup.sh`
Expected: `0 errors` (schema/config validity).

- [x] **Step 5: Commit**

```bash
git add config/source-capabilities.json .agents/skills/evidence-scout/references/provider-policy.md
git commit -m "Register AI answer-engine and mention-listening observation providers"
```

---

### Task 4: Routing, catalog and eval parity (TDD)

**Files:**
- Test: `tests/test_website_launch.py` (extend routing tests after line 106; the file already imports `route_request` at line 12)
- Modify: `config/workflow-routes.json` (`website-build` and `competitor-monitoring` match lists)
- Modify: `config/skill-catalog.json` (`competitor-monitoring` and `brand-website-designer-builder` entries)
- Modify: `.agents/skills/brand-website-designer-builder/evals/evals.json`
- Modify: `.agents/skills/competitor-monitoring/evals/evals.json`
- Modify: `.agents/skills/marketing-strategy-builder/evals/evals.json`
- Modify: `.agents/skills/social-digital-marketing-planner/evals/evals.json`
- Modify: `.agents/skills/evidence-scout/evals/evals.json`

**Interfaces:**
- Consumes: capability IDs from Task 3 (eval text references them); Task 2 workflow changes (their evals assert the new behavior).
- Produces: route match terms `"AEO audit"`, `"AEO/GEO"`, `"answer engine optimization"`, `"structured data audit"`, `"agent readiness"` → `brand-website-designer-builder`; `"brand mentions"`, `"social listening"`, `"AI citation tracking"`, `"AI visibility monitoring"` → `competitor-monitoring`.

- [x] **Step 1: Write the failing routing tests**

Append to `tests/test_website_launch.py`:

```python
@pytest.mark.parametrize('prompt,expected', [
    ('Run an AEO audit', 'brand-website-designer-builder'),
    ('Structured data audit', 'brand-website-designer-builder'),
    ('Track brand mentions', 'competitor-monitoring'),
    ('Set up AI citation tracking', 'competitor-monitoring'),
])
def test_visibility_routes(prompt, expected):
    assert route_request(prompt)['skill'] == expected
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_website_launch.py::test_visibility_routes -q`
Expected: FAIL — all four prompts currently fall through to `clarify`/business-strategist (none of the new terms appear anywhere in `config/workflow-routes.json`).

- [x] **Step 3: Update `config/workflow-routes.json`**

In the `website-build` route, append to `match` (after `"GEO audit"`):
```json
"AEO audit",
"AEO/GEO",
"answer engine optimization",
"structured data audit",
"agent readiness"
```
In the `competitor-monitoring` route, append to `match`:
```json
"brand mentions",
"social listening",
"AI citation tracking",
"AI visibility monitoring"
```

- [x] **Step 4: Update `config/skill-catalog.json`**

In the `competitor-monitoring` entry, replace the `intent` array with:
```json
"intent": [
  "monitor competitor pricing, messaging, and product changes",
  "monitor own-brand mentions and AI-answer visibility observations"
]
```
and the `artifacts` array with:
```json
"artifacts": [
  "monitoring baseline",
  "change report",
  "visibility observation report"
]
```
In the `brand-website-designer-builder` entry, append to its existing `intent` array (keep current entries unchanged):
```json
"audit and improve AEO/GEO answer-engine visibility and agent readiness of websites"
```

- [x] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_website_launch.py -q`
Expected: all PASS (existing routing assertions unchanged — the matcher is casefolded substring, longest-phrase-wins; none of the new terms collide with existing test prompts).

- [x] **Step 6: Add eval entries**

Each `evals.json` is an object with an `"evals"` array — append each entry **into that array**. Before each append, pick the next free integer id:
`python3 -c "import json; print(sorted(e['id'] for e in json.load(open('<file>'))['evals']))"`

Append to `.agents/skills/brand-website-designer-builder/evals/evals.json` → `"evals"` (existing ids 1–7; use 8):
```json
{
  "id": 8,
  "prompt": "Run an AEO/GEO visibility audit of our existing marketing site and tell me what to fix first.",
  "expected_output": "Existing-site audit loads maintenance path plus aeo-geo-visibility procedure; bottleneck and measurement limits stated; no citation guarantees; owner actions surfaced via contract.",
  "files": [],
  "must_mention": [
    "aeo-geo-visibility",
    "maintenance",
    "owner",
    "evidence"
  ]
}
```

Append to `.agents/skills/competitor-monitoring/evals/evals.json` → `"evals"` (existing ids 1–3; use 4):
```json
{
  "id": 4,
  "prompt": "Set up AI citation tracking and brand-mention monitoring for our own brand.",
  "expected_output": "Own-brand observation run using watchlist/snapshot conventions and the ai_answer_engines measurement contract; coverage gaps recorded for failed engines; no demand-evidence claims.",
  "files": [],
  "must_mention": [
    "watchlist",
    "observation",
    "coverage",
    "cadence"
  ]
}
```

Append to `.agents/skills/marketing-strategy-builder/evals/evals.json` → `"evals"` (next free id from the command above):
```json
{
  "id": <next free integer>,
  "prompt": "Should we invest in AI answer-engine visibility work this quarter?",
  "expected_output": "Bottleneck diagnosis first (exposure, proof, conversion path, offer); smallest justified intervention with a named business outcome and stop rule; visibility metrics labelled intermediate measures; handoff to the website skill or an own-brand monitoring run; owner actions via contract.",
  "files": [],
  "must_mention": [
    "bottleneck",
    "stop",
    "owner",
    "handoff"
  ]
}
```

Append to `.agents/skills/social-digital-marketing-planner/evals/evals.json` → `"evals"` (next free id):
```json
{
  "id": <next free integer>,
  "prompt": "Set up our Reddit and community presence to improve AI visibility.",
  "expected_output": "Bottleneck justification required before any recurring program; human posting stated as repository operating policy, not a platform prohibition; authentic viewpoint non-delegable; owner actions surfaced via contract.",
  "files": [],
  "must_mention": [
    "bottleneck",
    "owner",
    "policy"
  ]
}
```

Append to `.agents/skills/evidence-scout/evals/evals.json` → `"evals"` (next free id):
```json
{
  "id": <next free integer>,
  "prompt": "Track whether ChatGPT and Perplexity mention our brand for category questions.",
  "expected_output": "AI answer-engine observation under the measurement contract; success/error/unsupported states with failure as unknown; coverage-gap protocol for credit-blocked engines; observations never treated as demand evidence; cadence and cost note recorded.",
  "files": [],
  "must_mention": [
    "coverage",
    "observation",
    "demand",
    "cadence"
  ]
}
```

- [x] **Step 7: Run the config gates**

Run: `python3 scripts/validate_skill_routes.py && python3 scripts/run_evals.py 2>&1 | tail -3 && bash scripts/validate_setup.sh 2>&1 | tail -2`
Expected: route parity passes, `All eval structure checks passed.`, `0 errors`.

- [x] **Step 8: Commit**

```bash
git add tests/test_website_launch.py config/workflow-routes.json config/skill-catalog.json .agents/skills/brand-website-designer-builder/evals/evals.json .agents/skills/competitor-monitoring/evals/evals.json .agents/skills/marketing-strategy-builder/evals/evals.json .agents/skills/social-digital-marketing-planner/evals/evals.json .agents/skills/evidence-scout/evals/evals.json
git commit -m "Route AEO/GEO and own-brand observation requests with eval coverage"
```

---

### Task 5: AI-answer observation pilot script (TDD)

**Files:**
- Create: `scripts/monitoring/__init__.py` (empty)
- Create: `scripts/monitoring/ai_answer_probe.py`
- Test: `tests/test_ai_answer_probe.py`

**Interfaces:**
- Consumes: env var names from Task 3 (read but not required in recorded mode); output conventions from `scripts/brand/check_lighthouse.py` (argparse, JSON stdout, boolean exit via SystemExit).
- Produces:
  - `normalize_observation(raw: dict) -> dict` — validated observation with keys: `engine` (str), `model` (str), `search_config` (str), `locale` (str), `timestamp` (str), `surface` (`api`|`consumer`|`ai_overview`), `prompt_type` (`unbranded_discovery`|`brand_seeded`|`decision_stage`|`educational`), `prompt_id` (str), `prompt_version` (int), `repetition` (int), `status` (`success`|`error`|`unsupported`), `brand_mentioned` (bool|None), `url_cited` (bool|None), `recommended` (bool|None), `answer_text` (str).
  - `diff_observations(current: list[dict], prior: list[dict]) -> dict` — `{'changes': [...], 'coverage': {'current': int, 'prior': int, 'compared': int, 'skipped_incompatible': int, 'skipped_failed': int}}`; compares only rows with identical `(engine, model, search_config, surface, locale, prompt_id, prompt_version)` and `status == 'success'` on both sides.
  - `build_summary(rows: list[dict], prior_rows: list[dict]) -> dict` — `{'observations': int, 'coverage_gaps': [{'engine': str, 'reason': str}], 'diff': dict|None, 'boundary': str}`.
  - CLI: `python3 scripts/monitoring/ai_answer_probe.py --panel <panel.json> --recorded <observations.jsonl> [--prior <observations.jsonl>] --out <run-dir>` — writes `evidence.jsonl`, `summary.json`, `report.md`; exits 1 on invalid input. Live API probing is NOT in this task (read-only pilot per spec §4.2).

- [x] **Step 1: Write the failing tests**

Create `tests/test_ai_answer_probe.py`:

```python
import json
import pytest
from scripts.monitoring.ai_answer_probe import normalize_observation, diff_observations, build_summary

BASE = {
    'engine': 'openai', 'model': 'gpt-x', 'search_config': 'web_search:on',
    'locale': 'en-US', 'timestamp': '2026-09-20T10:00:00Z', 'surface': 'api',
    'prompt_type': 'unbranded_discovery',
    'prompt_id': 'p01', 'prompt_version': 1, 'repetition': 1,
    'status': 'success', 'brand_mentioned': True, 'url_cited': False,
    'recommended': False, 'answer_text': '...',
}


def obs(**kw):
    return normalize_observation({**BASE, **kw})


def test_success_observation_normalized():
    row = obs()
    assert row['status'] == 'success' and row['brand_mentioned'] is True


def test_failed_probe_is_unknown_not_absent():
    row = obs(status='error', brand_mentioned=None, url_cited=None, recommended=None, answer_text='')
    assert row['brand_mentioned'] is None
    with pytest.raises(ValueError, match='status'):
        obs(status='error', brand_mentioned=False)


def test_invalid_status_rejected():
    with pytest.raises(ValueError, match='status'):
        obs(status='ok')


def test_surface_labels_separated():
    assert obs(surface='consumer')['surface'] == 'consumer'
    with pytest.raises(ValueError, match='surface'):
        obs(surface='chatgpt')


def test_prompt_type_labels_separated():
    assert obs(prompt_type='decision_stage')['prompt_type'] == 'decision_stage'
    with pytest.raises(ValueError, match='prompt_type'):
        obs(prompt_type='branded')


def test_diff_compares_only_compatible_successful():
    prior = [obs(brand_mentioned=False), obs(prompt_id='p02', brand_mentioned=True)]
    current = [obs(brand_mentioned=True), obs(prompt_id='p02', status='error', brand_mentioned=None, url_cited=None, recommended=None, answer_text='')]
    result = diff_observations(current, prior)
    assert result['changes'] == [
        {'prompt_id': 'p01', 'engine': 'openai', 'field': 'brand_mentioned', 'from': False, 'to': True}
    ]
    assert result['coverage']['compared'] == 1
    assert result['coverage']['skipped_failed'] == 1


def test_diff_skips_incompatible_config():
    prior = [obs(model='gpt-old'), obs(prompt_id='p03', locale='de-DE')]
    current = [obs(), obs(prompt_id='p03')]
    result = diff_observations(current, prior)
    assert result['changes'] == []
    assert result['coverage']['skipped_incompatible'] == 2


def test_summary_reports_coverage_gap_for_failed_engine():
    rows = [obs(engine='perplexity', status='error', brand_mentioned=None, url_cited=None, recommended=None, answer_text='')]
    summary = build_summary(rows, prior_rows=[])
    assert summary['coverage_gaps'] == [{'engine': 'perplexity', 'reason': 'error'}]
    assert 'demand' in summary['boundary'] or 'observation' in summary['boundary']
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_ai_answer_probe.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.monitoring'`.

- [x] **Step 3: Write the implementation**

Create empty `scripts/monitoring/__init__.py`, then `scripts/monitoring/ai_answer_probe.py`:

```python
"""Normalize and diff AI answer-engine observations; observations are not demand evidence."""
import argparse
import json
from pathlib import Path

STATUSES = ('success', 'error', 'unsupported')
SURFACES = ('api', 'consumer', 'ai_overview')
PROMPT_TYPES = ('unbranded_discovery', 'brand_seeded', 'decision_stage', 'educational')
FIELDS = ('engine', 'model', 'search_config', 'locale', 'timestamp', 'surface',
          'prompt_type', 'prompt_id', 'prompt_version', 'repetition', 'status',
          'brand_mentioned', 'url_cited', 'recommended', 'answer_text')
KEY = ('engine', 'model', 'search_config', 'surface', 'locale', 'prompt_id', 'prompt_version')
TRACKED = ('brand_mentioned', 'url_cited', 'recommended')


def normalize_observation(raw):
    if not isinstance(raw, dict):
        raise ValueError('observation must be an object')
    row = {k: raw.get(k) for k in FIELDS}
    if row['status'] not in STATUSES:
        raise ValueError(f"status: must be one of {STATUSES}")
    if row['surface'] not in SURFACES:
        raise ValueError(f"surface: must be one of {SURFACES}")
    if row['prompt_type'] not in PROMPT_TYPES:
        raise ValueError(f"prompt_type: must be one of {PROMPT_TYPES}")
    if type(row['prompt_version']) is not int or type(row['repetition']) is not int:
        raise ValueError('prompt_version and repetition: integer required')
    for k in ('engine', 'model', 'search_config', 'prompt_id'):
        if not isinstance(row[k], str) or not row[k]:
            raise ValueError(f'{k}: nonempty string required')
    if row['status'] == 'success':
        for k in TRACKED:
            if type(row[k]) is not bool:
                raise ValueError(f'{k}: boolean required on success')
    else:
        for k in TRACKED:
            if row[k] is not None:
                raise ValueError(f'{k}: must be null when status is {row["status"]}; failure is unknown, not absence')
    return row


def _key(row):
    return tuple(row[k] for k in KEY)


def diff_observations(current, prior):
    prior_ok = {_key(r): r for r in prior if r.get('status') == 'success'}
    changes, skipped_failed, skipped_incompatible, compared = [], 0, 0, 0
    for row in current:
        if row.get('status') != 'success':
            skipped_failed += 1
            continue
        old = prior_ok.get(_key(row))
        if old is None:
            skipped_incompatible += 1
            continue
        compared += 1
        for field in TRACKED:
            if row[field] != old[field]:
                changes.append({'prompt_id': row['prompt_id'], 'engine': row['engine'],
                                'field': field, 'from': old[field], 'to': row[field]})
    return {'changes': changes,
            'coverage': {'current': len(current), 'prior': len(prior), 'compared': compared,
                         'skipped_incompatible': skipped_incompatible, 'skipped_failed': skipped_failed}}


def build_summary(rows, prior_rows):
    gaps = sorted({(r['engine'], r['status']) for r in rows if r.get('status') != 'success'})
    return {'observations': len(rows),
            'coverage_gaps': [{'engine': e, 'reason': s} for e, s in gaps],
            'diff': diff_observations(rows, prior_rows) if prior_rows else None,
            'boundary': 'observation of configured surfaces only; not customer-demand evidence; failures are unknown, not absence'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--panel', type=Path, required=True)
    p.add_argument('--recorded', type=Path, required=True)
    p.add_argument('--prior', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    try:
        panel = json.loads(args.panel.read_text())
        assert isinstance(panel.get('prompts'), list) and panel['prompts'], 'panel.prompts must be a nonempty list'
        rows = [normalize_observation(json.loads(line)) for line in args.recorded.read_text().splitlines() if line.strip()]
        prior = [normalize_observation(json.loads(line)) for line in args.prior.read_text().splitlines() if line.strip()] if args.prior else []
    except (OSError, ValueError, AttributeError, AssertionError) as exc:
        print(json.dumps({'status': 'fail', 'errors': [str(exc)]}))
        return True
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'evidence.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    summary = build_summary(rows, prior)
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2))
    lines = ['# AI-answer observation report', '', f"Boundary: {summary['boundary']}", '',
             f"Observations: {summary['observations']}; coverage gaps: {len(summary['coverage_gaps'])}"]
    if summary['diff']:
        lines.append(f"Compared: {summary['diff']['coverage']['compared']}; changes: {len(summary['diff']['changes'])}")
    (args.out / 'report.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'status': 'pass', 'out': str(args.out), **summary}, default=str))
    return False


if __name__ == '__main__':
    raise SystemExit(main())
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_ai_answer_probe.py -q`
Expected: 8 passed.

- [x] **Step 5: Smoke-test the CLI end to end**

Run:
```bash
mkdir -p /tmp/probe-test && printf '%s\n' '{"prompts": [{"id": "p01", "version": 1, "type": "unbranded_discovery", "text": "best X for Y"}]}' > /tmp/probe-test/panel.json && printf '%s\n' '{"engine":"openai","model":"gpt-x","search_config":"web_search:on","locale":"en-US","timestamp":"2026-09-20T10:00:00Z","surface":"api","prompt_type":"unbranded_discovery","prompt_id":"p01","prompt_version":1,"repetition":1,"status":"success","brand_mentioned":true,"url_cited":false,"recommended":false,"answer_text":"..."}' > /tmp/probe-test/obs.jsonl && python3 scripts/monitoring/ai_answer_probe.py --panel /tmp/probe-test/panel.json --recorded /tmp/probe-test/obs.jsonl --out /tmp/probe-test/run1
```
Expected: JSON with `"status": "pass"`, and `/tmp/probe-test/run1/` contains `evidence.jsonl`, `summary.json`, `report.md`.

- [x] **Step 6: Run the full suite**

Run: `python3 -m pytest tests/ -q`
Expected: all pass — 576 tests (564 currently collected + 4 routing tests from Task 4 + 8 probe tests).

- [x] **Step 7: Commit**

```bash
git add scripts/monitoring/__init__.py scripts/monitoring/ai_answer_probe.py tests/test_ai_answer_probe.py
git commit -m "Add read-only AI-answer observation pilot with failure-aware diffing"
```

---

### Task 6: Final gate run

**Files:** none (verification only).

- [x] **Step 1: Run every CI gate**

Run: `bash scripts/validate_setup.sh 2>&1 | tail -2 && python3 scripts/validate_skill_routes.py && python3 scripts/run_evals.py 2>&1 | tail -2 && python3 -m pytest tests/ -q 2>&1 | tail -2`
Expected: `0 errors`, route parity pass, `All eval structure checks passed.`, 576 passed.

- [x] **Step 2: Report**

Summarize per task: files changed, gate results, and the deliberate deferrals (live API probing, the one-project pilot run itself, mention-listening collector, DEO commerce scaffolding, GA4/server-log automation, CrUX/funnel-loop additions) per spec §4.6 and the self-review below.

---

## Self-review notes (planner, revised after the 2026-09-20 gap review)

**Spec coverage**

| Spec section | Where |
|---|---|
| §0 decision rule + feedback loop | Task 2 Steps 2–3 (bottleneck, outcome, stop rule, observation→change→effect→result→decision) |
| §1 binding claim table | Stays in the spec; Task 1 references point to it and carry no stronger claim |
| §2.1 SEO | No setup change required by §4; existing coverage is the base |
| §2.2 SMO + corrected Reddit framing | Task 2 Step 3 (policy vs prohibition, viewpoint vs mechanics) |
| §2.3 AEO | Task 1 Step 1 (question mining, capsules-as-hypotheses, supported schema only, freshness, Bing WMT first-party feed, FAQ/HowTo deprecation) |
| §2.4 GEO | Task 1 Step 1 (observation, entity consistency, Wikidata, competitive citation-source mapping, crawler diagnostics) |
| §2.5 DEO | Task 1 Step 2 (conditional framing, owner-gated approvals, truth inputs, MCP/`/.well-known`/llms.txt deferred) |
| §2.6 SXO | Message-match boundary in Task 1 Step 1; CrUX field data, scheduled funnel-drop loop and Playwright friction fixes are per-project execution, explicitly deferred here |
| §3.1 probe contract | Task 5 implementation (surface + `prompt_type` labels, success/error/unsupported, failure=unknown, compatible-window diff incl. locale, coverage; 15–30 panel and "not a commercial-tool replacement" in Task 1 Step 1) + Task 3 policy |
| §3.2 analytics + `not_requested` fallback | No repo change: GA4/server-log setup is per-project execution, not repo setup. Deliberate gap — agents reach the boundary via `campaign-tracking.md` and Task 1's message-match paragraph |
| §3.3 crawler diagnostics | Task 1 Steps 1 & 4 |
| §3.4 feed contract | Task 1 Step 2 (documentation level; spec requires no code) |
| §3.5 message-match boundary | Task 1 Step 1 (message-match paragraph) |
| §4.1 entry points | Tasks 1–2 |
| §4.2 pilot | Task 5 ships the recorded-mode tooling; running the actual one-project pilot is post-plan execution, matching the spec's pilot-before-build order |
| §4.3 owner actions | Task 2 Step 1 |
| §4.4 provider registration | Task 3 |
| §4.5 routing/catalog/evals | Task 4 — all five changed skill/reference sets get eval coverage; both catalog entries updated for parity |
| §4.6 deferrals | Honored: no new skill, no signed authorization machinery, no MCP/discovery files, no launch-contract migration, no schema-presence blocker (the optional correctness validator was not built; spec says "may") |
| §5 sequencing | Task order 1→5 follows steps 1–3 |
| §6 retained work | Question mapping ✓, prices/terms ✓, crawler diagnostics ✓, message-match + funnel review ✓ (boundary in Task 1), own-brand observation ✓ (tooling), owner handoff ✓ |
| §7 source register | Task 1 sources are all in the register; the DEO reference defers its vendor docs to re-fetch instead of quoting unregistered sources |

**Deliberate non-goals:** live LLM API probing (pilot is recorded-mode), the pilot run itself, brand_mention_listening collector (`collector_provider: pending_pilot`), GA4/server-log automation, CrUX/funnel-loop additions. There is no "own-brand lane" inside the competitor-monitoring skill; every handoff describes applying its documented watchlist/snapshot/diff conventions to the user's own brand.

**Type consistency:** `normalize_observation` / `diff_observations` / `build_summary` signatures match between Step 1, Step 3 and the Interfaces block; `prompt_type` and `locale` appear in FIELDS/KEY in both tests and implementation. Eval IDs: website skill uses 8 (1–7 taken), competitor-monitoring uses 4 (1–3 taken); the other three files use the next free integer verified by the command in Task 4 Step 6.

**Forward references:** Tasks 1 and 3 reference paths created in Tasks 2 and 5 — land tasks in order (Global Constraints).
---

## Implementation Progress Log

Executed via superpowers:subagent-driven-development on branch `feat/search-visibility-setup`
(branched off `main` at `12d83ad`; SDD ledger at `.superpowers/sdd/2026-09-20-search-visibility-setup/progress.md`).

Pre-flight conflict scan: no two tasks write the same file. Couplings are forward references only
(Task 1 → `references/owner-actions.md` from Task 2 and `scripts/monitoring/ai_answer_probe.py` from Task 5;
Task 3 → Task 5 env-var/collector names; Task 4 → asserts Tasks 1–3 content). Ruling: land 1→6 in order,
no parallel dispatch.

| Task | Status | Commit | Gates | Notes |
| --- | --- | --- | --- | --- |
| 1. Website visibility references | done | `bcf70c8` | 0 errors / 162 evals / routes pass / 564 tests | SPEC PASS + QUALITY PASS, zero findings; new files byte-exact vs plan |
| 2. Owner-action contract | done | `abf742d` | 0 errors / 162 evals / routes pass / 564 tests | SPEC PASS + QUALITY PASS; 5 nits, 0 must-fix. Nits 1-4 are inherited plan-text defects (see erratum ruling in ledger), deferred to the final fix dispatch |
| 3. Provider registration | done | `0717237` | 0 errors / 162 evals / routes pass / 564 tests | SPEC PASS + QUALITY PASS; both entries byte-exact, 26 pre-existing entries untouched, `capability_lookup.py` surfaces `ai_answer_engines`. 3 nits, 0 must-fix |
| 4. Routing/catalog/eval parity | done | `fb8e073` + fix `388b9a1` | 0 errors / 167 evals / routes pass / 568 tests | 1 fix round: bare `"AEO"` matched as an unbounded substring and hijacked `Kaeon`/`Aeon`/archaeology prompts. Bounded to `"AEO audit"` + `"AEO/GEO"`; 233-prompt probe clean. Plan text updated to match |
| 5. AI-answer observation pilot | done | `60b6db6` | 0 errors / 167 evals / routes pass / 576 tests | SPEC PASS + QUALITY PASS; offline grep clean, no false-negative survives adversarial fixtures, 4 of 5 reviewer mutations caught. 6 nits, 0 must-fix |
| 6. Final gate run | done | n/a (verification only) | 1 warning / **0 errors**, `All eval structure checks passed.`, `{"passed": true, "errors": []}`, **576 passed** | Every target in the plan hit exactly |

### Final whole-branch review — VERDICT: SHIP

One review pass on the most capable model over `12d83ad..60b6db6`, one fix dispatch, one scoped re-review.

Three must-fixes, all of them coherence defects only a whole-branch view could surface. Two are further
instances of the Task 4 defect class — the plan mandated bare match tokens and `scripts/route_workflow.py:230`
matches casefolded substrings with no word boundary:

1. **Routed destination had no instructions.** `competitor-monitoring` was advertised in the router and catalog
   for own-brand AI-visibility work while its `references/workflow.md` was untouched and its line 8 provider
   exclusion actively steered away from it. Fixed by a new paragraph at `references/workflow.md:16`: own-brand
   watchlist rows under the existing snapshot/diff conventions, `ai_answer_probe.py` in recorded mode, both
   capability IDs, all four §3.1 measurement elements inline, a provider carve-out scoped to those two
   capabilities only, and a customer-voice handoff to `references/customer-voice.md`.
2. **`"brand mentions"` stole voice-of-customer requests.** "What do customers say about us — pull brand
   mentions" moved `business-strategist` → `competitor-monitoring`, so the VOC pass mandated by `AGENTS.md:64`
   never ran. Bounded to `"track brand mentions"` + `"own-brand mentions"`.
3. **`"agent readiness"` hijacked app-UI prompts.** At 15 characters it beat `"app screens"` and `"dashboard UI"`
   under longest-phrase-wins, routing into a lane that declares `"forbidden": ["brand-website-designer-builder"]`.
   Bounded to `"agent readiness audit"` + `"website agent readiness"`.

Nits closed in the same dispatch: the two unresolvable pointers in `marketing-strategy-builder/references/workflow.md`
(now qualified to `brand-website-designer-builder/references/{experimentation,campaign-tracking}.md`); the missing
`next_action` encoding in `references/owner-actions.md:7` (highest-priority action in `next_action`, remainder as
`open_blockers` entries prefixed `owner action: `, verified against `schemas/project-manifest.schema.json`); the
§0 bottleneck-gate clause missing from `aeo-geo-visibility.md:3`; and the §1 line citation in the spec (`143–147`).

| Stage | Commits | Outcome |
| --- | --- | --- |
| Fix dispatch (1 of 1 permitted) | `f7c9dfc`, `a75a0cf` | 3 must-fix + 5 nits closed |
| Scoped re-review | n/a | **SHIP** — all 3 must-fixes verified closed; substring test over the new tokens found **zero** substring relations in either direction, eliminating the bare-token failure mode; spec walk §0–§6 found no silent drops; evidence-discipline audit clean on every forbidden pattern |
| Docs | `c0be157` | Spec, adversarial review and this plan committed |

Final gates: **1 warning / 0 errors**, **167 eval cases**, `{"passed": true, "errors": []}`, **576 passed**, clean tree.

Residuals accepted, not fixed — each recorded with its cost:

- `scripts/route_workflow.py:230` has no word-boundary logic, so `"AEO audit"` still fires inside a synthetic
  `archaeo audit`. Adding boundaries would re-scope all ~40 routes on the strength of prompts that are not
  plausible English. Cost if wrong: a contrived prompt reaches `website-build`.
- `competitor-monitoring/SKILL.md:3` still describes the skill as competitor-only. The router and catalog carry
  the authoritative intent and `references/workflow.md:16` now carries the instructions.
- "agent readiness audit of our dashboard UI" resolves to `website-build`. The prompt is genuinely ambiguous.
- `tests/test_ai_answer_probe.py:71` asserts `'demand' in boundary or 'observation' in boundary`, so a mutated
  boundary of `'validated market demand signal'` passes. The shipped boundary string is correct; the test is the
  weak part, and it is byte-exact to this plan.
- `scripts/monitoring/ai_answer_probe.py:84` validates panel input with `assert`, which `python3 -O` strips. The
  evidence-discipline checks use real `raise ValueError` and are unaffected.
- `config/source-capabilities.json`: the four `requires_env` keys are per-engine alternatives but read as
  all-required. `requires_env` is display-only (`capability_lookup.py:86`); recorded mode reads no key at all.

## Errata — superseded after an independent review (2026-09-20)

This plan is executed; the progress log above is the record of that execution. An independent review
(`docs/search-visibility-implementation-review-2026-09-20.md`) subsequently found five material defects that
this plan's literal content either mandated or failed to catch, and the fixes are tracked in
`docs/superpowers/plans/2026-09-20-search-visibility-review-fixes.md`. **Do not replay the literal blocks below
without these corrections.**

1. **Line 74 (Task 1) — wrong markup scopes.** "Organization-level MerchantReturnPolicy and OfferShippingDetails"
   conflates scopes: `OfferShippingDetails` is an offer-level type (`Offer.shippingDetails`); the organization-level
   shipping equivalent is `Organization.hasShippingService` → `ShippingService`. Corrected in the working tree at
   `.agents/skills/brand-website-designer-builder/references/deo-agent-readiness.md:5`.
2. **Line 145 (Task 2) and the `owner action: ` encoding rule** — superseded. `open_blockers` is now reserved for
   genuine dependencies; accepted-but-optional actions go to `next_action` as a concise ordered set. Corrected at
   `references/owner-actions.md:7`.
3. **The `ai_answer_probe.py` literals in Task 5** shipped three defects the plan did not anticipate: repeated
   observations collapsed to last-row-wins so file order could flip a reported gain/loss; the selected panel was
   validated then ignored, so an empty recording reported zero coverage gaps; and successful observations were
   accepted without locale, timestamp or source answer. Fixed in the follow-up plan.

Two of the residuals listed immediately above are now closed rather than accepted: the boundary assertion is
exact-equality (`tests/test_ai_answer_probe.py`) and the panel check raises `ValueError` instead of asserting.
