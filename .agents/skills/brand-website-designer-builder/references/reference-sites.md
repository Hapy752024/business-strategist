# Website references and supplied photos

Apply to a new website or a material visual redesign. A copy fix, tracking integration, performance repair or maintenance task preserving the design does not restart creative intake.

## Intake once, then inspect

Reuse references, photos, preferences and decisions already supplied. If references are missing, ask once for a small set (normally 2–5) of websites the user likes, what they like about each, and anything to avoid. In the same intake, offer user photos for direct use or AI guidance. Example:

“Which websites should guide the look, and what do you like about them? You can also attach photos to use as supplied or to guide AI images; tell me which use you want. If you have no references or photos, say none.”

The question is a normal new-site step, not a requirement that the user supply URLs or photos. An explicit “none”, “choose for me”, or existing adequate brief lets work continue; record it and use a proportionate reference search or the approved brand. Do not ask repeatedly, invent user preferences, or start business research.

For supplied URLs, inspect the actual rendered site at desktop and mobile where tools allow. For screenshot references, inspect the actual images. Record layout/hierarchy, spacing, palette, type roles, imagery/crops, navigation/components, and observed motion. Separate user likes from your observations and recommendations. If a page cannot be inspected, record the gap and use accessible references; do not infer its style from a title or claim a screenshot review that did not happen.

Write a compact `design/reference-review.md`: source URL/image, inspection date and evidence, specific traits, what to adapt/avoid, accessibility/performance implications, and how those choices translate into this site's direction. Cross-category references are valid. Combine useful principles into an original design; reference sites do not confer rights to their code, logos or photographs. Reuse the benchmark method in `../../brand-guideline-researcher/references/research-method.md` where useful; a narrow reference pass does not require a full brand research project.

## Photo sets

Accept attachments, existing local files, shared folders/archives and accessible image URLs. Inventory the actual available files and inspect each usable photo or a labelled contact sheet. Ask for missing access only when needed. Do not claim to have inspected unavailable images.

Reuse an explicit batch instruction, such as “use all these as references”. Otherwise ask only for missing distinctions: use as supplied, edit, AI reference/guidance, or visual-brief inspiration without uploading the original. A photo can have multiple approved uses. Record the default plus any per-photo exceptions, preferred placements and crop restrictions. User-selected photos are useful design input; do not replace them automatically with generic stock or an AI generation.

Follow `../../brand-asset-producer/references/image-sourcing.md` for rights, original-file protection, input transfer and generated-output lineage. Native generation must follow the available `imagegen` skill, including its actual reference-input limits; do not silently omit a required photo when a set exceeds one call's limit.

## Persist and consume

Use existing `website-preferences.json` fields rather than inventing incompatible top-level keys:

- `choices.reference_sites_status`: unresolved, supplied, none, delegated, or pending.
- `choices.reference_sites`: URL/image reference list; record inspection notes under `choices.reference_review` as a path.
- `likes` and `dislikes`: reference, quality and reason; retain user-stated versus agent-inferred provenance.
- `choices.supplied_photo_assets`: asset IDs or private relative paths; `choices.image_asset_manifest`: the imagery manifest path.

Record observations in the review, per-photo permissions/use in the asset manifest, and confirmed taste in preferences. Carry the review and approved photo guidance into creative territories, imagery selection and the hero slice. Resume saved choices without re-interviewing. If inference is needed, label it and keep it reversible.
