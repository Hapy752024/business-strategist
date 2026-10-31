# Pilot regulatory guardrails (fintech, insurtech, sensitive data)

Read with [pilot mode](pilot.md) whenever a test touches regulated activity or sensitive data. Working guidance, not legal advice: verify current regulator-specific facts when the user names a country, state, regulator or live-consumer pilot, and flag where licensed counsel, compliance review, a licensed partner or a regulator sandbox may be required.

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

Start with the least regulated and least sensitive test that still teaches:

- Use synthetic, mock, redacted, or anonymized data before production data.
- Use read-only data before write access, money movement, eligibility changes, policy changes, claims actions, or customer-facing recommendations.
- Keep humans in the loop for regulated or high-impact decisions.
- Avoid giving financial, credit, investment, insurance, tax, legal, eligibility, or claims advice unless the team has the required licenses, partner oversight, and review.
- Identify whether the company acts as software vendor, data processor, lead generator, broker, agent, carrier, lender, payment processor, advisor, model provider, or decisioning system.
- Document data collection, retention, access, disposal, vendor exposure, audit logs, incident response, and customer-facing disclosures.
- Check for bias, protected-class impacts, explainability, complaint handling, and human appeal paths where eligibility, pricing, underwriting, fraud, claims, or credit are involved.
- Consider a licensed partner, regulator sandbox, or no-action/sandbox-style path when testing live consumers or novel regulated activity.

Never recommend live production testing with consumer funds, coverage, claims, credit, underwriting, or advice if the legal/compliance path is unknown. Propose a safer staged alternative.

## Exposure checklist

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
