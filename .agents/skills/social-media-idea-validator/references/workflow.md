# Social Media Idea Validator — Workflow

Detailed procedure for `social-media-idea-validator`. Keep `SKILL.md` lean; maintain this file.

## Principle

Most social/content ideas fail before production starts: the audience is not on the platform, nobody searches for the topic, the founder cannot sustain the format, or the channel cannot reach a conversion event within budget. Validation is cheaper than production. Run the gates in order and stop at the first hard KILL.

## Step 0 — Restate The Idea As A Testable Claim

One sentence: `For <specific audience>, <platform/format> about <promise> will lead to <conversion event> because <demand hypothesis>.`

Reject vague versions ("grow brand awareness on Instagram") until the user names audience, conversion event, and hypothesis. If the underlying business idea is itself unvalidated, route to `idea-grill` first — a content channel cannot outrun a weak offer.

## Gate 1 — Audience Presence

Question: does the target audience actually spend time on this platform, in a mindset that fits the offer?

Instruments:

- `python3 scripts/capability_lookup.py --question "where does <segment> discuss <topic> online" --compact` to route to the right provider.
- Serper/Brave search for community evidence: subreddits, Facebook groups, LinkedIn hashtags, YouTube channels, podcasts serving the segment; note sizes and activity.
- Reddit/forum reading (default provider) for the exact language the segment uses — needed later for hooks.
- For regulated local professions (insurance agents, loan officers), check where *peers* say business actually comes from before believing platform hype (see founder-playbooks: r/loanoriginators patterns).

KILL when: the segment demonstrably is not on the platform, or is there only in a mindset hostile to the offer (e.g. consumers shopping mortgages on TikTok for entertainment).

## Gate 2 — Demand Evidence

Question: is there observable demand for the promised content — searches, questions, engagement on adjacent content?

Instruments:

- Google Trends via SerpAPI and Serper keyword probes for the 5-10 core questions the idea would answer; record direction, not just level.
- YouTube/podcast/competitor content scan: do comparable formats get real engagement (comments from the target segment, not just views)?
- Question mining: Reddit, Quora, Facebook groups, "People Also Ask" for recurring pain questions the idea would answer.
- Pain-Point SEO check (see founder-playbooks): for search-driven ideas, prefer bottom-funnel high-intent topics (category, comparison/alternatives, jobs-to-be-done) over high-volume top-funnel topics.

KILL when: no question demand and no working comparable format after an honest search. Mark `[DATA UNAVAILABLE]` per instrument that could not be checked.

## Gate 3 — Founder-Format Fit

Question: can this specific founder/team produce this format natively, credibly, and weekly for 6 months?

Check: on-camera comfort vs writing vs audio; domain credibility; time budget per week; editing capability; language. Practitioners warn that social "can become a whole job in itself" — a format the founder hates will be abandoned by week 6. Prefer the format that reuses existing work (answer the questions clients already ask).

## Gate 4 — Differentiation / White Space

Question: what is the angle incumbents are NOT covering?

Instruments: competitor content audit via Firecrawl/Brave (top 5-10 competing channels/blogs for the segment): what formats, what questions ignored, what quality bar? Policygenius won because incumbents bought ads and left organic content open (see founder-playbooks). A copycat idea in a crowded format needs a distinctive asset: proprietary data, a niche slice, a stronger point of view, or a better format.

KILL when: the idea is a generic copy of what bigger players already do better, with no niche or asset difference.

## Gate 5 — Channel Economics

Question: can this channel plausibly reach the conversion event within the user's budget and timeline?

Check: the full path from content to conversion event (newsletter signup, call booked, quote requested, trial). Count the steps and the drop-offs. Local professional services (brokers, loan officers) usually convert through calls and face-to-face — social then plays an assist role (credibility, realtor/partner engagement, retargeting pool), which changes the verdict shape: GO-as-assist vs GO-as-primary. Define the conversion event and how it will be measured before any production.

## Gate 6 — Sustainability

Question: does the idea have >= 20 durable content items, or does it exhaust itself by week 8?

Check: list the first 20 titles/questions now. If the list dies at 6, the idea is a series, not a channel — PIVOT to a broader promise or fold it into an existing channel as a campaign.

## Verdicts

- **GO:** all gates pass with evidence; define the 4-week pilot below.
- **GO-as-assist:** channel cannot be the primary conversion driver but supports one (common for brokers/loan officers); scope expectations accordingly.
- **PIVOT:** demand exists but gate 1, 3, 4, or 6 fails; state exactly what to change (platform, format, niche, promise) and re-check the failed gate only.
- **KILL:** no demand evidence, or the channel cannot reach any conversion event; say so plainly and name what would have to be true to revisit.

## The One-Week Low-Cost Test (Mandatory For GO)

Smallest spend that would change the verdict:

1. 3-5 pieces in the chosen format answering the highest-intent questions found in Gate 2.
2. One clear CTA to the conversion event, tracked (UTM, booking link, dedicated phone line or email).
3. Distribution: post natively + share in 2-3 communities from Gate 1 (no spam; follow community norms).
4. Optional: small paid boost (< budget cap) only if organic signal is unreadable.
5. Stop rule: define it now — e.g. "if 0 qualified conversations after 5 pieces and 2 community posts, kill or pivot."

Record results in the topic workspace; a GO verdict without a scheduled test is incomplete.

## Output Contract

- Idea restatement (one testable sentence).
- Gate table: gate, question, evidence found, source, date, pass/fail.
- Verdict + confidence (high/medium/low) + what would change it.
- The one-week test + stop rule.
- Source list with dates; `[DATA UNAVAILABLE]` marks per unchecked instrument.

## Quality Checklist

- [ ] Idea restated as one testable claim (audience, platform, format, promise, conversion event)
- [ ] All six gates evaluated in order, or stopped early at a documented hard KILL
- [ ] Every GO verdict cites at least one demand signal and one audience-presence signal with source and date
- [ ] Practitioner patterns from `founder-playbooks.md` applied (named in the verdict reasoning)
- [ ] GO-as-assist used when the channel cannot be the primary conversion driver (brokers, loan officers, local services)
- [ ] One-week test and stop rule defined; no GO verdict without them
- [ ] `[DATA UNAVAILABLE]` used for unchecked instruments; no memory-filled gaps
- [ ] Verdict states what would change it
