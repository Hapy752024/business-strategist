# Smoke test to interview

Default validation path for a founder without a customer panel: expose a specific promise to the intended segment, measure a behavioral step, then interview the people who took it. This designs a test brief; publishing, ad spend and outreach keep their own authorization.

## Sequence

1. Problem interviews or reviewed public evidence name the segment, trigger and pain in customer language (idea-grill, evidence-scout).
2. Message/offer smoke test: one page, one segment, one conversion action, two or three message variants that differ in pain frame, not wording.
3. Escalate commitment only after the page converts: priced fake door, deposit, pre-order, booked qualified call, or concierge sale.
4. Recruit interviewees from responders (screener → booked → attended → usable incident). Feed results to interview-bridge and back into the risk ranking.

## Conversion action and thresholds

Choose the action that matches the buying cycle: email capture is directional only; a booked qualified call, deposit or payment is behavioral evidence. Set thresholds before launch and label them as proposed learning budgets, not benchmarks. Published ranges checked 2026-09-24 vary widely; one practitioner rule treats 5%+ visitor-to-signup from cold traffic as a go signal, while others reject universal benchmarks. Compute the required sample from the threshold: distinguishing 2% from 5% conversion takes several hundred qualified visitors per variant. Record visitor source, variant and segment fit for every responder; unqualified signups do not count.

## Disclosure

A fake door must tell the responder within one step that the product is not yet available, what happens with their data, and offer the interview or waitlist honestly. No fake scarcity, fabricated testimonials, or payment details without the ability to refund.

## Budget approval

Advertising spend is not pre-authorized. Write `budget-approval.json` with the requested amount, currency, channel, duration and the decision it will inform; the founder fills `approved_by`/`approved_at`. Launch only when `status` is `approved`. Size the request from the threshold and an assumed CPC range retrieved for the channel at run time; state the CPC source and date.

## Responder to interview funnel

identified → exposed → responded → eligible → booked → attended → usable incident. Keep denominators per variant and channel. Apply `references/interview-recruitment.md` for screening and no-payment rules. Responders are volunteers, not customers; the interview verifies the incident, workaround and spend.

## Stop rules

Stop or change the test when the approved budget or window is spent; qualified traffic is below the minimum sample and the channel cannot supply more; responders are out of segment; or the segment consistently reports a different pain. A failed smoke test refutes the message or channel first; it does not by itself refute the need.
