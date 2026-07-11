---
name: saas-fintech-pilot-designer
description: Design rigorous tests, MVPs, POCs, paid pilots, sandbox trials, and decision gates for SaaS, fintech, and insurtech products. Use when the user asks how to validate a SaaS/fintech/insurtech idea, run a pilot with a customer, design an MVP, choose between prototype/POC/pilot/beta, handle regulated pilots, use synthetic or real data safely, structure pilot success criteria, or avoid enterprise pilots that never convert.
---

# SaaS Fintech Pilot Designer Workflow

Use this skill to turn an early SaaS, fintech, or insurtech idea into a concrete learning plan: which test to run, with whom, under what constraints, using which data, with what success threshold, and what decision follows.

This is a business and product-validation skill, not legal advice. For fintech, insurtech, credit, payments, banking, insurance, KYC/AML, underwriting, claims, financial advice, insurance advice, consumer disclosures, or use of sensitive personal data, flag where licensed counsel, compliance review, a licensed partner, or a regulator sandbox may be required.

## Reference

Before creating a substantial MVP or pilot plan, read:

- `references/mvp-pilot-research.md`

If the user asks about current rules, a named jurisdiction, a named regulator, live consumer testing, or production financial/insurance data, search the web and cite official sources before making claims.

## Stance

Be concrete and skeptical. A pilot is not progress unless it creates evidence that changes the build, sell, partner, regulate, or stop decision.

Separate:

- Evidence: observed workflow pain, signed pilot, payment, real usage, retained usage, measurable time/risk/cost reduction, procurement progress.
- Assumptions: buyer urgency, willingness to pay, data access, integration feasibility, compliance path, channel repeatability.
- Test artifact: interview, smoke test, prototype, concierge MVP, Wizard-of-Oz MVP, POC, pilot, paid pilot, sandbox trial, beta.
- Guardrails: data minimization, synthetic/anonymized data, role restrictions, disclaimers, human review, security, auditability, compliance review.
- Decision gate: continue, narrow, change buyer, change workflow, seek partner/license/sandbox, or stop.

## Minimum Inputs

Try to capture:

- Product idea and category: SaaS, fintech, insurtech, or adjacent.
- Customer segment, user, champion, buyer, and blocker.
- Problem, trigger event, current workaround, and cost of the problem.
- Jurisdiction and target market.
- Whether the test touches real consumers, regulated decisions, money movement, credit, insurance, investment, advice, claims, underwriting, identity, KYC/AML, or personal data.
- Data needed: synthetic, anonymized, customer-provided sample, production read-only, production write, or third-party API.
- Current stage: idea, interviews, prototype, technical POC, first pilot, paid pilot, beta, revenue.
- Target learning deadline and available founder resources.

If one missing fact would change the legality or safety of the test, ask one focused question before producing the plan. Otherwise state assumptions and proceed.

## Test Type Selection

Choose the lowest-risk artifact that can answer the riskiest assumption.

- Problem interview: use when pain, urgency, buyer, or current workaround is unproven.
- Smoke test or fake-door: use when demand or conversion is uncertain; use ethical disclosure and avoid collecting unnecessary sensitive data.
- Clickable prototype: use when workflow, trust, UX, buyer comprehension, or procurement reaction is uncertain.
- Concierge MVP: use when the value can be delivered manually before automation; use strong data controls.
- Wizard-of-Oz MVP: use when the user experience can be realistic while humans handle the backend; disclose where regulated judgment, advice, or material decisions are involved.
- Technical POC: use when feasibility, data availability, integration, model accuracy, or latency is the main risk.
- Paid pilot: use when buyer urgency, procurement, implementation, usage, and willingness to pay must be tested with a named customer.
- Regulatory sandbox or controlled market trial: use when real consumers, regulated activity, or novel compliance questions must be tested under official or partner-supervised constraints.
- Beta: use only after core value, buyer, and compliance path are clear enough to harden the product with broader usage.

Do not call a prototype a pilot. Do not call a consulting engagement a SaaS pilot unless the conversion path is explicit.

## SaaS Pilot Design

For B2B SaaS, design the pilot around a named business outcome:

- Named account, champion, economic buyer, end users, technical owner, procurement/security owner.
- Entry criteria: pain confirmed, workflow identified, data available, sponsor committed, timeline agreed.
- Scope: one segment, one workflow, one measurable outcome, limited integrations, clear non-goals.
- Duration: usually 30 to 90 days, unless the workflow has a naturally longer cycle.
- Success metrics: activation, repeated use, retained use, outcome improvement, time saved, risk reduced, revenue impact, support load, expansion signal.
- Commercial structure: paid pilot or contract with termination option when possible; avoid indefinite free pilots.
- Conversion gate: exact condition for annual/monthly contract, expansion, narrow retry, or stop.

Watch for failure patterns: no economic buyer, vague success criteria, custom-feature dependency, no data access, champion-only enthusiasm, security/procurement discovered too late, manual service hidden as software, and pilots that extend without a conversion decision.

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

## Procedure

1. State the startup thesis and the specific riskiest assumption.
2. Classify the test domain: SaaS, fintech, insurtech, or mixed.
3. Identify the regulatory/data sensitivity level: low, medium, high, or blocked until review.
4. Choose the test type and explain why it is the smallest sufficient artifact.
5. Define the participant profile and recruiting path.
6. Define scope, non-goals, timeline, owner, and operating cadence.
7. Define data needed and data that must not be collected.
8. Define security, privacy, compliance, and human-review guardrails.
9. Define success, failure, and inconclusive thresholds.
10. Draft the pilot agreement outline.
11. Create a week-by-week execution plan.
12. Create an evidence log and final decision gate.

## Pilot Agreement Outline

Include only business-facing structure unless the user asks for contract language:

- Parties, sponsor, champion, and users.
- Problem and pilot objective.
- Duration, milestones, and cadence.
- Scope, integrations, environments, and excluded use cases.
- Data sources, data rights, retention, deletion, confidentiality, and security obligations.
- Human review, disclaimers, regulated-use restrictions, and customer-facing disclosure responsibilities.
- Fees, expenses, and conversion credit if paid.
- Support model and incident escalation.
- Success criteria and decision date.
- Conversion, extension, termination, and post-pilot data handling.

## Output

For a full request, produce:

- One-sentence test thesis.
- Riskiest assumptions ranked.
- Recommended test type.
- Why not heavier or lighter alternatives.
- Customer/participant profile.
- MVP or pilot scope and non-goals.
- Data plan and compliance guardrails.
- Success metrics, failure metrics, and stop/scale thresholds.
- Pilot agreement outline.
- Week-by-week plan.
- Evidence log template.
- Decision gate.
- Common ways this pilot could mislead the founder.

For a quick answer, produce:

- Recommended test.
- 5 to 7 concrete steps.
- Key metrics.
- Biggest risk.
- Next action this week.

## Quality Checklist

Before finalizing, check:

- The test answers one riskiest assumption, not every possible question.
- The target customer can be recruited this week.
- SaaS pilots have a buyer, champion, users, data owner, and conversion gate.
- Fintech/insurtech tests minimize regulated activity and sensitive data.
- Synthetic/anonymized/read-only data is preferred before live production data.
- Success metrics include behavior and business outcome, not only opinions.
- Stop conditions are explicit.
- The plan does not hide a custom services project inside a pretend SaaS pilot.
- Legal/compliance uncertainty is flagged without pretending to give legal advice.
- The next 7 days are executable without building a full product.

## Suggested First Question

If needed, ask:

`Will the test touch real customer financial/insurance data, money movement, eligibility, underwriting, claims, or advice, and in which jurisdiction?`
