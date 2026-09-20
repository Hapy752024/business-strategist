# Digital-Marketing Optimization Plan — Six-Layer Search Stack (revised)

Status: revised 2026-09-20 after two adversarial reviews ([review record](digital-marketing-optimization-plan-adversarial-review.md) plus a Codex challenge review). This revision corrects evidence claims, reorders the approach around the business bottleneck, defines measurement validity, and narrows the initial change.
Framework source: James Dooley, "Modern Search Optimisation Stack" (x.com/james_dooley/status/2100907455890800881, 2026-09-18).

## 0. Decision rule first: diagnose the bottleneck before selecting layers

The six layers (SEO, SMO, AEO, GEO, DEO, SXO) are an inventory of possible work, not a program to impose. Before prescribing any layer or monitoring investment, state:

1. **Observed bottleneck** — does the business lack qualified exposure, persuasive proof, a usable conversion path, or an offer customers want? Use the existing decision questions in [references/evidence-registry.md](../references/evidence-registry.md) (lines 49–62) and the channel-selection rule in [marketing-strategy-builder/references/workflow.md](../.agents/skills/marketing-strategy-builder/references/workflow.md) (lines 143–147): customer fit, conversion bridge, source-cohort metric, stop rule, one primary acquisition motion, explicit deferrals.
2. **Relevant buyer behavior** — where this business's actual buyers discover, compare and decide (from customer evidence, not the generic framework).
3. **Available assets and owner capacity** — content, data, reviews, time; a weekly cadence the owner cannot sustain is not a plan.
4. **Smallest justified intervention** with a named business outcome (qualified enquiries, bookings, purchases, retained value) and a **stop/change rule**. Visibility metrics are intermediate measures, never the outcome; where outcome attribution is unavailable, record that uncertainty rather than implying it.

Feedback procedure for everything below: **observation → proposed change → expected business effect → result → next decision**, reusing the existing analytics/experimentation guidance (`references/experimentation.md`, `references/campaign-tracking.md`). Do not build the full stack for a business that has not justified it.

## 1. What the evidence actually supports

Every consequential claim is bound to source, population, measured outcome and applicability limit. The full register is in §7.

| Claim usable in agent outputs | Source / population / outcome | Applicability limit |
|---|---|---|
| AI-referred visitors can convert far above organic | Seer case study (2025-06-03): ChatGPT 15.9% vs organic 1.76% — **one client**; Adobe Q1 2026: 1.42x relative vs non-AI traffic — **US retail only** | Not a general benchmark; do not quote "4–9x" |
| Brand web mentions correlate with AI Overview visibility more strongly than backlinks do (0.664 vs 0.218) | Ahrefs 75,000-brand correlation study (2025-12-12) | Ahrefs explicitly warns correlation does not establish that increasing mentions increases visibility; do not use as proof that outreach causes citations |
| Adding citations, statistics and quotations improved visibility up to ~40% | Princeton et al., KDD 2024 (arXiv:2311.09735), benchmark queries | Benchmark visibility metric, varies by domain; does not establish qualified-customer uplift |
| Answer-first capsules (≈40–60 words) are a reasonable structure to test | Practitioner consensus; Ahrefs word-count correlation ≈0.04 | A near-zero length correlation cannot establish capsule superiority; treat as hypothesis, not rule |
| JSON-LD showed no measurable AI-citation improvement | Ahrefs matched observational study, 1,885 pages, May 2026 | Concurrent changes and a short window; say "no measurable improvement in this sample/window", not a universal causal null. Keep schema for entity clarity and rich results |
| ~82–84% of AI citations come from "earned media" | Muck Rack (Dec 2025, May 2026) | Category includes research, government, encyclopedic and third-party corporate sources; **not** the fraction winnable via journalist outreach |
| Blocking AI crawlers correlated with −23% monthly visits | Rutgers/Wharton (Dec 2025) | Publisher population; direction of causality not isolated |

