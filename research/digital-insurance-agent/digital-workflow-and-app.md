# Digital Workflow And App Roadmap

## 1. Product Principle

The workflow should not feel like a quote form. It should feel like:

> A structured decision conversation that teaches, asks, explains, and then routes the customer to a human review only when the data is ready.

The app should not be built first. Start with a web workflow and advisor operations. Build the app after there is retention demand.

## 2. Core Digital Workflow

### Step 1: Segment And Trigger

Ask:

- Preferred language: German, English, Mandarin.
- Current status: employee, self-employed, Beamter, student-to-employee, family, homeowner.
- Product interest: PKV/GKV, BU, life, critical illness, existing offer review.
- Trigger: salary threshold, broker offer, family planning, health history, premium increase, moving to Germany.

Output:

- Customer enters the right decision path.

### Step 2: Eligibility And Fit

For PKV:

- Income above JAEG?
- Self-employed?
- Beamter / Beihilfe?
- Family situation?
- Health status complexity?
- Time horizon in Germany?

For BU:

- Occupation.
- Income.
- Desired monthly BU pension.
- Health-history complexity.
- Prior therapy, chronic issues, medication, back/back pain.
- Existing offers.

Output:

- Fit score.
- "You are likely / maybe / not currently eligible."
- If not eligible, explain alternatives without pushing a sale.

### Step 3: Information Pills

Short, contextual learning units triggered by user answers.

Examples:

- If married or planning children: "PKV family cost scenario."
- If non-working spouse: "GKV family insurance vs PKV per-person premiums."
- If health-history complexity: "Why anonymous risk pre-inquiry matters."
- If income near threshold: "What happens if salary falls below JAEG."
- If foreign resident: "How long-term Germany plans affect PKV."
- If Mandarin selected: show German term + Mandarin explanation + English fallback.

Format:

- 30-90 second text/video modules.
- One concept per screen.
- Must end with a simple question or confirmation.

### Step 4: Upload And Data Capture

Allow:

- Existing PKV/BU offers.
- Broker presentations.
- Current policy PDFs.
- Doctor invoice / PKV reimbursement examples later.
- Employer benefits documents.

Extract:

- Insurer.
- Tariff.
- Premium.
- Deductible.
- Exclusions.
- Risk surcharges.
- Waiting periods.
- Benefit limits.
- Broker/advisor claims.

Early MVP can do this manually. Do not overbuild OCR before proving demand.

### Step 5: Scenario Builder

For PKV:

- Stay single.
- Have children.
- Non-working spouse.
- Income drop/job change.
- Self-employment.
- Leaving Germany.
- Retirement contribution assumptions.
- Premium increase sensitivity.

For BU:

- Full acceptance.
- Exclusion.
- Risk surcharge.
- Rejection.
- Alternative products.
- Self-insurance with savings.

Output:

- Scenario comparison, not a fake exact forecast.
- "Which assumption matters most" explanation.

### Step 6: Personalized Video

Use personalized videos as explanation, not as gimmick.

MVP:

- Advisor records a 3-5 minute Loom-style video after intake.
- Template:
  1. "Your situation."
  2. "Main decision."
  3. "Top 3 risks."
  4. "What I would clarify before signing."
  5. "What we will discuss on the call."

Later:

- Auto-generate video script from decision memo.
- Use human-reviewed narration.
- Offer Mandarin, German, English versions.

Do not use AI avatar/video for regulated advice until compliance and customer trust are tested. For early trust, a real advisor face is better.

### Step 7: Recommendation Memo

This is the core artifact.

Sections:

- Customer profile and assumptions.
- Products considered.
- Existing offer summary.
- Recommendation.
- Rejected alternatives and why.
- Trade-offs.
- Cost and risk notes.
- Health-underwriting notes.
- Questions for advisor call.
- Compensation disclosure.
- "What would make this recommendation change?"

The memo should be downloadable and available in all selected languages where possible.

### Step 8: Human-In-The-Loop Advisor Call

Call goal:

- Confirm facts.
- Correct misunderstandings.
- Review open risks.
- Explain recommendation.
- Decide whether to proceed, pause, or seek more data.

Call structure:

1. Confirm situation.
2. Review decision memo.
3. Discuss rejected options.
4. Review health/underwriting issues.
5. Explain next steps.
6. Confirm no pressure to sign.

### Step 9: Application Support

If customer proceeds:

- Prepare insurer application.
- Run anonymous risk pre-inquiry where needed.
- Track application status.
- Store documents.
- Schedule follow-up.

### Step 10: Post-Sale Advisor Team

Assign a small advisor pod:

- Primary advisor.
- Backup advisor.
- Claims/service specialist.

Customer promise:

> You do not restart from zero after signing. Your advisor team keeps your decision memo, contract history, and claim context.

## 3. App Feature Backlog

### MVP App / Portal Features

1. Policy vault.

- Upload all insurance PDFs.
- Tag by product and insurer.
- Store recommendation memo.
- Store advisor notes.

2. Contract overview.

