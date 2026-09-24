# Adversarial review: digital-marketing optimization plan

Reviewed: 2026-09-19. Verdict: **FLAG — revise before implementation.**

Scope: `docs/digital-marketing-optimization-plan.md` and the relevant agent instructions, marketing/monitoring/website skills, references, routing/catalog configuration and supporting scripts. `projects/` was excluded. This is a review of material effects on agent outputs, not an exhaustive audit of every skill. Architecture preferences, test-coverage gaps and rare edge cases were excluded. The plan and implementation remain unchanged.

The plan contains useful work, but its default sequence would encourage the agent to produce visibility dashboards and recurring activity before establishing whether either improves the selected business outcome. Some new guidance would also be less accurate than the existing instructions. Keep the useful content and measurement additions; correct the decision rules and factual errors first.

**1. High priority: the evidence is stronger in the headlines than in the underlying studies.**

Plan locations: lines 22–30, 62, 86 and 155–166.

- “AI-referred traffic converts 4–9x organic” is not supported as a general benchmark. Seer's 15.9% versus 1.76% result comes from one client. Adobe's March 2026 finding concerns US retail and is a 42% relative improvement versus non-AI traffic: 1.42x, not 4–9x. These are different populations and comparison groups. [Seer](https://www.seerinteractive.com/insights/case-study-6-learnings-about-how-traffic-from-chatgpt-converts), [Adobe](https://business.adobe.com/blog/ai-traffic-surge-retail-sites-not-machine-readable).
- Ahrefs explicitly warns that its YouTube/brand-mention correlations do not establish that increasing those metrics increases AI visibility. Using the correlation as the reason to prescribe appearances or outreach exceeds the evidence. [Ahrefs correlation study](https://ahrefs.com/blog/ai-brand-visibility-correlations/).
- The GEO paper's reported improvement is benchmark visibility, varies by domain, and does not establish a general uplift in qualified customers. A near-zero word-count correlation also cannot establish that 40–60-word capsules outperform other formats. [GEO paper](https://arxiv.org/abs/2311.09735).
- The schema study uses matched observational pages and acknowledges concurrent changes and a short measurement window. Prefer “no measurable citation improvement in this sample/window” to a universal causal null. [Ahrefs schema study](https://ahrefs.com/blog/schema-ai-citations/).
- Muck Rack's earned-media category includes research, government, encyclopedic and third-party corporate sources. Its percentage cannot be read as the fraction of citations a founder can win through journalist outreach. [Muck Rack's study announcement](https://www.globenewswire.com/news-release/2026/05/07/3290268/0/en/generative-pulse-earned-media-consistently-drives-ai-citations-holding-at-84.html).

Material consequence: the agent can confidently recommend the wrong channel, overstate likely returns and turn tentative formatting ideas into universal rules.

Required revision: bind consequential claims to a direct source, population, outcome measured and applicability limit. Persist those links in the plan or a repository reference. “Seven reports available in session; regenerate on request” is not a reusable evidence base for future agent runs. The introductory caveat does not repair stronger claims later in the document.

**2. High priority: select the business bottleneck before selecting layers or monitoring work.**

Plan locations: lines 36–49, 139–153.

The six layers are a useful inventory, but the fixed phases make multi-engine monitoring the first investment and off-site activity a later default. The plan does not first decide whether the site lacks qualified exposure, persuasive proof, a usable conversion path, or an offer customers want. Its owner-action fields emphasize cadence and evidence payoff, without requiring a business outcome or stopping condition.

The repository already has the stronger rule: [marketing workflow, lines 143–145](../.agents/skills/marketing-strategy-builder/references/workflow.md) requires customer fit, conversion bridge, source-cohort metric, stop rule, one primary acquisition motion and explicit deferrals. [Evidence registry, lines 49–62](../references/evidence-registry.md) supplies the decision questions. Those should govern the new capabilities.

Required revision: before prescribing a layer, state the observed bottleneck, relevant buyer behavior, available assets and owner capacity. Select the smallest intervention and name the outcome that will continue, change or stop it. Use qualified enquiries, bookings, purchases or retained value where observable; label visibility as an intermediate measure. Where outcome attribution is unavailable, preserve that uncertainty.

The highest-value addition is a small feedback procedure: observation → proposed change → expected business effect → result → next decision. Reuse the existing analytics/experimentation guidance. Do not impose the full stack on a business that has not justified it.

**3. High priority: the proposed AI probe does not yet define a valid measurement.**

Plan locations: lines 79, 82–83, 98, 111 and 125.

A fixed prompt sent to an unspecified model API is not evidence of what a buyer sees in a consumer product. The plan leaves model/version, search configuration, location, language, prompt selection and repetitions unspecified. Monthly runs over 12 weeks provide only a few observation windows; they do not by themselves distinguish sampling variation from a trend. OpenAI's API documentation explicitly exposes search configuration, optional search decisions, citation annotations and location controls. [Official API documentation](https://developers.openai.com/api/docs/guides/tools-web-search).

Inference: until the measurement surface is defined and checked, calling this a replacement for commercial visibility tools is premature. Likewise, a model mentioning a brand, citing its URL and recommending it are different outcomes. Model responses must not become customer-demand evidence merely because they are saved as `evidence.jsonl`.

Required revision:

- Label API probes as measurements of the configured API experience; keep consumer-product observations and AI Overview observations separate.
- Select prompts from relevant customer questions/search evidence; distinguish unbranded discovery from brand-seeded reputation checks.
- Record model, search/tool usage, locale, timestamp, prompt version and repeated observations within comparable windows. Preserve failures as unknown, not absent mentions.
- Distinguish correct-entity mentions, recommendations and supporting citations; retain the source answer so the agent can inspect why a result changed.
- Start with a narrow, relevant panel and expand only when its findings change a decision. Report panel coverage rather than implying market-wide visibility share.

The message-match proposal also needs a boundary: the described AI referrer grouping does not supply the visitor's conversation or recommendation. Compare observed probe contexts or legitimately supplied conversations with landing pages as a diagnostic; do not present them as the actual context of each AI-referred visit. Reuse the existing [campaign measurement contract](../.agents/skills/brand-website-designer-builder/references/campaign-tracking.md) for observable conversions and attribution limits.

**4. High priority: the recommended crawler split can undermine the visibility being optimized.**

Plan location: line 80, with the related owner choice at line 89.

`Google-Extended` is described as a training crawler to block while retaining retrieval access. Google's documentation says its control also covers grounding in Gemini Apps and Grounding with Google Search on Vertex AI. It is a product token, not a separate HTTP user agent. Google Search inclusion is a separate boundary. [Google crawler documentation](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers#google-extended).

Material consequence: the owner could choose a purported training-only restriction and unintentionally exclude specified grounding uses. User-agent log analysis also cannot observe a separate Google-Extended crawler that does not exist.

Required revision: describe each vendor control's actual training/search/grounding effect and implement the selected policy. Remove the claimed universal “mainstream” configuration. The current [SEO reference, line 9](../.agents/skills/brand-website-designer-builder/references/seo-performance.md) already correctly requires a vendor-specific decision.

**5. Medium priority: mandatory schema coverage would create false quality failures.**

Plan locations: lines 70, 133 and 136.

The proposed validator fails pages for absent Product/Offer/FAQ/Organization markup by page type. That makes markup presence an acceptance criterion without establishing platform eligibility or a useful outcome. Google deprecated HowTo rich results in 2023 and stopped FAQ rich results in May 2026. Its AI-feature guidance requires no special schema. These facts do not mean schema.org types are invalid or useless for every other consumer. [HowTo update](https://developers.google.com/search/blog/2023/08/howto-faq-changes), [FAQ update](https://developers.google.com/search/updates), [AI-feature guidance](https://developers.google.com/search/docs/appearance/ai-features).

Required revision: prioritize correctness of markup that is present, especially prices, availability and ratings. Require coverage only for a selected, supported feature or feed contract; otherwise report a scoped recommendation or not-applicable result. Do not add a general launch blocker for absent FAQ markup. Preserve the existing requirement that markup represents visible, supported facts.

**6. Medium priority: adding references and route keywords does not ensure the audit agent uses them.**

Plan locations: lines 129–144.

The plan links the new AEO/GEO references from `seo-performance.md`. However, the current [website skill, lines 14–16](../.agents/skills/brand-website-designer-builder/SKILL.md) directs repairs/audits to `maintenance.md`; SEO/performance is explicitly selected for new builds/releases. The [maintenance reference](../.agents/skills/brand-website-designer-builder/references/maintenance.md) does not direct an AEO/GEO audit to those new references. Marketing/social workflows would mainly acquire an owner-actions appendix rather than instructions for selecting and applying the new tactics.

Material consequence: an existing-site GEO audit—the intended use case—can follow the documented path without loading the new procedure. Broader strategy can continue unchanged while appending more tasks.

Required revision: add a short conditional load instruction to the actual audit/maintenance entry point. Give marketing/social workflows a selection rule and explicit handoff for a justified visibility task. Keep focused answers and content execution scoped. This is an instruction change, not a reason to build another orchestration layer.

**7. Medium priority: the owner-actions contract can turn optional ideas into recurring obligations.**

Plan locations: lines 36, 46, 60, 74 and 138–141.

“Every skill output that touches these layers” is broader than the later strategy/planning/audit convention. Pending/done also fails to distinguish an agreed action from an unselected suggestion. A proposed weekly posting cadence can therefore keep returning on resume despite never having been adopted.

Requiring an SME to recheck every extractable fact also fails to distinguish owner-only truth—prices, experience, guarantees—from facts the agent can verify against current authoritative sources or an already approved source record.

Required revision: include only decisions or actions relevant to the requested deliverable. Separate proposed, accepted, deferred and completed work using a small table if needed. Reuse approved factual inputs; ask the owner about unavailable firsthand facts, changed commercial commitments and actual decisions. Preserve publication authorization already given in the session. Do not append recurring programs to narrow copy work.

This preserves the existing [task-scope contract](../references/task-scope.md) and reduces owner workload without weakening factual checks.

**8. Medium priority: repository policy and platform restrictions are conflated.**

Plan locations: lines 32, 56 and 60–61.

The plan says autonomous community posting is prohibited and attributes a universal 90/10 rule to Reddit's Responsible Builder Policy. The retrieved policy does not establish that ratio. Reddit's own app guidance explicitly supports compliant, disclosed automation. That does not authorize promotional bots or any particular posting workflow. [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy), [Reddit app guidance](https://support.reddithelp.com/hc/en-us/articles/45376380316052-Apps-on-Reddit-and-how-to-get-a-label-for-your-app).

Required revision: describe human posting as the repository's selected operating policy where that is the intention. Check the platform, community and use case before claiming an external prohibition. Distinguish ownership of an authentic viewpoint from the mechanics of publishing an approved post. Keep the existing prohibition on unauthorized outreach/publishing. There is no recommendation here to launch automated community posting.

**Work worth retaining, with narrower scope**

| Addition | Material benefit | Condition |
| --- | --- | --- |
| Customer-question mapping and clearer answers | Improves page relevance and comprehension | Derive questions from actual audience evidence; avoid universal word-count prescriptions |
| Accurate, readable prices, terms and comparisons | Helps people and machines evaluate an offer | Use confirmed facts and applicable page types |
| Crawler and content-access diagnostics | Finds an actionable discovery obstruction | Apply the selected vendor-specific policy |
| Message-match and funnel review | Connects site iteration to customer outcomes | Separate observed context and conversions from inferred attribution |
| Own-brand/citation observation | Can reveal factual errors or missed relevant sources | Begin narrowly; preserve sampling and product-surface limits |
| Owner handoff | Makes missing inputs actionable | Include accepted work and genuine blockers, not every possible tactic |

**Defer or remove from the initial change**

Do not add a new visibility skill, signed community-style authorization machinery, MCP commerce scaffolding, discovery files or a schema launch-contract migration merely because they are available or described as cheap. The plan itself calls some of these speculative/conditional; keep them deferred until a selected integration needs them.

Also correct the implementation estimate: the inspected competitor-monitoring skill documents a watchlist/snapshot/diff procedure, but there is no `scripts/monitoring/` implementation in the inspected tree. Reusing its conventions is sensible; claiming reusable executable machinery and the cheapest implementation is not established. A read-only pilot should settle the useful output before a multi-provider build.

**Recommended revision order**

1. Correct source claims, crawler behavior and schema guidance; persist direct evidence links.
2. Reuse the existing bottleneck/channel-selection rules and connect the new references to the actual audit and strategy entry points.
3. Define a narrow observation-to-action report using available, authorized data. Include measurement limits and a business outcome/stop rule.
4. Automate the repeatedly useful parts. Expand providers or commerce integrations only after their outputs prove decision-relevant.

No architecture redesign or expanded coverage suite is proposed. This review does not establish live output improvement; that would require using the revised procedure on representative tasks. No project data, customer accounts or production configurations were inspected or changed.

**Source register**

All external sources below were retrieved on **2026-09-19**. Dates describe publication/update dates where established; otherwise these are living documents checked on the retrieval date. Only the claims discussed above were verified, not every number or platform assertion in the original plan.

- [Seer: single-client ChatGPT conversion case study](https://www.seerinteractive.com/insights/case-study-6-learnings-about-how-traffic-from-chatgpt-converts) — 2025-06-03.
- [Adobe: Q1 2026 AI traffic and US retail conversion](https://business.adobe.com/blog/ai-traffic-surge-retail-sites-not-machine-readable) — reports March/Q1 2026 observations.
- [Ahrefs: 75,000-brand correlation study](https://ahrefs.com/blog/ai-brand-visibility-correlations/) — 2025-12-12.
- [GEO: Generative Engine Optimization](https://arxiv.org/abs/2311.09735) — arXiv 2023; KDD 2024.
- [Ahrefs: schema and AI citations](https://ahrefs.com/blog/schema-ai-citations/) — May 2026.
- [Muck Rack: May 2026 AI citation study](https://muckrack.com/blog/what-is-ai-reading-may-2026) — May 2026.
- [Muck Rack/Generative Pulse: study announcement and earned-media definition](https://www.globenewswire.com/news-release/2026/05/07/3290268/0/en/generative-pulse-earned-media-consistently-drives-ai-citations-holding-at-84.html) — 2026-05-07; issuer press release.
- [OpenAI API web search](https://developers.openai.com/api/docs/guides/tools-web-search) — living documentation.
- [Google common crawlers / Google-Extended](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers#google-extended) — living documentation; also retrieved using Firecrawl.
- [Google HowTo/FAQ changes](https://developers.google.com/search/blog/2023/08/howto-faq-changes) — 2023-08-08; HowTo update 2023-09-14.
- [Google Search documentation updates](https://developers.google.com/search/updates) — FAQ deprecation entry 2026-05-08, effective 2026-05-07.
- [Google AI features and websites](https://developers.google.com/search/docs/appearance/ai-features) — living documentation.
- [Reddit Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy) — living policy.
- [Reddit app labeling and automation guidance](https://support.reddithelp.com/hc/en-us/articles/45376380316052-Apps-on-Reddit-and-how-to-get-a-label-for-your-app) — living guidance.
