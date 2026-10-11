# Institutional, company-register and university sources

Added 2026-10-11. Choose sources by the research decision and target geography. Presence in the capability catalog is not proof of authenticated access or complete coverage.

## Direct institutional adapters

`python3 scripts/market_research/institutional_sources.py --help` supports ECB, FRED, BIS, World Bank and Companies House. Each explicit fresh `--out` directory contains `capture.json`, pending `research-facts.jsonl` and a summary. Existing `research_facts.py` review and publication-claim binding apply unchanged. No project is inspected or selected automatically.

Use provider metadata to discover the dataset, series dimensions and units before retrieving data. Use `--discover` with an explicit dataset/series ID to retrieve ECB/BIS definitions, FRED series metadata or World Bank indicator metadata. Metadata captures contain no statistical observations. Unknown units remain unknown. SDMX captures preserve returned attributes and observation flags. FRED retains vintage dates; World Bank and company search preserve bounded-page coverage. Statistical zero, missing observation and inaccessible data remain distinct.

Examples (dataset/series IDs below are probe examples, not defaults for a business case):

```bash
python3 scripts/market_research/institutional_sources.py --provider ecb --dataset EXR --series M.USD.EUR.SP00.A --limit 2 --out /tmp/ecb-example
python3 scripts/market_research/institutional_sources.py --provider bis --dataset WS_CBPOL --series M.CH --limit 2 --out /tmp/bis-example
python3 scripts/market_research/institutional_sources.py --provider fred --series FEDFUNDS --limit 2 --out /tmp/fred-example
python3 scripts/market_research/institutional_sources.py --provider world_bank --country CHE --dataset SP.POP.TOTL --start 2024 --end 2024 --unit persons --population 'Total population' --out /tmp/world-bank-example
python3 scripts/market_research/institutional_sources.py --provider companies_house --query 'repair' --limit 5 --max-pages 2 --country 'United Kingdom' --out /tmp/companies-house-example
```

SDMX `--limit` means last observations **per matched series**, not a market-wide row count. Use narrow series keys. Retained bodies are bounded at 2 MB; oversized responses require a narrower query. Paging is bounded by `--max-pages`; a cap remains a coverage limitation.

Credentials: `FRED_API_KEY` and `COMPANIES_HOUSE_API_KEY`, loaded by the existing secret loader. ECB, BIS and World Bank statistical queries require no key. Do not print credentials or store authenticated request headers; source URLs omit credential parameters.

Run isolated live checks with `python3 scripts/validate_apis/validate_institutional_sources.py --provider <name> --out <directory>`. These probes do not publish facts as reviewed research.

## Regulators and surveys

- ECB/BIS/FRED/World Bank: macroeconomic, lending and financing context; never customer demand proof.
- Federal Reserve Board: public surveys such as the Survey of Consumer Finances; retain survey weights, variable definitions and population coverage.
- EBA: public dashboards and report annexes. EU-wide transparency data stopped updating from June 2025 and must be labelled historical.
- EIOPA: insurance/pensions statistics and reports; distinguish aggregates from individual undertakings.
- ESMA: public authorised-entity/fund/instrument registers and documented downloads; apply each register's definitions.

The last four currently use existing official-site search, original-document extraction or downloads; dedicated API integrations are not claimed.

## Company registers

Use BRIS for EU/EEA cross-country company search and national registers for original details: UK Companies House, France Sirene, Germany Handelsregister and Switzerland Zefix. US incorporation research uses relevant state registers; SEC EDGAR supplies filings for SEC filers and is not an all-business register. Public browsing, free documents, bulk downloads and APIs have different availability and permissions. Do not assume a public portal grants unrestricted automated bulk access.

Companies House has the adapter above. `scripts/market_research/registry_sources.py` provides bounded France government company-directory and Swiss Zefix/LINDAS queries, SEC submissions by CIK, and ingestion of original CSV/JSON exports from other registers. Germany, BRIS and US state portals retain their own public-download/manual-access constraints. SEC requires a descriptive `SEC_USER_AGENT` with a contact email (or existing `CROSSREF_MAILTO`), not an API key. Match official legal identifiers across observations and distinguish legal entities, establishments and operating businesses. Existence, active registration, purchases, retention and profitability support different claims.

## University research

Use OpenAlex and Crossref for discovery, then retrieve original accessible research. Complement them with RePEc/EconPapers, EconStor, CORE repository discovery and GESIS datasets. Search relevant university repositories and department/centre working-paper series when topic coverage is weak. Do not assume commissioned or proprietary market research is public or indexed.

OpenAlex discovery stores metadata/access links. `scripts/market_research/fetch_research_document.py --openalex-work W... --out <fresh-directory>` retrieves available original GROBID XML with the existing OpenAlex key; live download and extraction were verified. The same command supports original public URLs or local files in PDF, XML, HTML, XLSX, CSV and text formats. Original bytes and hashes are retained; extracted passages remain pending review. Limits mark partial extraction; scanned PDFs requiring OCR remain explicit gaps. CORE's public discovery route needs no new credential; an optional dedicated CORE API requires its own key/access check and is not yet implemented.

For each study retain version, original URL, date, geography, population, methods, sample, uncertainty and applicability. Link duplicate versions by DOI/other stable identifiers rather than count each discovery route as an independent study.

## Agent access and readiness

The capability catalog records source purpose, geography, access method, credentials, limitations and collection commands. Default readiness receipts live in `.research-infra/api-validation/`, outside case/project folders. Provider doctor consumes current receipts; stale, failed and missing-credential states remain distinct. Run the registered API validators to refresh readiness. A successful access probe never marks research or demand as reviewed.
