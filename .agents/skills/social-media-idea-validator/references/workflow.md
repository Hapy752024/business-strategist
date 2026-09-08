# Social Media Idea Validator — Workflow

Detailed procedure for `social-media-idea-validator`. Keep `SKILL.md` lean; maintain this file.

**Cross-skill rules:** apply the sequencing rule, weak-evidence list, channel jobs, and loop gates from `references/evidence-registry.md` at repo root. In particular: views, likes, followers, and waitlist numbers found during Gate 1–2 are weak evidence until tied to retained behavior, and any "viral loop" idea must satisfy the registry's loop gates (value before invitation, relevant recipient, measurable steps, retained economics after rewards and abuse).

## Principle

Most social/content ideas fail before production starts: the audience is not on the platform, nobody searches for the topic, the founder cannot sustain the format, or the channel cannot reach a conversion event within budget. Validation is cheaper than production. Run the gates in order and stop at the first hard KILL.

## Step 0 — Restate The Idea As A Testable Claim And Context

One sentence: `For <specific audience>, <platform/format> about <promise> will lead to <conversion event> because <demand hypothesis>.`

Reject vague versions ("grow brand awareness on Instagram") until the user names audience, conversion event, and hypothesis. If the underlying business idea is itself unvalidated, route to `idea-grill` first — a content channel cannot outrun a weak offer.

Reuse supplied founder context before testing a channel: desired operating role, credible voice/capability, time, cash, downside, buying-cycle deadline, and channel constraints. Ask one focused question only when a missing item would change the proposed test. Mark a hard constraint separately from a preference or assumption; do not research it as a market fact.

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

If no question demand or working comparable format is found, return INSUFFICIENT EVIDENCE and describe checked coverage and the cheapest way to resolve it. A failed or empty retrieval cannot establish rejection. Mark `[DATA UNAVAILABLE]` per instrument that could not be checked. Reject only when relevant observed behaviour or a demonstrated constraint supports rejection.

## Gate 3 — Founder-Format Fit

Question: can this specific founder/team produce this format natively, credibly, and for long enough to learn within the buying cycle?

Check: on-camera comfort vs writing vs audio; domain credibility; time budget per week; editing capability; language. Practitioners warn that social "can become a whole job in itself" — a format the founder hates will be abandoned by week 6. Prefer the format that reuses existing work (answer the questions clients already ask).

## Gate 4 — Economic Entry And Customer Relationship

Question: why would a suitable person notice, return to, trust, and eventually choose an unknown entrant?

Audit competing channels/blogs for customer questions, formats, quality bar, discovery routes and the relationship they create. Evaluate three separate layers: (1) discovery—how a relevant person encounters the entrant; (2) relationship—why they return, ask substantive questions or voluntarily follow up; (3) business—how this becomes a qualified enquiry, purchase and retained contribution. Returning engagement is a proxy, not a trust score; views, likes and followers are not demand.

An unserved topic is one possible entry mechanism, not a requirement. Existing providers prove supply, not saturation; no visible provider proves neither demand nor opportunity. A crowded space can be viable if a specific audience, credible voice, better customer experience, access route, proof or bundle gives people a reason to choose. Several modest advantages may jointly suffice.

KILL when: evidence shows the target does not want this promise from this entrant and no bounded change to audience, promise, format or route is plausible. Do not KILL because competitor coverage is unknown or because the channel is not novel.

## Gate 5 — Route Economics And Learning Window

Question: can this route reach enough suitable people and learn fast enough within the user's budget, capacity and buying cycle?

Check the full path from discovery to repeat engagement, conversion event (newsletter signup, call booked, quote requested, trial), purchase and subsequent value. Count steps, likely drop-offs, production, response/moderation, sales and delivery time—not only media spend. Separate organic, paid and borrowed reach; a paid boost cannot prove organic feasibility. Backsolve required qualified prospects from explicit economic ranges. Classify social as primary acquisition or assist from the observed discovery path; a later human call does not erase social's acquisition role. Self-reported discovery still does not establish incremental CAC.

Predeclare distinct deadlines for access, relationship learning and commercial outcome. Low relevant exposure is an access result; relevant exposure with repeated qualified rejection is different evidence. Do not use a universal number of posts or one-week KILL rule.

## Gate 6 — Sustainability

Question: can the promise sustain the amount of useful content and response required by its intended role?

Check a realistic first set of topics/questions and the ongoing response burden. A finite list may be a useful campaign rather than a channel. Test a broader relevant editorial promise only when an ongoing relationship is needed; do not create a community or permanent channel by default.

## Verdicts

- **GO:** enough evidence supports a bounded pilot; define its duration from the uncertainty, buying cycle and runway. GO authorizes a test, not a scale commitment.
- **INSUFFICIENT EVIDENCE:** coverage or relevant exposure is inadequate; name the unresolved assumption and bounded next investigation. This is not KILL.
- **GO-as-assist:** channel cannot be the primary conversion driver but supports one (common for brokers/loan officers); scope expectations accordingly.
- **PIVOT:** demand exists but gate 1, 3, 4, or 6 fails; state exactly what to change (platform, format, niche, promise) and re-check the failed gate only.
- **KILL:** observed rejection or demonstrated access/economic incompatibility makes the proposed route infeasible within constraints; name what would have to change to revisit.

## The Bounded Low-Cost Test (Mandatory For GO)

Smallest spend that would change the verdict:

1. A small initial set of pieces in the chosen format answering the highest-intent questions found in Gate 2; size it to the audience access mechanism and buying cycle.
2. One clear CTA to the conversion event, tracked (UTM, booking link, dedicated phone line or email).
3. Distribution: post natively + share in 2-3 communities from Gate 1 (no spam; follow community norms).
4. Optional: separately authorized paid test within the budget cap if it answers a distinct exposure or creative question. It cannot pass an organic-access test.
5. Stop rule: define separate thresholds for relevant exposure, substantive repeat engagement and qualified commercial response, calibrated to the buying cycle. State whether failure means stop, change the route, or change the promise.

Record results in the topic workspace; a GO verdict without a scheduled test is incomplete.

## Output Contract

- Idea restatement (one testable sentence).
- Gate table: gate, question, evidence found, source, date, pass/fail/unknown.
- Verdict + confidence (high/medium/low) + what would change it.
- A bounded test with separate access, relationship and commercial thresholds.
- Source list with dates; `[DATA UNAVAILABLE]` marks per unchecked instrument.

## Quality Checklist

- [ ] Idea restated as one testable claim (audience, platform, format, promise, conversion event)
- [ ] All six gates evaluated in order, or stopped early at a documented hard KILL
- [ ] Every GO verdict cites at least one demand signal and one audience-presence signal with source and date
- [ ] Practitioner patterns from `founder-playbooks.md` applied (named in the verdict reasoning)
- [ ] GO-as-assist used when the channel cannot be the primary conversion driver (brokers, loan officers, local services)
- [ ] A bounded test has separate access, relationship and commercial thresholds; no GO verdict without them
- [ ] `[DATA UNAVAILABLE]` used for unchecked instruments; no memory-filled gaps
- [ ] Verdict states what would change it
