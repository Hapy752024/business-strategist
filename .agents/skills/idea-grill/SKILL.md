---
name: idea-grill
description: Pressure-test a chosen business idea's segment, buyer, painful job, workarounds, and risks. Use when a founder wants to validate or challenge a specific customer/problem hypothesis.
---

# Idea Grill

**Core validation sequence for a founder-chosen idea.**
1. `idea-grill` clarifies the idea, target segment, core hypothesis, alternatives, workaround, urgency, and riskiest assumption.
2. `evidence-scout` validates API access and collects source-grounded evidence, including its topic-led and entity-led customer-voice frames.
3. `service-customer-perspective-challenger` constructs evidence-grounded buying contexts.
4. `competitive-landscape-builder` separates same-market competitors, similar companies, and capability references, then analyzes offers, prices, social usage, and positioning.
5. `opportunity-risk-designer` ranks risks and designs low-cost tests. Only the competitive-market lane may support competitive whitespace claims.

When the idea is clear enough to identify industry, business model and target customer, run `business-archetype-playbook-researcher` before strategic or launch recommendations (trigger and scope in its SKILL.md).
Venture-scale and VC-signal checks follow `opportunity-risk-designer`'s standing rule.

**Preserve the selected outcome.**
Validate/challenge the founder's stated idea, or explain a customer segment's pain points about a topic, as the user chose.
For substantive chosen-idea validation, include a targeted international commercial-precedent pass or explain its inapplicability; narrow factual and pure customer-problem questions remain proportionate.
Similar companies, including companies in other countries, can support scoped purchase, repeat-value and economics findings;
do not redirect the task into finding businesses to import or copy.
Read repo-root `references/opportunity-research-approaches.md` for substantive work that benefits from distinct evidence approaches.

**Strategic-positioning intake.**
Before material opportunity ranking, apply repo-root `references/strategic-positioning.md`:
reuse supplied founder context, ask only decision-changing gaps, and compare viable alternatives with comparable initial evidence coverage.
Narrow factual and execution requests bypass this intake.
Founder constraints and preferences are inputs, not market evidence.

**Research coaching.**
For chosen-idea and strategic continuation work, follow repo-root `references/research-coaching.md`:
persist known answers, ask one decision-changing question early, apply or explicitly reuse the required skill elements in order, and retain unresolved choices while independent desk work proceeds.
Interview/GTM/risk planning must apply repo-root `references/interview-recruitment.md` and provide researched, idea-specific routes to the first interviewees, including zero-network access.
Recruitment planning is allowed before the pain gate; launches remain gated.

When contributing to a registered Business case, keep source-grounded findings in your normal artifact and pass material conclusions or answered founder questions to the case-insights owner under repo-root `references/case-insights.md` before the case task closes.
Use this skill to validate or challenge the founder’s idea by testing its customer and problem assumptions.
For a topic without a chosen idea, route to market-problem-discovery.

**Pain-first back-track.** When the founder arrives with a solution, do not pressure-test the solution first. Back-track explicitly: pin the customer segment (`market_research/customer_segments/`), the customer journey for the topic (`market_research/customer_journey/`), and the pain points along that journey (`market_research/pain_points/`) — then validate those pains with web-searched evidence (collection runs land in `market_research/pain_points/runs/`). Only after the pain picture is on record do you pressure-test whether the proposed solution is the right answer to it. Solution-first grilling without the segment/journey/pain foundation is out of scope for this skill.

## Success Criteria
- **Quantitative:** triggers on >=90% of validation-mode queries; captures all 8 minimum inputs in <=15 questions; produces a copy-pasteable evidence-scout command on every completion.
- **Qualitative:** the output hypothesis is specific enough to generate search terms; segment is narrow enough to find and interview this week; solution language is stripped from search targets.

## Workflow

1. Read `references/workflow.md` completely.
2. For solution-first requests, back-track to segment → journey → pains before anything else (see above).
3. Ask one focused question at a time only for the remaining minimum inputs.
4. Write or update project-workspace intake artifacts under `market_research/` (segments, journey, pains) and `strategy/intake/`.
5. Separate evidence, assumptions, counter-hypotheses, and unknowns.
6. If the founder targets venture scale, needs VC financing, or asks whether investors are active in the category, assess investor-topic activity separately under repo-root `references/vc-investment-signals.md`. Keep it distinct from pain validation and market demand.
7. Stop before customer-evidence collection when the segment or painful job is not researchable.

## Output

Open every output with a `## Strongest reason this fails` section tied to a cited claim, an `{{assumption.<id>}}` or a named unknown with its test; never open with what is promising, and hold correct findings under pushback (repo-root `references/research-coaching.md`, truthful stance). Produce a core hypothesis, assumptions, counter-hypotheses, customer-language search terms, riskiest assumption, and next evidence command.

Also read when the stage needs it (referenced by the workflow):
- `.agents/skills/evidence-scout/references/pain-query-calibration.md`
- `references/customer-voice.md`
- `references/research-query-calibration.md`
- `references/voc-research-method.md`
