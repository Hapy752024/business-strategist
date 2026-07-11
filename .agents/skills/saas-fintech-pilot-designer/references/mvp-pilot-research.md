# MVP, POC, And Pilot Research Notes

These notes summarize research used by `saas-fintech-pilot-designer`. Use them as working guidance, then verify current regulator-specific facts when a user names a country, state, regulator, or live-consumer pilot.

## Core Distinctions

- Problem interview: validates pain, urgency, current workaround, buyer, and trigger event. It should happen before a build when pain is weak or the customer segment is broad.
- Smoke test or fake-door: validates interest, click intent, signups, demo requests, or willingness to join a waitlist. It is not proof of retention or willingness to pay.
- Prototype: validates workflow, comprehension, trust, UX, and buyer reaction. It can be clickable, throwaway, or Wizard-of-Oz.
- Concierge MVP: manually delivers the promised outcome to learn value, cost-to-serve, and workflow before automation.
- Technical POC: validates feasibility, data availability, integrations, model performance, latency, security architecture, or other technical assumptions.
- Pilot: validates a limited real-world deployment with named stakeholders, scope, timeline, success metrics, and a conversion or stop decision.
- Paid pilot: adds evidence of budget, procurement seriousness, and willingness to pay. A token fee can qualify interest, but only if the pilot has explicit success and conversion criteria.
- Beta: hardens a product after the core value proposition and risk path are understood. It is not a substitute for discovery or pilot design.

Simon O'Regan's distinction is useful: the artifact should match what is being tested; POCs focus on feasibility, prototypes test experience, and pilots test more realistic use with stakeholders.

Source: https://www.simonoregan.com/essays/poc-prototype-mvp-pilot

## SaaS Pilot Practices

Strong B2B SaaS pilots usually include:

- A named account and narrow workflow.
- Champion, economic buyer, end users, technical owner, and procurement/security owner.
- A measurable business outcome, not "try the product".
- Entry criteria: pain confirmed, data available, sponsor committed, calendar agreed.
- Limited scope and explicit non-goals.
- 30 to 90 day timeline unless the workflow naturally has a longer cycle.
- Weekly cadence and named owners on both sides.
- Success, failure, and inconclusive thresholds.
- Conversion decision date and commercial path.

Heavybit's SaaS POC guidance emphasizes paid pilots, clear pilot goals, and maintaining commercial momentum so the conversion to a longer contract is not delayed by legal and security work discovered after the pilot.

Source: https://www.heavybit.com/library/article/saas-poc-paid-pilot-program

## Common SaaS Pilot Failure Modes

- The user is excited but the buyer is absent.
- The pilot is free, vague, and extends indefinitely.
- The customer requires custom features before any core value is proven.
- Security, legal, procurement, data access, or integration is discovered late.
- The founder measures activity instead of retained use or business outcome.
- A manual service is disguised as repeatable software without tracking cost-to-serve.
- The pilot succeeds politically but fails commercially because no conversion gate exists.

## Fintech And Insurtech Pilot Risk Ladder

Use a staged path from least risky to most risky:

1. Interviews and workflow mapping with no sensitive data.
2. Landing page, smoke test, or sales deck with no financial/insurance data collection.
3. Clickable prototype using fake personas and synthetic data.
4. Back-office concierge test using redacted examples.
5. Technical POC with synthetic or anonymized data.
6. Read-only customer data in a controlled environment after security and legal review.
7. Human-reviewed recommendations with disclaimers and partner oversight.
8. Live production data, customer-facing advice, eligibility, pricing, underwriting, claims, money movement, or coverage changes only after the compliance path is clear.
9. Regulator sandbox or licensed-partner trial where novel live-market testing is needed.

## Fintech And Insurtech Guardrails

For each test, identify whether the product touches:

