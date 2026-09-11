# Approved sources per field

Ranked per field. Prefer the first you can actually read; record what you
used in `source_label`. Dated secondary sources beat undated official pages.

## population

1. ISTAT official (istat.it — "Popolazione residente" per comune, or the
   annual comuni CSV releases).
2. tuttitalia.it comune page (mirrors ISTAT, shows reference date) — cite as
   "Tuttitalia (ISTAT data)".
Record the ISTAT reference date in `--ref-date`.

## buy (OMI €/m²) — KEY FIELD, needs `--confirm-url`

1. Agenzia delle Entrate OMI — Osservatorio del Mercato Immobiliare,
   "Quotazioni immobiliari" per comune/zona (residenziale, compravendite).
   Cite the semester (e.g. `2025-S2`).
2. Confirmation: a dated secondary that quotes OMI (idealista/immobiliare
   market pages, il Sole 24 Ore OMI write-ups) OR a second OMI zone reading.
Two zones of the same comune (centro vs periferia) are not independent
sources; a different publisher reading the same OMI data is acceptable as
confirmation but note it in the label.

## rent — manual, dated

1. idealista.it / immobiliare.it "prezzi e andamenti" rent pages per comune
   (dated month shown on page).
2. A small sample of current listings (3+) with retrieval date in the label.
Never scrape at scale (ToS); small manual reads are fine.

## tax7 — KEY FIELD, needs `--confirm-url`, official only

The rule (art. 24-ter TUIR, as amended): eligible comuni are those in
Abruzzo, Basilicata, Calabria, Campania, Molise, Puglia, Sardegna, Sicilia
with population below the statutory cap (raised from 20,000 to 30,000 by the
2026 budget law — Law 34/2026; verify the current figure before applying),
plus comuni on the SISMA 2009/2016 earthquake-zone lists (Lazio, Umbria,
Marche, Abruzzo).

1. Agenzia delle Entrate / MEF published eligible-comuni lists or norm text
   (esteri.it / agenziaentrate.gov.it / normattiva.it).
2. Confirmation: the comune's ISTAT population vs the cap (population source
   above) — the law text plus the population figure together are two
   independent legs.
A relocation agency's blog post is NEVER sufficient, even as confirmation.

## hospital / airport — manual, dated

1. The hospital's official page (ASL/AO site) for name + town; a mapping
   tool read for drive minutes — record the tool in `source_label`
   (e.g. "Google Maps read, typical drive").
2. Airport: the airport's official site; drive minutes as above.
If no tool read was done, say "estimated from road distance" in the label.

## expat_presence — community evidence

1. Dated community sources: Expats-in-Italy / InterNations groups, local
   English-language associations, comune foreign-resident stats (ISTAT
   "stranieri residenti" per comune is the cleanest signal).
2. Absence of evidence = `low` only if you actually looked; otherwise leave
   empty.

## climate_note / fit_note — judgment, no source needed

Write from the sourced climate data you have seen plus the brand voice:
honest, specific, one watch-out minimum. Dated via `last_verified`.
