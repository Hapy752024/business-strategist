

# Naming and legal checks

Run when a name is needed or before logo/tagline approval. Outputs under `naming/`: `naming-brief.md`, `candidates.md`, `domain-checks.json`, `checks.md`. Checks are preliminary; a registrar, trademark office or counsel confirms.

1. Brief: positioning, audience languages, tone, associations to avoid, pronunciation, naming style and target jurisdictions/TLDs.
2. Candidates: 12–20 names across three naming strategies; screen meaning, spelling on hearing and category clichés.
3. Domain: `python3 scripts/brand/check_domain_rdap.py <name> --tlds <list> --out naming/domain-checks.json`; unknown means recheck manually and available still needs registrar confirmation.
4. Social handles: record availability for relevant platforms and the check date.
5. Trademark: search identical and confusingly similar marks in relevant classes on EUIPO, WIPO and USPTO; record query, classes, date and hits. A close hit stops approval until the founder decides. Search the chosen tagline and distinctive logo shape too.
6. Protection note (United States; checked 2026-09-24): In *Thaler v. Perlmutter*, the D.C. Circuit held that the autonomously generated image in that case lacked the human authorship required by the Copyright Act. The Copyright Office's 2025 AI report says copyright may cover sufficient human expressive contribution, including creative modifications or arrangement; prompts alone are not enough. The Supreme Court denied certiorari on 2026-03-02, which left the appellate judgment in place without a Supreme Court merits ruling. A vector-edit pass records human contribution but does not itself guarantee copyright. See the [D.C. Circuit opinion](https://media.cadc.uscourts.gov/opinions/docs/2025/03/23-5233.pdf), [Copyright Office AI report](https://www.copyright.gov/ai/), and [Supreme Court docket](https://www.supremecourt.gov/docket/docketfiles/html/public/25-449.html). Trademark protection is a separate question; run the similarity checks above and seek counsel for close conflicts.
7. Present the top three with all check results; the founder chooses. Secure domain and handles before announcement.
