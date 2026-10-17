# Website privacy and proportionate customer experience

Research date: 2026-10-17. Scope: shared website skill guidance; no project site changes, production assessment, deployment or customer contact. Fresh retrieval used official regulator and standards sources. Prior repository consent guidance supplied engineering context, not current legal evidence.

## Findings and implementation decisions

Layered transparency is explicitly supported by regulator guidance. The practical decision is to communicate the key facts at collection and make complete information easy to reach, rather than duplicate a long policy everywhere. No source establishes one compulsory pixel location or sentence count for every site. See source 1, paragraphs 35–37.

Consent is one possible lawful basis, not a universal checkbox for all forms. Model purposes separately and assess the applicable basis before collecting information. Source 3 explains the bases and their conditions. An enquiry reply must not silently become a marketing subscription. Source 5 distinguishes service and marketing communications in the UK; other countries need their own electronic-marketing assessment.

Consent-required tracking should be denied until permission; this is distinct from independently lawful service processing. Source 4 is the current consolidated French recommendation, including a December 2025 amendment on cross-device consent. It supports understandable purposes and meaningful choices; national exemptions are not universal. Existing cookie technical tests remain useful, with a new no-consent-required branch.

Data minimization and purpose-specific retention belong in implementation, not just copy. Source 2 supports limiting collected data, enforcing deletion policies and checking backups/logs. We did not adopt a generic retention duration or claim to have verified any website's deletion system.

Accessibility is part of a usable privacy journey. Source 6 supports clear actionable errors, associated field messages and perceivable success feedback. The checklist extends this into keyboard, mobile and zoom reviews as engineering practice; these do not constitute legal certification.

The resulting implementation reference is [privacy-design.md](../../.agents/skills/brand-website-designer-builder/references/privacy-design.md), complemented by the amended [consent-eu.md](../../.agents/skills/brand-website-designer-builder/references/consent-eu.md). Recommended skill entrypoint: require privacy-design.md for new builds/releases and changes to forms, tracking, vendors or personal data. Quality review should compare copy, actual data flows and operational evidence, not count disclosure words or demand extra banners.

## Source register

All sources accessed 2026-10-17. Dates below describe the document, not the date of fresh research. Regulator guidance is interpretative; the W3C tutorial is implementation guidance. None establishes worldwide compliance.

1. [WP29 Guidelines on transparency, WP260 rev.01, hosted by EDPB](https://www.edpb.europa.eu/system/files/documents/2023-09/wp260rev01_en.pdf). Adopted 2017-11-29; revised/adopted 2018-04-11. Full document retrieved; paragraphs 35–37 reviewed for layering and first-layer information. The initial search-result PDF URL failed; the official landing-page download resolved it.
2. [EDPB Guidelines 4/2019 on Article 25](https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf). Final version 2.0, adopted 2020-10-20, distinct from the 2019 consultation version. Retrieved; sections 3.5 and 3.7 reviewed for minimization and retention/deletion.
3. [EDPB SME guide: Process personal data lawfully](https://www.edpb.europa.eu/sme/be-compliant/process-personal-data-lawfully_en), and [Respect individuals' rights](https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en). Live regulator guides retrieved; exact publication/update dates not established. Used for lawful bases, notice and rights, not as legislation.
4. [CNIL consolidated cookie recommendation](https://cnil.fr/sites/default/files/2026-01/recommandation_cookies_consolidee.pdf). Published 2026-01-16, consolidating deliberations 2020-092 (2020-09-17) and 2025-131 (2025-12-18). Retrieved. [CNIL cookie law guidance](https://cnil.fr/fr/cookies-et-autres-traceurs/que-dit-la-loi) independently retrieved in search results for consent exceptions; exact page update date not established. French scope.
5. [ICO: Identify direct marketing](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/direct-marketing-guidance/identify-direct-marketing/). Retrieved full page; latest update displayed 2025-08-20, reflecting the Data Use and Access Act definition change. UK scope. Service messages exclude promotional additions; context and purpose matter.
6. [W3C WAI: User Notification in Forms Tutorial](https://www.w3.org/WAI/tutorials/forms/notifications/). Retrieved full page; exact update date not established. Accessibility implementation guidance, not proof of compliance with a jurisdiction's accessibility law.

## Retrieval limitations and confidence

Firecrawl CLI status reported authenticated but negative remaining credits (-451 / 1,000). Fresh searches and page retrievals used the available web provider instead; no top-up or account changes. EUR-Lex GDPR HTML/PDF and ePrivacy consolidated-text retrieval returned robot-verification pages. Consequently this report does not claim direct inspection of those statutory texts in this run; it relies on the retrieved official regulator guidance for the scoped decisions. The failed direct-text checks and source dates remain visible for future legal refresh.

This is a focused EU/French and UK privacy-design baseline with accessibility implementation guidance. It is not an exhaustive audit of national law, consumer law, AI disclosure, sector rules or all launch requirements. It cannot establish a particular controller's lawful basis, contracts, transfers, retention or production behavior without project facts. Those missing facts should constrain affected features, not trigger unnecessary consent controls or invented compliance claims.
