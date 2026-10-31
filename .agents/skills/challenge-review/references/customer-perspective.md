# Customer-perspective mode (route `service-customer-perspective-challenger`)

A complete protocol of its own; do not mix in panel roles or tournament drafting.

Success: simulated customer voice is labeled as hypothesis, not research evidence; regional context is applied when geography is specified; each challenge is tied to evidence or a named assumption.

Read in order: this file; the relevant geography in [regional lenses](regional-lenses.md) (sources: [customer evidence base](customer-evidence-base.md)); [decision lenses](decision-lenses.md) to construct decision contexts, not stereotypes. Write the review with `assets/customer-perspective-review-template.md`.

## Purpose and boundary

Use this mode as a hypothesis generator and adversarial review after the segment and problem are researchable. It does not replace interviews, behavioral evidence, or `evidence-scout`. It differs from a demographic persona generator: it models a buying decision around a trigger, job, stakes, alternatives, risks, and proof threshold.

## Required inputs

Recover what is known before asking questions:

- service, outcome, scope, price/model, geography, language, and delivery channel;
- target user, buyer, payer, trigger event, urgency, current workaround, and alternatives;
- proof, credentials, guarantees, privacy/data use, cancellation/refund, and support;
- current stage and evidence from interviews, sales, usage, reviews, complaints, or experiments.

If decisive inputs are absent, state assumptions and continue with a provisional review. Ask only when different answers would reverse the recommendation.

## Procedure

1. **Classify the service decision.** Record purchase frequency, price, consequence of failure, reversibility, personal-data sensitivity, expertise asymmetry, urgency, and whether quality is observable before purchase.
2. **Build the evidence ledger.** Tag each relevant claim as observed fact, sourced market pattern, inference, or untested hypothesis. Attach geography, service category, date, and limitation.
3. **Construct decision contexts.** Create one primary likely buyer and one skeptical near-fit buyer. Define trigger, job, desired outcome, stakes, budget, time pressure, alternatives, trust threshold, decision participants, and disqualifiers. Add a vulnerable/high-risk context when the service concerns money, health, insurance, immigration, housing, or legal consequences.
4. **Enter the customer role.** Write a concise, explicitly synthetic first-person reaction: what I notice, what I do not understand, what feels risky, proof I seek, what I compare, and what would make me act or leave. Do not invent a biography, quote, or prior experience as fact.
5. **Run the challenge.** Test problem recognition, outcome clarity, credible differentiation, total effort/cost, trust and redress, purchase friction, delivery risk, cancellation, and post-purchase reassurance.
6. **Repackage the service.** Specify trigger-led name, promised outcome, bounded scope, deliverables, timeline, customer obligations, exclusions, total price, risk reversal, support, privacy, cancellation, and next step. Prefer concrete proof over adjectives.
7. **Rewrite the market entry.** Produce a message hierarchy and recommend discovery, evaluation, conversion, and referral channels that fit the decision journey. Keep jurisdiction-specific legal claims and disclosures explicit.
8. **Design behavioral tests.** Test the most consequential assumptions with observed behavior: qualified reply, booked call, deposit, paid diagnostic, document upload, completed checkout, retained usage, referral, cancellation, or complaint. Set pass, revise, and stop thresholds before launch.

## Handoff

When evaluating customer priorities or a service-positioning conflict, load repo-root `references/strategic-positioning.md`. Within each buying situation distinguish minimum requirements, deciding preferences, and acceptable sacrifices, with evidence/inference labels. Repackage within the selected position; surface material changes to audience, promise, price, or exclusions for an explicit strategy decision. Keep this mode scoped to consumer-service buying contexts.

- Run after `idea-grill` and initial `evidence-scout` collection when possible.
- Send evidence gaps back to `evidence-scout`; simulated reactions are not evidence records.
- Use `opportunity-risk-designer` to rank failed assumptions and tests.
- Use `marketing` (strategy mode) after this review for marketing expression, funnel, and campaigns; GTM owns unresolved business-position selection.
- Use `archetype-gtm-strategist` when stage, first-customer motion, partnership, or international rollout is the primary question.

## Output standard

Use the bundled template. Lead with the customer verdict and decisive barrier. Give concrete copy/package changes, not generic advice. Preserve disagreement between decision contexts instead of averaging it away.

For a registered Business case, pass material buyer-context findings and unresolved objections to the case-insights owner under repo-root `references/case-insights.md`; retain source attribution in your normal artifact.

## Evidence and Persona Rules

### Evidence hierarchy

Prefer, in order:

1. the idea's own paid behavior, retention, cancellations, complaints, lost deals, and interviews;
2. direct statements and observed behavior from a tightly matched segment;
3. regulator, government, standards, and peer-reviewed evidence for the same jurisdiction and service category;
4. reputable industry surveys with disclosed sample and method;
5. broad regional surveys and operator anecdotes as context only.

Record source date, sample/geography, service category, finding, and limitation. A broad consumer average cannot predict an individual buyer.

### Anti-stereotype rule

Do not infer personality from nationality. “German customers are risk-averse” is not an acceptable premise. Convert regional evidence into testable design hypotheses, such as: “For this German high-data service, test whether a plain-language data-use summary and data-minimizing intake improve qualified completion.”

Segment first by trigger, job, consequence of failure, purchase frequency, budget, expertise, channel, and decision role. Use age, nationality, gender, or income only when evidence shows they materially change this service decision and the use is lawful and relevant.

### Synthetic customer voice rule

Label first-person passages `Simulated customer voice — hypothesis`. Never fabricate quotes, emotions, personal history, or consensus. Phrase uncertainty honestly: “I may ask…”, “This buyer could interpret…”, or “Test whether…”.

