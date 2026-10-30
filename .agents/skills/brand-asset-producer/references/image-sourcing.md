# Website image sourcing and AI references

Use for website photographs, illustrations, textures and hero/card imagery. Reuse the approved website/brand direction or the user's scoped image brief. A single image or a supplied-photo placement does not need a new logo or full branding process. For a new imagery system use `imagery-art-direction.md`; for an existing approved style, apply it directly.

## Pick the source for each placement

Inventory supplied photos, existing approved assets and reference images before searching elsewhere. Record the placement, subject, aspect ratio, text-safe area, expected dimensions and alt-text purpose. Choose user photography, licensed stock, AI generation, or a mix according to the brief. Do not assume all imagery must be generated or all stock must be avoided.

### User-provided photo sets

Accept attachments, local files, accessible image links and folders/archives. Inspect the actual files, assign stable asset IDs, and preserve private originals unchanged. Reuse the user's stated ownership/permission and intended use; do not ask for the same authorization again. Clarify only a material missing permission or usage choice.

Map each photo to one or more approved uses:

- **As supplied:** retain the scene and composition. Normal web resizing/compression and removal of unnecessary EXIF/GPS metadata are allowed; substantive edits or composition-changing crops need the user's direction. Do not upload an as-supplied-only photo to an AI service.
- **Edit:** perform the requested alteration with the selected image editing tool, retaining an original and recording the transformation.
- **AI guidance/reference:** use the supplied scene, palette, lighting, composition or subjects as generation guidance. A request to use photos as AI references authorizes that reference workflow within the selected tool/scope; no repetitive generic confirmation is needed. Respect a user restriction against uploading originals.
- **Brief only:** inspect the photo and describe approved visual principles in a new prompt without transferring the source file to the generation provider.

A batch default applies to the whole supplied set unless the user gives per-photo exceptions. Record which photos are used directly and which inform each generated output. If a tool cannot accept the entire set, inspect the set first, select and name suitable references per output or split the work into batches; do not claim every photo was passed to a model. Ask for an unavailable required image again only when the tool's attachment mechanism cannot include it.

### Licensed stock: find, verify, acquire

1. Search an appropriate library using available image/web tools. Shortlist images that fit the subject, audience, layout and approved visual style. Search thumbnails are discovery aids, not proof of rights.
2. Open the actual asset page and current license/terms. Verify that the exact asset/version is covered for the intended commercial/editorial use, modifications, delivery channels and any required attribution. Check relevant people/property/brand releases and avoid implied endorsements. A reference website's image is not reusable merely because its page is public.
3. Record the asset ID, creator, canonical source page, license URL/version and checked date, permitted planned uses, attribution text, restrictions, and a private proof/receipt reference when relevant. Do not publish credentials, receipts or signed download URLs.
4. Download the permitted original, not a watermarked preview. Retain its provenance and hash. Publish optimized local derivatives when permitted; honor any applicable API attribution/hotlink/download conditions rather than treating the image license as the entire API contract.
5. Implement required visible credits and keep a public attribution record where needed. Paid acquisition or new generation spend follows existing authorization; a stock search alone does not authorize buying a license.

If rights for one proposed use are unresolved, resolve that asset/use or choose a permitted substitute. Continue independent website work. Do not impose an all-stock prohibition or a new approval ceremony for already authorized, adequately licensed use.

## Licensed stock as AI inspiration is allowed

A licensed stock image may guide an AI-generated image. Do not reject this merely because the source is stock. Distinguish the planned use:

- Visual inspiration or a text-only brief describing palette, mood, lighting, composition and subject principles.
- Uploading the source as a model reference, image-to-image input or editing input.
- Training/fine-tuning a model, which is a separate use and is not authorized by a request to generate a website image.

Check permissions for the actual use, including express AI restrictions and the selected provider's input/training/retention terms. Do not require the literal word “AI” when existing permissions already cover the planned use, and do not treat a training-only restriction as an automatic ban on every generation workflow. Conversely, commercial website display permission alone does not establish permission for every third-party upload. If upload is restricted, use a permitted brief-only workflow or another appropriately licensed source. Do not transfer a restricted file to a model or represent an AI transformation as erasing source obligations.

Preserve any attribution/derivative obligations that apply to the actual output, and review for near-copying of distinctive protected content, marks, watermarks or misleading real-world claims. Inspiration should create imagery suited to this brief, not a disguised copy of a stock photograph. No blanket claim of exclusive ownership, copyright protection or rights clearance follows solely from AI generation.

## Generation tool handoff

When the environment provides the **imagegen** skill and built-in **image_gen** tool, load that skill and use its native generation/editing workflow by default for raster imagery. This capability is environment-owned: discover its advertised location rather than adding a duplicate repository skill or hardcoding a home directory. Follow its reference-image mechanisms, inspection rules and input limits. Do not require FAL/OpenRouter credentials when native image generation is available.

Use FAL or OpenRouter alternatives when explicitly selected or when the native option is unavailable and an authorized alternative is appropriate. Apply `scripts/fal_assets.py` only through the existing `workflow.md`/website `fal-assets.md` instructions; no FAL-specific flags are imposed on the native tool. Before paid generation, retain the approved need, quantity, dimensions and available cost limits; reuse valid authorization. Do not silently substitute a different paid provider. If no generation tool is available, continue the layout with labelled placeholders or permitted existing imagery and state the missing capability.

For final assets, inspect the result at its actual hero/card/mobile crop, verify dimensions and visual fit, optimize delivery, and supply meaningful alt text or mark decorative imagery appropriately. Keep original licensed/supplied files private when required; strip unnecessary personal metadata from published derivatives. Generated imagery must not masquerade as documentary proof, a real client testimonial, a real staff photo or an actual property photograph.

## One image provenance manifest

Maintain `assets/image-assets.json` (or reuse an existing compatible imagery manifest). For each source and output, record:

- Stable asset ID, source kind (user/stock/generated/derived), private local path or approved published path, hash, dimensions and placements.
- User usage modes and per-photo exceptions; rights basis, planned-use status, relevant restrictions, license evidence and attribution requirements.
- `reference_use` (brief-only/model-input/image-to-image), source asset IDs actually used, and the generated output's parent/reference IDs.
- For generation: tool/provider/model where available, prompt, dimensions, generation reference/seed if supplied, and applicable approval/cost record. Mark unavailable metadata as unavailable; do not fabricate it.
- Review/approval state, transforms/crops, output files and required credits. Public manifests must redact private paths, people/customer details, receipts and access tokens.

Do not overwrite an existing export manifest with a new incompatible format. Add the source/rights lineage to the existing asset record or link the imagery manifest. The website consumes the actual approved files and the recorded rights/placement decisions, rather than rediscovering or regenerating them.

Primary examples checked 23 October 2026 (verify current terms for each acquisition): [Unsplash license](https://unsplash.com/license), [Pexels license](https://www.pexels.com/legal-pages/license/), [Pexels terms](https://www.pexels.com/terms-of-service/), and [Getty terms](https://www.gettyimages.co.uk/eula). These examples are not a blanket permission for every asset, plan or AI input workflow.
