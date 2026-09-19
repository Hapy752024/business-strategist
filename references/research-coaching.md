# Research coaching and applicable order

Read for chosen-idea validation, a resumed strategic research project, or a change to its target/solution. Focused factual answers and fixed execution retain `task-scope.md` boundaries.

## Coach before committing

Reuse the conversation and current intake. Persist the founder's answers in `market_research/manifest.json.coaching`: `known_answers` entries contain `field`, `value`, `provenance` (`user_confirmed`, `assumption`, `evidence`) and optional `source`; `unresolved_inputs` lists remaining gaps; `pending_question` contains one question or an empty string. Optional `decision_impact` explains which decision depends on the answer; `updated_at` dates the update. Keep questions/answers in the existing intake narrative as needed, not another current summary.

Ask the single decision-changing question early, wait for its answer before deciding that branch, and update known answers instead of asking them again. Explain a concrete tension or counter-hypothesis, then help the founder make the next choice. Do not turn coaching into a questionnaire or a long report with a token closing question. A declared zero network is a constraint to solve, not a request for warm introductions. Researchable hypotheses may remain assumptions; never require the founder to invent customer facts.

Preserve the user's business model and transaction journey while refining the segment. An adjacent model with different payment timing, buyer, job or cash cycle is a labelled comparator, not silent replacement of the target. Before its evidence changes the recommendation, ask the decision-changing scope question and retain the original hypothesis. After a correction, replace the pending question with the latest critical clarification; move earlier unanswered questions to unresolved_inputs. Do not treat a related industry's pain as proof for the selected customer.

While a material founder choice is pending, continue independent, authorized desk research with its assumptions labelled; keep the choice unresolved and recommendations conditional. Do not treat silence, elapsed time, file creation, source retrieval or an agent's agreement as owner approval. Before committing to a segment/country/solution, reconcile the answer with contrary evidence. Sending invitations, spending, publishing and operating a pilot retain their explicit authorization boundaries.

## Apply or reuse the right elements

| Work | Required order / checkpoint |
|---|---|
| Broad market discovery | Research first, then user candidate choice; do not force idea-grill before a candidate exists. |
| Chosen idea validation | idea-grill establishes researchable segment, job, geography and hypothesis; segment and journey precede pain assessment. Collect and semantically review relevant sources before treating them as evidence. |
| Customer/competitor interpretation | After identifying relevant entities, apply `customer-voice.md` through evidence-scout before segment/journey/pain and risk synthesis. Separate actual customer inputs from supplier copy; apply service-customer-perspective-challenger and competitive-landscape-builder where buyer trust/choice or alternatives matter. Reuse reviewed evidence and record applicability and omissions in intake/README. Parallel independent source reads are fine. |
| Risk and interview recruitment | opportunity-risk-designer and interview-bridge can work provisionally with weak/mixed evidence before pain validation. Source gaps become risks. Recruitment is a learning step, not first_customers or a demand pass. |
| Strategic recommendation / GTM / pilot | Review passed intake, segment, journey, pain and opportunity_risk checkpoints first. Apply/reuse operator playbooks when the archetype is researchable. Full strategy routes expose missing stages and block advancement; repair the first unmet prerequisite. |

For the requested scope, record each applicable skill as applied, reused (artifact/date/scope rationale), pending (specific gap) or not applicable (reason) in the current intake or README. This is an audit of coverage, not a claim a skill executed merely because an artifact exists. Stages pass only through the existing stage updater after review; neither filenames nor prose claims set stage status. Never mark intake completed with unresolved decision-changing founder choices. A provisional risk memo may be useful while its overall stage remains in progress.

The router enforces configured full-strategy prerequisites and the existing pain gate. Focused source repairs, interview recruitment and provisional risk planning are available independently; do not relabel a full launch plan as focused to bypass prerequisites. Explicit user gate overrides use the existing auditable mechanism. Reuse an existing passed checkpoint only after checking its artifact, scope and current constraints; stale evidence requires repair. This contract does not guarantee that every LLM or direct file operation obeys the workflow.

## Narrow the research after discovery

Use broad discovery only while the target is unknown. Record a provisional target hypothesis (business model, geography, role, trigger and job) before sentiment/pain validation. Pass its identity as --customer-segment and short source-language audience terms as --segment-keywords to collect.py. Validation queries retain those audience terms; the full segment prose remains metadata. Search subsegments separately and preserve hypothesis IDs. Broad industry sentiment is contextual, not target-customer evidence.

Collection always sets segment_relation=unresolved: a matched keyword does not establish who the author is. In the digest-bound source review classify each source as target, adjacent or unresolved and explain the actual business-model/journey fit. Only accepted firsthand target-customer records support target pain probes; adjacent voices remain labelled comparators, unknown membership remains unresolved. A source about invoice-based services cannot validate a pay-at-purchase retailer merely because both mention payments. If narrow retrieval is empty, record a coverage gap and adjust discovery or ask for a scope choice; never silently broaden the target to fill the quota.