- Money movement, payments, custody, or account access.
- Credit eligibility, lending, underwriting, pricing, collections, or adverse action.
- Insurance advice, broking, carrier activity, underwriting, policy comparison, claims, fraud, or cancellation.
- Investment advice, portfolio recommendations, financial planning, tax, or legal advice.
- KYC/AML, identity verification, fraud, sanctions, or transaction monitoring.
- Consumer disclosures, consent flows, complaints, appeals, or protected classes.
- Personal data, health data, financial data, insurance data, credit data, or employment data.

If yes, prefer synthetic data, read-only mode, human review, partner oversight, and explicit legal/compliance review before real consumer use.

## Official Regulatory And Data-Security References

FCA Regulatory Sandbox:

- The UK FCA regulatory sandbox supports firms that need to test innovative propositions in the market with real consumers. This is relevant when a fintech/insurtech test cannot be safely or legally validated with only synthetic data or internal users.
- Verify current eligibility, application windows, and jurisdiction before recommending it.

Source: https://www.fca.org.uk/firms/innovation/regulatory-sandbox

Bermuda Monetary Authority Innovative Insurance Sandbox:

- The BMA describes an insurance sandbox path for innovative insurance business models. Use it as evidence that insurance-specific controlled testing pathways exist, not as a substitute for jurisdiction-specific advice.

Source: https://www.bma.bm/innovative-insurance-sandbox

CFPB Disclosure Sandbox:

- The CFPB has used sandbox-style approaches for testing consumer disclosures. Treat U.S. consumer-finance disclosure experiments as jurisdiction- and program-specific; verify current CFPB policy before advising a founder to rely on it.

Source: https://www.consumerfinance.gov/about-us/blog/cfpb-office-innovation-proposes-disclosure-sandbox-companies-test-new-ways-inform-consumers/

FTC Protecting Personal Information:

- The FTC frames a sound data-security plan around knowing what personal information the business has, keeping only what is needed, protecting what is kept, disposing of what is no longer needed, and planning for incidents.
- Apply this directly to MVPs: collect less, retain less, restrict access, and define deletion and incident response before importing sensitive data.

Source: https://www.ftc.gov/business-guidance/resources/protecting-personal-information-guide-business

FTC Safeguards Rule:

- Covered financial institutions must maintain safeguards to protect customer information. A fintech founder should not assume that "we are only a startup" removes data-security obligations.
- Check whether the business is covered and whether customer information is involved.

Source: https://www.ftc.gov/business-guidance/resources/ftc-safeguards-rule-what-your-business-needs-know

NIST Privacy Framework:

- NIST's Privacy Framework is useful as a voluntary structure for managing privacy risk in products and pilots.
- Use it to think through governance, identification of data processing, controls, communication, and protection activities.

Source: https://www.nist.gov/privacy-framework

## Test Design Pattern

Use this pattern for every SaaS/fintech/insurtech MVP or pilot:

1. Name the riskiest assumption.
2. Select the smallest artifact that can test it.
3. Define who participates and what behavior proves learning.
4. Define the data boundary before implementation.
5. Define the compliance boundary before recruiting users.
6. Define success, failure, and inconclusive outcomes.
7. Set a short timeline and decision date.
8. Log evidence as observations, not founder interpretation.
9. Decide: continue, narrow, pivot, seek license/partner/sandbox, or stop.

## Evidence Log Template

| Date | Participant / Account | Segment | Assumption Tested | Test Type | Observed Behavior | Metric | Quote / Artifact | Risk Signal | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Pilot Scorecard Template

| Dimension | Threshold | Result | Evidence | Decision |
| --- | --- | --- | --- | --- |
| Activation | e.g. 80% of invited users complete first workflow |  |  |  |
| Repeated use | e.g. 3+ uses per active user in 30 days |  |  |  |
| Outcome | e.g. 30% less review time or 20% fewer errors |  |  |  |
| Buyer value | e.g. sponsor confirms budget owner and target price |  |  |  |
| Data feasibility | e.g. required fields available with acceptable quality |  |  |  |
| Security/compliance | e.g. no high-risk unresolved items |  |  |  |
| Cost to serve | e.g. manual ops under target minutes per account |  |  |  |
| Conversion | e.g. signed annual contract or paid extension |  |  |  |
