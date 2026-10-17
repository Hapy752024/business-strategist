# Privacy design that helps customers finish their task

Apply to new websites and changes affecting forms, tracking, vendors or personal data. Use proportionate checks for other generated digital assets. This is an engineering and content baseline, not a certification or universal legal opinion. Establish applicable jurisdictions and actual processing; EU GDPR, national ePrivacy, UK rules and sector obligations are distinct. Refresh material legal assumptions before release. Continue ordinary design work with known facts; isolate unresolved legal decisions to the affected feature.

## Start with the data flow

Record controller/contact, audience jurisdictions, each field/event and purpose, lawful basis, recipients/processors and transfers, retention criterion, deletion owner and mechanism, and user rights route. Include hosting logs, email/CRM copies, anti-abuse tools, embeds and server-side forwarding. Do not invent the operator, vendor contracts, retention period or a legal basis to fill a template. No personal-data collection should go live while its necessary inputs remain unresolved.

For each field, explain why the present task needs it. Remove speculative qualification fields, defer later-stage details, distinguish required from optional, and avoid free-text invitations to submit sensitive information. Keep secrets and personal values out of URLs, analytics, replay and error telemetry. Choosing a smaller data flow is often the simplest UX improvement. These are implementation defaults; specific necessity must be assessed. [EDPB design guidance, final v2.0, 2020-10-20](https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf).

## Give useful information when it matters

Use a short, readable first layer with controller, purpose, rights and material or surprising consequences, with an obvious route to complete information. Surface it at collection or the relevant decision. Layering should reduce repetition without hiding required facts. A footer privacy link supports persistent access; whether it is sufficient for a particular interaction depends on collection, timing and context. Do not impose a universal sentence count, exact pixel placement or modal. [WP29 transparency guidance, revised 2018-04-11, paragraphs 35–37](https://www.edpb.europa.eu/system/files/documents/2023-09/wp260rev01_en.pdf).

Use plain, factual language. Describe what happens after submission and the actual reply channel. Avoid alarmist legal copy, generic compliance badges, unsupported “never shared” promises, and a full policy pasted beside every button. Equally, do not soften a consequential disclosure to improve conversion. Tailor the complete notice to the actual Article 13/14 information needs: purposes/bases, controller and relevant contacts, recipients/transfers, retention, rights and complaints, required fields/consequences, and relevant automated decisions or indirect collection. [EDPB rights guide](https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en).

## Separate notice, consent and marketing

A privacy notice informs; it is not permission for every use. Select and document the appropriate lawful basis for each purpose. Do not add a required “I consent to the privacy policy” box to routine enquiries by default. Contract/pre-contract necessity and legitimate interests each have conditions; neither is a blanket fallback. Where consent is the basis, specify the purpose, obtain a freely given affirmative choice and support withdrawal. [EDPB lawful processing guide](https://www.edpb.europa.eu/sme/be-compliant/process-personal-data-lawfully_en).

Keep requested replies or administrative updates separate from newsletters, promotions, partner lead sharing and later sales sequences. A contact submission does not establish permission for those additional uses. Assess message content, purpose, channel and national electronic-marketing rules; do not assume every “follow-up” is service or every requested reply needs a marketing checkbox. When marketing consent is required, make it optional, unselected and separate from submitting the enquiry. Do not silently enroll people after submission. [ICO Identify direct marketing, updated 2025-08-20; UK guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/direct-marketing-guidance/identify-direct-marketing/).

Apply [EU consent implementation](consent-eu.md) to cookies, device access and tracking. No consent-required technology means no automatic cookie-consent banner. This does not remove notice or other data-protection duties. Keep refusal, preferences and withdrawal usable when consent is required.

## Make promises operational

Choose retention by purpose and applicable obligations, not a universal number of months. Specify the trigger, period or criterion, exceptions, processor copies, mailboxes, backups and deletion responsibility. Verify that the implemented workflow actually follows the policy. A UI deletion, local test or vendor promise alone does not prove deletion across systems. Minimize any justified suppression record needed to respect objections. [EDPB design guidance, section 3.7](https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf).

## Review with realistic customer tasks

- Check controller and data-flow facts against the rendered notice and backend configuration; record unresolved facts explicitly.
- Complete an enquiry without optional marketing. Inspect submitted payload, destination, logs and confirmation; reject unrequested marketing enrollment.
- Test consent-required traffic before choice, after rejection, after acceptance and after withdrawal using [consent-eu.md](consent-eu.md). For sites without it, verify the inventory and actual absence of such traffic.
- Verify labels, linked instructions, focus, keyboard operation, zoom/mobile readability and understandable errors and success states. Do not communicate choice or failure through colour alone. Test notifications with assistive technology where available; automated accessibility checks are partial evidence. [W3C WAI form notifications](https://www.w3.org/WAI/tutorials/forms/notifications/).
- Review choice wording and visual prominence: no preselection, guilt, misleading urgency, hidden refusal or repeated nagging. These are project design defaults, not a claim that every layout has the same legal status.
- Trace a synthetic rights/deletion request through the actual approved workflow, including processors where in scope. Keep test data and evidence sanitized. Record operational checks that remain unverified.

Report observed behavior, legal assumptions and unresolved release dependencies separately. A build, checklist or screenshot never establishes universal compliance. Fresh source review and limitations: [research record](../../../../evals/website-maintenance/2026-10-17-privacy-design.md), checked 2026-10-17.
