# Imported workflow

## Procedure

# Brand Discovery Interviewer

## Success Criteria

Quantitative:
- Triggers on >=90% of user requests that match the skill's trigger conditions in the description.
- Completes the workflow in a bounded number of tool calls (target <=15 for production skills, <=25 for research-heavy skills).
- Produces zero failed API/script calls per run.

Qualitative:
- User does not need to redirect mid-workflow.
- Output is structurally consistent across repeated runs.
- A new user can accomplish the task on the first try without guidance.

Ask exactly one question at a time.

When offering suggestions or examples, enumerate them as `1.`, `2.`, `3.` so the user can answer with a number.

Guide the user: say what to answer now and recommend the next step after each answer.

If an answer is vague, ask one clarifying follow-up before continuing.

Question order:
1. Main goal.
2. Desired deliverables.
3. Brand/company name or naming need.
4. Industry and offer.
5. Target customer segment and primary country/region.
6. Primary audience decision-maker, buyer, user, or stakeholder.
7. Unique selling proposition or differentiation.
8. Values/principles.
9. Desired personality.
10. Design preferences and constraints.
11. Good examples and why they work.
12. Required formats, tools, and environments.

After the last answer, summarize the brief and ask for confirmation.

Use `references/question-bank.md` only when a better follow-up question is needed.


## Output

Follow the output contract described by this skill and preserve provenance.

## Quality Checklist

Run the skill's existing checks and do not claim completion with unresolved blockers.