Deprecated or weak levers: `llms.txt` (0.1% of AI-bot visits in OtterlyAI's 90-day experiment; Google states it is unused — do not prioritize); universal schema-citation claims; vendor conversion percentages generally (small, US/English-skewed samples).

## 2. Per-layer program: agent work vs. owner work

Owner-action mechanics are defined in §4.3 — nothing below becomes a recurring obligation by appearing here.

### 2.1 SEO
- **Agent:** technical audits (crawlability, indexation, canonicals, redirects, orphans); keyword/question research and intent clustering from audience evidence; attribute-rich schema drafts with validation; internal-link proposals; content briefs; GSC-API freshness/decay detection; CWV measurement and code fixes under Lighthouse CI gates.
- **Owner:** approve every published content change (Google's scaled-content enforcement makes unreviewed publishing the largest agentic SEO risk); supply firsthand experience, credentials, proprietary data; conduct journalist relationships and authorize any outreach send.
- **Agent-verifiable vs owner-only truth:** facts checkable against current authoritative sources or an already approved source record are rechecked by the agent; only unavailable firsthand facts, changed commercial commitments and actual decisions go to the owner.

### 2.2 SMO
- **Agent:** profile/entity-consistency audit with drafted fixes; own-brand mention monitoring via licensed APIs; repurposing drafts and scheduling queues (publish only via official APIs with owner authorization); Reddit/forum opportunity surfacing and draft replies.
- **Owner:** authentic voice and viewpoints (founder/employee posts in own words); genuine community participation; creator/journalist relationships; UGC incentive and rights design.
- **Policy framing (corrected):** human posting is this repository's **selected operating policy**, not a claimed platform prohibition. Reddit's Responsible Builder Policy does not establish a "90/10" ratio, and Reddit's app guidance explicitly supports compliant, disclosed automation. Check the platform, community and use case before stating any external restriction. The existing repository prohibition on unauthorized outreach/publishing stands regardless. Distinguish ownership of an authentic viewpoint (non-delegable) from the mechanics of publishing an owner-approved post (delegable where the platform permits).

### 2.3 AEO
- **Agent:** question mining (PAA APIs, GSC question-regex pulls, community phrasing) → clustered question→URL map derived from actual audience evidence; answer-first restructuring drafts (capsules, comparison tables, HowTo steps) as testable hypotheses; schema drafts for currently supported features only; freshness flags per page type; snippet/PAA ownership tracking; Bing Webmaster Tools AI Performance pulls (only first-party AI citation feed).
- **Owner:** verify owner-only facts in extractable blocks (prices, guarantees, firsthand claims) before publication. Note: Google deprecated HowTo rich results (2023) and FAQ rich results (May 2026) — do not present FAQ markup as a rich-result or citation lever.

### 2.4 GEO
- **Agent:** AI-answer observation under the measurement contract in §3; entity-consistency audit and corrections where edit access exists; Wikidata entry maintenance; competitive citation-source mapping; AI-crawler/access diagnostics (§3.3).
- **Owner:** earned-media work (data-driven PR, expert quotes with real credentials, relationships); authentic community participation; the strategic decision on AI **training**-crawler policy (IP trade-off) — after being shown each vendor control's actual effect (§3.3), not a generic "block training bots" default.
- Do not promise citation outcomes from any single lever; see §1 limits.

### 2.5 DEO (conditional layer — only for businesses with commerce/comparable offers)
- **Agent:** Product/Offer and policy markup encoded **only** from owner-confirmed facts; plain-HTML pricing/comparison pages; feed generation and transforms **after** the feed contract in §3.4 is in place; decision-stage prompt panels (separate from educational prompts).
- **Owner:** platform approvals (OpenAI merchant, Merchant Center/UCP onboarding, GBP verification — identity-gated); all truth inputs (prices, stock, return windows, guarantees); review-generation decisions (real customers only; fake reviews are fraud).
- DEO is an emergent label (coined 2026-09); its mechanics (ACP, UCP, feeds) are real, but recommendation→selection→transaction conversion has almost no public data. Present it as conditional infrastructure, not a promised channel.
- **Deferred from initial change:** MCP commerce scaffolding, `/.well-known` discovery files, `llms.txt` — build only when a selected integration needs them.

### 2.6 SXO
- Existing coverage stays the base (launch contract, Lighthouse budgets, experimentation, consent).
- **Agent additions:** message-match diagnostic (see boundary in §3.5); CrUX field-data collection; scheduled funnel-drop review loop; form/checkout friction fixes with Playwright E2E tests.
- **Owner:** experiment launch and winner promotion; pricing/guarantee/certification wording; consent architecture.

## 3. Measurement contracts

### 3.1 AI-answer observation (probe) contract
An API probe measures **the configured API experience**, not what a buyer sees in a consumer product. Rules:

- Label observations by surface: API-with-search-config, consumer product, AI Overviews — never pooled.
- Prompts selected from relevant customer questions/search evidence; distinguish unbranded discovery prompts from brand-seeded reputation checks; version the panel.
- Each observation records: engine, model/version, search/tool configuration, locale, timestamp, prompt ID/version, repetition index, and **collection status (success / error / unsupported)**. Failures are recorded as *unknown*, never as absence of mention.
- Diff reports compare only compatible successful observations (same model, config, panel version, window); report panel coverage; test partial-provider failure and configuration-change handling before trusting trends.
- Distinguish correct-entity mention, recommendation, and supporting citation; retain the full source answer so changes can be diagnosed.
- Start with a narrow, decision-relevant panel (15–30 prompts); expand only when findings change a decision. Do not describe this as a replacement for commercial visibility tools, and never treat saved model responses as customer-demand evidence.
- A credit-blocked or failed engine is a **coverage gap** (recorded, reported, re-run after top-up) — per the repository provider policy, never evidence of absence.

### 3.2 Analytics
- GA4 AI-referrer channel group where analytics is installed; note the native GA4 AI channel misses Perplexity and referrer-stripped traffic.
- **Fallback when the owner declined analytics** (`not_requested` in the launch contract): server-log referrer analysis for AI referrers replaces the GA4 channel; do not assume GA4/PostHog exists.

### 3.3 Crawler/access diagnostics (corrected)
- Describe each vendor control's actual effect before implementing: `Google-Extended` is a **product token** (no separate HTTP user agent) whose control covers training **and grounding in Gemini Apps and Grounding with Google Search on Vertex AI**; it cannot be observed via user-agent logs. OpenAI and Anthropic operate independent training vs. search/retrieval bots. Google Search inclusion is a separate boundary.
- No claimed "mainstream" configuration. The owner selects per-vendor policy; the agent implements and verifies against server logs where a crawler actually exists. The existing vendor-specific rule in `seo-performance.md` (line 9) already governs; also check CDN-level defaults (e.g., Cloudflare blocks AI crawlers by default for new domains since Jul 2025).

### 3.4 Commerce feed contract (before any scheduled publication)
- Name the authoritative inventory/price source and its freshness limit; pushes older than the limit fail closed.
- Define target-specific replacement/deletion semantics: a product removed from the source must be withdrawn, not merely not-updated; price/stock corrections must be confirmed applied.
- Delivery reconciliation: track acknowledgements, rejections and retries; alert the operator on stale input, rejected updates and exhausted retries.
- Acceptance tests required before enabling scheduled pushes: stale input, removed products, rejected updates, delayed retries.

### 3.5 Message-match boundary
The AI-referrer channel group does **not** supply the visitor's conversation or the recommendation that sent them. Compare observed probe contexts or legitimately supplied conversations against landing pages as a diagnostic; do not present them as the actual context of individual AI-referred visits. Observable conversions and attribution limits follow the existing [campaign measurement contract](../.agents/skills/brand-website-designer-builder/references/campaign-tracking.md).

## 4. Agent-setup changes (narrowed)

### 4.1 Entry points — the actual fix
- Add a short **conditional load instruction** to [maintenance.md](../.agents/skills/brand-website-designer-builder/references/maintenance.md) (the real existing-site audit/repair entry point): when the task is an AEO/GEO/visibility audit, load the new references. Linking from `seo-performance.md` alone is insufficient — new builds load it, audits do not.
- Give `marketing-strategy-builder` and `social-digital-marketing-planner` workflows a **selection rule and explicit handoff**: a visibility task is dispatched only when the §0 bottleneck diagnosis justifies it. Focused answers and content execution stay scoped per [references/task-scope.md](../references/task-scope.md). No new orchestration layer.
- New references (written as procedure, not advice): `references/aeo-geo-visibility.md` and `references/deo-agent-readiness.md` on the website skill, incorporating §1's evidence limits.

### 4.2 Monitoring pilot before build
- The competitor-monitoring skill documents watchlist/snapshot/diff **conventions**; there is no reusable `scripts/monitoring/` machinery in the tree. Do not claim or assume one.
- Step 1: a **read-only pilot** (single script, one or two engines, licensed sources only) producing the §3.1 observation report for one project, to settle what output is actually decision-useful.
- Step 2 (only if the pilot's output changes decisions): automate into the snapshot/diff layout under the project's research runs, with evals.

### 4.3 Owner-action contract — integrated with existing manifests
- Scope: include only decisions/actions relevant to the requested deliverable; never append recurring programs to narrow copy work.
- States: `proposed / accepted / deferred / completed` — a suggestion the owner never accepted does not recur on resume.
- **Persistence: write accepted actions and genuine blockers into the project manifest's existing `next_action` / `open_blockers` fields** (the fields the workspace-lifecycle resume flow already reads). A human-readable `owner-actions.md` may render them, but the manifest is the source of truth — no parallel tracking artifact.
- Reuse approved factual inputs across runs; ask the owner only about unavailable firsthand facts, changed commercial commitments and actual decisions. Preserve publication authorization already granted in the session.

### 4.4 Provider registration
- Probe/monitoring providers (LLM APIs, listening APIs) must be added to `config/source-capabilities.json` and the evidence-scout provider policy with: credential env vars, the repository `insufficient_credits` protocol (§3.1 coverage-gap rule), and a cost/cadence note (recurring panels × engines × repetitions) even under the pre-authorized spend policy.

### 4.5 Routing, catalog, evals
- `config/workflow-routes.json` match-term additions (e.g., "brand mentions", "AI citation tracking" → monitoring; "AEO", "structured data audit" → website skill) **together with** `config/skill-catalog.json` parity (`scripts/validate_skill_routes.py` enforces).
- Every new or changed skill/reference set gets `evals/evals.json` coverage — CI runs `scripts/run_evals.py`; routing parity alone is not the whole contract.

### 4.6 Explicitly deferred (do not build "because cheap")
New standalone visibility skill, signed community-style authorization machinery, MCP commerce scaffolding, discovery files (`llms.txt`, `/.well-known`), and any schema launch-contract migration — each waits until a selected integration justifies it. Schema-coverage enforcement (the proposed `check_structured_data.py` as a launch blocker) is **not** adopted: markup presence is not an outcome. A scoped validator may check **correctness of present markup** (prices, availability, ratings matching visible text) and report coverage as recommendation/not-applicable only.

## 5. Sequencing (per the reviews' revision order)

1. **Correct and persist evidence**: the §1 claim table and source register live in this document; skills quote from it, not from memory.
2. **Connect entry points** (§4.1) and adopt the §0 bottleneck rule in marketing/social workflows.
3. **Run the narrow observation pilot** (§4.2): baseline AI-answer panel + mention watch + crawler/access diagnostic for one project → first decision-relevant report with measurement limits and an outcome/stop rule.
4. **On-site levers where justified**: answer-structure drafts, freshness program, message-match diagnostic, feed contract (DEO only, commerce cases, after §3.4 tests).
5. **Automate what proved useful**; expand providers or commerce integrations only after their outputs change decisions.

## 6. Work retained from the original plan (narrowed)

| Addition | Benefit | Condition |
|---|---|---|
| Customer-question mapping and clearer answers | Page relevance and comprehension | Questions from actual audience evidence; no universal word-count rules |
| Accurate readable prices, terms, comparisons | Human and machine offer evaluation | Owner-confirmed facts; applicable page types |
| Crawler/content-access diagnostics | Finds actionable discovery obstruction | Vendor-specific selected policy (§3.3) |
| Message-match and funnel review | Connects iteration to customer outcomes | Observed context vs inferred attribution kept separate (§3.5) |
| Own-brand/citation observation | Reveals factual errors, missed sources | Narrow panel; sampling and surface limits stated (§3.1) |
| Owner handoff via manifest fields | Makes missing inputs actionable | Accepted work and genuine blockers only (§4.3) |

## 7. Source register

All external sources retrieved 2026-09-19/2026-09-20; living documents are marked. Only claims discussed here were verified.

- [Seer: ChatGPT traffic conversion case study](https://www.seerinteractive.com/insights/case-study-6-learnings-about-how-traffic-from-chatgpt-converts) — 2025-06-03, single client.
- [Adobe: Q1 2026 AI traffic, US retail](https://business.adobe.com/blog/ai-traffic-surge-retail-sites-not-machine-readable) — Q1 2026.
- [Ahrefs: 75,000-brand correlation study](https://ahrefs.com/blog/ai-brand-visibility-correlations/) — 2025-12-12; authors caution against causal reading.
- [Ahrefs: schema and AI citations](https://ahrefs.com/blog/schema-ai-citations/) — May 2026.
- [Princeton et al.: GEO (arXiv:2311.09735)](https://arxiv.org/abs/2311.09735) — KDD 2024.
- [Muck Rack: What Is AI Reading?](https://muckrack.com/blog/what-is-ai-reading-may-2026) — May 2026; [earned-media category definition](https://www.globenewswire.com/news-release/2026/05/07/3290268/0/en/generative-pulse-earned-media-consistently-drives-ai-citations-holding-at-84.html) — 2026-05-07, issuer press release.
- [Google: common crawlers / Google-Extended](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers#google-extended) — living documentation.
- [Google: HowTo/FAQ rich-result changes](https://developers.google.com/search/blog/2023/08/howto-faq-changes) — 2023-08-08; [Search documentation updates](https://developers.google.com/search/updates) — FAQ deprecation effective 2026-05-07.
- [Google: AI features and websites](https://developers.google.com/search/docs/appearance/ai-features) — living documentation.
- [OpenAI API: web search tool](https://developers.openai.com/api/docs/guides/tools-web-search) — living documentation.
- [Reddit: Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy) and [app labeling/automation guidance](https://support.reddithelp.com/hc/en-us/articles/45376380316052-Apps-on-Reddit-and-how-to-get-a-label-for-your-app) — living policies.
- Rutgers/Wharton AI-crawler-blocking study — Dec 2025 (via PPC Land coverage).
- OtterlyAI llms.txt 90-day experiment — 2025 (living blog).
- Dooley stack post — 2026-09-18; DEO term origin: USA Today press release — 2026-09-03.

Full per-layer research reports (SEO/SMO/AEO/GEO/DEO/SXO, each with dated source lists) were produced in-session on 2026-09-19; they inform this plan but the binding evidence for agent outputs is the table in §1 and this register.
