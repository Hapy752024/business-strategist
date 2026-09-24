

# Naming and legal checks

Run when a name is needed or before logo/tagline approval. Outputs under `naming/`: `naming-brief.md`, `candidates.md`, `domain-checks.json`, `checks.md`. Checks are preliminary; a registrar, trademark office or counsel confirms.

1. Brief: positioning, audience languages, tone, associations to avoid, pronunciation, naming style and target jurisdictions/TLDs.
2. Candidates: 12–20 names across three naming strategies; screen meaning, spelling on hearing and category clichés.
3. Domain: `python3 scripts/brand/check_domain_rdap.py <name> --tlds <list> --out naming/domain-checks.json`; unknown means recheck manually and available still needs registrar confirmation.
4. Social handles: record availability for relevant platforms and the check date.
5. Trademark: search identical and confusingly similar marks in relevant classes on EUIPO, WIPO and USPTO; record query, classes, date and hits. A close hit stops approval until the founder decides. Search the chosen tagline and distinctive logo shape too.
6. Record the human vector-edit pass; an unedited AI raster is not the approved master.
7. Present the top three with all check results; the founder chooses. Secure domain and handles before announcement.