### Service-specific risk

Services are often intangible, variable, co-produced, and hard to evaluate before purchase. Examine these risk dimensions separately:

- performance and outcome uncertainty;
- financial loss and hidden total cost;
- time/effort and coordination burden;
- privacy, security, and data reuse;
- social, emotional, health, legal, immigration, or regulatory consequence;
- dependence on one adviser or provider;
- redress, refund, cancellation, complaint, and continuity if delivery fails.

### Review and marketing integrity

Reviews are useful quality cues but can be biased, unrepresentative, fake, incentivized, suppressed, or stale. Require authenticity controls, material-connection disclosures, recency/category context, and access to critical reviews. Do not manufacture testimonials or suppress honest negative feedback.

Show total price, recurring terms, cancellation, exclusions, and material limitations before commitment. Treat guarantees as operational promises with conditions and capacity, not copy decoration.

### Evidence ledger

For every material recommendation record:

| Claim | Type | Geography/category | Source or observation | Confidence | Limitation | Next test |
|---|---|---|---|---|---|---|

Types are `fact`, `market pattern`, `inference`, and `hypothesis`. Do not silently upgrade one type into another.

## Challenge Protocol

Score each dimension `0 missing`, `1 weak`, `2 plausible`, or `3 evidenced`. A high prose score without behavioral evidence is still provisional.

### Idea challenge

1. **Trigger and job:** Is there a recognizable moment that makes action likely now?
2. **Pain and alternative:** Is the current workaround costly or risky enough to change?
3. **Outcome:** Can the buyer describe the result without repeating the provider's features?
4. **Fit boundary:** Who should not buy, and can they identify that early?
5. **Differentiation:** Is the advantage meaningful in the buyer's comparison set and hard to dismiss? Does it map to a top-3 customer priority? Which observed customer decision criterion does it improve, and what source supports that criterion for this segment?

### Customer decision criteria challenge

Treat function, reliability, convenience, price, trust, status, risk and switching effort as candidate lenses. Do not prescribe a universal order or percentage of decisions for B2B, B2C, SMEs or industry maturity. Determine the relevant criteria from recent purchases, exclusions, trade-offs and alternatives for this segment. A low price can itself be decisive; mature industries do not universally ignore features.

For each material criterion record the supporting customer incident/source, competing explanation and what would refute it. Ask what eliminated options last time, who influenced the choice and which compromise was actually accepted. Keep user/buyer/payer differences explicit. If evidence is missing, produce a testable hierarchy hypothesis and a non-leading interview probe, not a claimed customer priority. Founder or agent preferences are not customer evidence.

### Trust and purchase challenge

6. **Competence proof:** Are credentials, process, sample output, cases, and reviews relevant and verifiable?
7. **Motive and independence:** Are incentives, commissions, sponsorships, and partner relationships disclosed?
8. **Total commitment:** Are total price, customer work, timeline, recurring terms, and opportunity cost visible?
9. **Control and redress:** Can the customer pause, correct, cancel, complain, obtain a refund where applicable, and reach a person?
10. **Data and safety:** Is collection minimal, purpose clear, security credible, and sensitive-service escalation safe?

### Package challenge

Rewrite the package as:

`For [trigger-defined segment], [package name] delivers [bounded outcome] within [time/process], including [deliverables] for [total price/range]. You provide [inputs]. It excludes [limits]. Risk is reduced by [staged commitment/guarantee/redress]. Next step: [specific low-friction action].`

Reject vague packages such as “premium personalized support.” Name the work, result, boundary, and commitment. For high-variance services, use a paid diagnostic or scoped first stage before promising a fixed result.

### Message challenge

Build the hierarchy:

1. trigger and desired progress;
2. concrete outcome and fit boundary;
3. how delivery works;
4. proof matched to service/category;
5. total commitment and risk reducers;
6. one next action.

Remove unsupported superlatives, fake scarcity, pressure, hidden fees, forced consent, and claims that confuse activity with outcome. Translate internal process features into customer-relevant evidence without overstating certainty.

### Customer-role cross-examination

For each decision context answer in first person, labeled as synthetic:

- Why now, and why not keep my current workaround?
- What do I believe this actually includes?
- What could go wrong, and who absorbs that cost?
- What information or data must I surrender before receiving value?
- Why should I trust the provider, reviews, comparison, or partner?
- What will I compare and what makes me reject the offer?
- What happens after payment, when delivery varies, or when I want to leave?
- What single change would most increase my willingness to take the next step?
- What do I actually prioritize when choosing between options? (Rank: price, function, reliability, convenience, trust, brand, habit, novelty.)
- A year from now, three competitors offer the same thing. Why would I still choose you?
- What would a competitor need to offer to make me switch? Is that threshold realistic?

Then exit the role and translate each objection into a package, proof, process, message, targeting, or disqualification change.

### Behavioral validation

Choose the smallest test that exposes commitment:

- five problem interviews plus evidence of current workaround;
- message/offer test with qualified replies rather than impressions;
- paid diagnostic or refundable deposit;
- sample-deliverable test with a real case;
- price/scope choice using realistic packages;
- mock checkout/intake measuring abandonment by step;
- concierge delivery measuring effort, completion, complaint, and referral;
- cancellation and refund usability test;
- lost-deal and post-purchase interviews.

Set thresholds before the run. Track segment, trigger, geography, source, package, objection, conversion, delivery cost, completion, satisfaction, cancellation, complaint, retention/repeat, and referral. Do not scale because a synthetic persona liked the idea.
