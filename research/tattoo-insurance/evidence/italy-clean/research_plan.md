# Research Plan

This plan is generated before provider collection so the research flow has an explicit plan step before evidence interpretation.

## Objective

Test whether public evidence supports the hypothesis behind `Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo` for `Adults in Italy considering or recently getting a tattoo`.

## Current Assumptions

- Geography/language: `IT/it`
- Public evidence can identify pain patterns and interview targets, but cannot validate willingness to pay alone.
- Weak evidence should trigger user review and interviews, not a viability conclusion.
- User interaction should ask exactly one question at a time.

## Provider Plan

- `reddit`
- `serpapi_google_trends`
- `youtube`
- `firecrawl`
- `brave_search`

## Enrichment Checkpoint

This appears to have an app-market angle. Ask the user one question before spending Sonar credits:

`Do you want app-store enrichment via Sonar for keyword demand, app reviews, and competitor app context?`

If yes, rerun with explicit `--providers default,sonar`. Add `--sonar-apps ios:<id>,android:<package>` when competitor app review or revenue evidence is needed.

## Query Strategy

- Start with problem-first terms before solution-led terms.
- Include German umlaut and ASCII variants where relevant.
- Keep Google Trends terms short and search-like.
- Treat competitor/editorial/provider pages as category context, not user demand.

## Google Trends Preview

- `tatuaggio infezione`
- `reazione allergica inchiostro`
- `rimorso tatuaggio`
- `rimozione tatuaggio`
- `tatuaggio fatto male`

## Query Sample

- `Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo`
- `"why is it so hard to" Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo`
- `"how do you deal with" Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo`
- `"frustrated" Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo`
- `"alternative to" Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo`
- `"best way to" Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo`
- `Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo forum pain points`
- `Tattoo risks, regret, removal, infection and aftercare concerns before getting a tattoo reddit complaints`
- `tatuaggio infezione`
- `"why is it so hard to" tatuaggio infezione`
- `"how do you deal with" tatuaggio infezione`
- `"frustrated" tatuaggio infezione`
- `tatuaggio infezione forum complaints`
- `tatuaggio infezione reddit workflow`
- `reazione allergica inchiostro`
- `"why is it so hard to" reazione allergica inchiostro`
- `"how do you deal with" reazione allergica inchiostro`
- `"frustrated" reazione allergica inchiostro`
- `reazione allergica inchiostro forum complaints`
- `reazione allergica inchiostro reddit workflow`
- `rimorso tatuaggio`
- `"why is it so hard to" rimorso tatuaggio`
- `"how do you deal with" rimorso tatuaggio`
- `"frustrated" rimorso tatuaggio`
- `rimorso tatuaggio forum complaints`

## Planned User Checkpoint

Ask one question after collection:

`Which evidence item feels most like real buyer pain to you?`

Recommended next research if evidence is mostly weak: run 8-12 customer interviews before making a business-viability conclusion.
