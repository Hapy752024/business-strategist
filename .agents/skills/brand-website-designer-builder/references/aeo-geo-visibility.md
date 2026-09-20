# AEO/GEO visibility procedure

Apply for answer/generative-engine visibility audits and content work on existing or new sites, after the marketing bottleneck diagnosis justifies it (docs/digital-marketing-optimization-plan.md §0). Load from maintenance.md for existing-site audits. Eligibility work never guarantees citations; quote only the binding evidence table in docs/digital-marketing-optimization-plan.md §1.

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
