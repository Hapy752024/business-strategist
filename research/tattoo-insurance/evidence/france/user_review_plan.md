# User Review Plan

- Topic: TattooInsurance: risks and worries before getting a tattoo
- Segment under test: Adults in France considering or recently getting a tattoo

## Founder Checkpoints

Interaction rule: ask the founder exactly one question at a time. Do not bundle multiple questions into one message.

1. First ask: `Which evidence item below feels most like real buyer pain to you?`
2. After the answer, ask: `Which single assumption would most change your decision if false?`
3. After the answer, ask: `Should the next research focus on interviews, narrower segment evidence, or competitor flow teardown?`
4. Define the pass/fail threshold only after the user has answered the prior questions.

## Quality Flags To Discuss

- Only 2 direct user-pain record(s) found; treat demand evidence as thin.
- Google Trends signals are very low for the tested phrases.
- youtube API worked but produced zero relevant records.
- firecrawl API worked but produced zero relevant records.
- brave_search API worked but produced zero relevant records.

## Top User-Pain Items For Human Review

1. [reddit/pain/medium] Local OC companies hiring remote or remote/WFH as a disability accommodation \* I’ve included a photo so you can see I’m just a normal clean cut person, I don’t have any face tattoos or anything like that which could dissuade employers. Looking for LOCAL companies hiring remote/WFH or have remote/WFH as a disability accommodation. Hi everyone. I have a disability and I have been trying to get full time salaried work for SIX YEARS. I have some passive income which is how I made it this far but it (https://www.reddit.com/r/occlassified/comments/1tzrtvs/local_oc_companies_hiring_remote_or_remotewfh_as/)
2. [reddit/competitor_gap/medium] Your Ultimate Guide to Scalp Micropigmentation Perth If you’ve heard the term ‘scalp micropigmentation’ but aren’t quite sure what it is, you’re not alone. Think of it as a highly advanced, specialised cosmetic treatment that creates the illusion of real hair follicles on the scalp. For anyone in Perth looking for a real solution to hair loss, SMP offers a way to either replicate the look of a sharp, freshly shaved buzz cut or to add the appearance of thickness to thinning hair. It’s an art form (https://www.reddit.com/r/u_transformationperth/comments/1rf1asd/your_ultimate_guide_to_scalp_micropigmentation/)

## Decision Questions To Turn Into Interviews

1. Your Ultimate Guide to Scalp Micropigmentation Perth If you’ve heard the term ‘scalp micropigmentation’ but aren’t quite sure what it is, you’re not alone. Think of it as a highly advanced, specialised cosmetic treatment that creates the illusion of real hair follicles on the scalp. For anyone in Perth looking for a real solution to hair loss, SMP offers a way to either replicate the look of a sharp, freshly shaved buzz cut or to add the appearance of thickness to thinning hair. It’s an art form (https://www.reddit.com/r/u_transformationperth/comments/1rf1asd/your_ultimate_guide_to_scalp_micropigmentation/)

## Suggested Interview Prompts

- Tell me about the last time you considered PKV, BU, or changing an insurance advisor.
- What triggered the decision and what did you do first?
- Which sources or people did you trust, and which did you avoid?
- What felt risky, confusing, or too time-consuming?
- Did you compare portals, brokers, fee-based advisors, employer benefits, or do nothing?
- What would have made you comfortable completing 80% of the process self-service?
- At what point would you still want a human advisor, and what would that person need to prove?
- What would make you pay, switch broker mandate, or upload existing contracts into an app?

## User Decision Required

Before drawing a business-viability conclusion, ask the user to choose one next action:

- Recommended if public evidence is mostly weak: `Interview` - recruit 8-12 people matching the tightest segment and run the prompts above.
- `Narrow Segment`: pick one trigger event and rerun evidence collection with narrower keywords.
- `Competitor Deep Dive`: inspect product flows and pricing for the top 3 direct competitors.
- `Stop`: evidence is too weak or the segment is not reachable enough.
