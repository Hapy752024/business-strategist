# Customer-question tracking

Use optional `customer-questions.json` with `schemas/customer-questions.schema.json` and `fixtures/marketing/customer-questions/`. Customer rows bind normalized captures and accepted source reviews: exact passages, dates, segment applicability and buyer context remain separate from interpretation. Supplier and hypothesis rows cannot supply customer proof. Repeated episodes are not independent demand evidence.

Validate/render with `python3 scripts/marketing/customer_questions.py <artifact> --base <marketing-root> [--out <sanitized-table.md>]`. Bind the artifact and selected IDs in a content brief's optional `customer_questions` field; each selected target-customer question lists that brief ID in `linked_brief_ids`. Publishing/resuming the existing Marketing workstream rechecks source/review/artifact bytes, including source-only updates. Legacy briefs remain valid without question bindings.

For authorized first-party material, supply only a minimal sanitized extract and document `access_context`; private rows require `sanitized_extract:true`. This assertion is not authorization or privacy certification. Default rendering withholds private question/answer text. Do not ingest private archives or add connectors. Unknown answers/outcomes stay null. Optional outcome evidence binds question ID/current answer hash, date and limitations; helped/did_not_help/inconclusive observations do not imply causality.

The JSON and bound extract are internal artifacts and may contain authorized sanitized private text; sharing them requires a separate review. Only the default rendered table withholds private passage/answer text. Match a brief audience exactly to the reviewed segment; reconcile aliases through review before binding.
