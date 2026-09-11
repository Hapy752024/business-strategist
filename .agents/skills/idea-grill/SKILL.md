---
name: idea-grill
description: Pressure-test a specific business idea, segment, buyer, painful job, workarounds, and risks. Use before validating or building a chosen candidate idea.
---

# Idea Grill

Use this skill to turn a founder-chosen candidate into a researchable customer/problem thesis.

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
6. Stop before collection when the segment or painful job is not researchable.

## Output

Produce a core hypothesis, assumptions, counter-hypotheses, customer-language search terms, riskiest assumption, and next evidence command.