- PKV, BU, term life, critical illness.
- bAV and employer benefits.
- Current monthly premium.
- Renewal/review dates.
- Important exclusions and deductibles.

3. Claims support.

- Upload doctor invoice.
- Track submitted / reimbursed / rejected.
- Checklist: what document is missing?
- Advisor escalation for delayed or disputed claims.

4. Employer benefits inventory.

- bAV contract overview.
- Group accident / group life / employer disability benefits.
- Vesting and job-change notes.
- "What happens if you change employer?"

5. Life-event prompts.

- Salary crosses JAEG.
- Marriage.
- Child.
- Mortgage.
- Self-employment.
- Job change.
- Leaving Germany.
- Premium increase.
- Health-history event.

6. Advisor message center.

- Ask a question.
- Share document.
- See response SLA.
- Book review call.

### High-Value Later Features

1. PKV invoice assistant.

- Scan invoice.
- Explain GOA/GOÄ basics in plain language.
- Flag missing justification for high multipliers.
- Track reimbursement.

2. BU claim preparation.

- Document checklist.
- Timeline.
- Advisor support.
- Claim status.

3. Scenario simulator.

- Compare GKV/PKV scenarios.
- Family planning.
- Retirement sensitivity.
- Income drop.
- Move abroad.

4. Annual coverage review.

- Changes since last year.
- Premium changes.
- Family/employment changes.
- Recommended actions.

5. Multilingual glossary.

- German insurance terms with Mandarin and English explanations.
- Contextual glossary inside every memo and screen.

6. Trusted-contact support.

- Allow spouse/partner to access selected policies.
- Useful for life insurance, claims, emergencies.

7. Tax-advisor export.

- Premium summary.
- bAV/Rürup/private pension documents.
- Annual export packet.

## 4. What Not To Build Early

Avoid early:

- Full native mobile app before conversion is proven.
- Automated "best tariff" engine.
- Claims automation without human support.
- AI-only advice.
- Too many insurance categories.
- Real-time insurer integrations unless a specific workflow demands them.

Build first:

- Web intake.
- Offer upload.
- Decision memo.
- Advisor review workflow.
- Manual personalized video.
- Portal-style document vault.

## 5. Advisor Operations

### Advisor Incentives

Advisors should be measured on:

- Recommendation memo quality.
- Customer clarity score.
- Compliance completeness.
- Response time.
- Retention/claims satisfaction.
- Low complaint rate.

Advisors should not be measured on:

- Product-specific commission.
- Pushing a particular insurer.
- Number of contracts signed regardless of fit.

### Advisor Pod Capacity

Early team:

- 1 licensed lead advisor.
- 1 Mandarin-speaking advisor or associate.
- 1 service/claims specialist.

Target load:

- 20-40 active advisory cases/month per pod during early manual phase.
- Keep claims/service queue visible before adding more acquisition.

### Service Promise

Initial SLA:

- New inquiry: response within 1 business day.
- Offer review: memo within 3-5 business days after complete documents.
- Claims/support question: response within 2 business days.
- Urgent claim issue: same/next business day triage.

## 6. Compliance And Trust Guardrails

Public product must include:

- Licensed entity and advisor status.
- Broker/agent/advisor role.
- Compensation disclosure.
- Privacy and data handling for health data.
- Disclaimer that public content is education, not individualized advice.
- Documentation of recommendation rationale.
- Consent before using customer examples.

Do not say:

- "Guaranteed best policy."
- "Completely conflict-free."
- "We give your commission back."
- "AI recommends the best insurance."

Better wording:

- "Product-specific sales bonuses are not part of advisor compensation."
- "Every recommendation includes rationale and rejected alternatives."
- "Compensation is disclosed before application."
- "Advisor review is required before submission."

## 7. MVP Build Sequence

### Phase 1: Concierge MVP

Tools:

- Landing page.
- Typeform/Tally.
- Secure upload.
- Calendly.
- Loom.
- Notion/CRM.
- PDF memo template.

Goal:

- Validate willingness to complete intake, upload offers, and take advisor call.

### Phase 2: Structured Web Workflow

Build:

- Account creation.
- Multilingual intake.
- Offer upload.
- Memo generation support.
- Advisor dashboard.
- Call notes.
- Document vault.

Goal:

- Reduce advisor prep time and increase consistency.

### Phase 3: Portal/App

Build:

- Policy overview.
- Claims tracking.
- bAV/employer benefits inventory.
- Life-event prompts.
- Advisor messaging.

Goal:

- Retention and referrals.

## 8. Success Criteria

Workflow is working if:

- 60%+ of qualified users complete intake after starting.
- 50%+ upload an existing offer or document.
- 80%+ say memo improved clarity.
- 25%+ proceed to advisor-reviewed application or paid review.
- Claims/service usage appears within 90 days of first policy customers.

App is worth building if:

- Customers ask for post-sale help unprompted.
- Claims questions recur.
- Customers have multiple policies or bAV confusion.
- Advisor team needs a central operating system to maintain service quality.
