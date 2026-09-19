# Branding-owned favicon set

Branding owns design, approval and export. Reuse an approved mark; if absent obtain minimal mark/direction approval without requiring full Business/Branding completion. Test optical legibility at 16/32px on light/dark browser chrome.

Export sanitized SVG, real multi-resolution ICO with 16/32/48px entries, 180px Apple touch PNG, and 192/512px PNGs for manifest contexts. Use existing export tooling with requested sizes; inspect dimensions and actual ICO entries, not filenames. Preserve aspect ratio and intentional padding/background; do not square-stretch a wordmark. Missing tools/formats keep handoff pending.

Record paths, MIME, sizes, SHA-256 and approval/source provenance in brand asset manifest with role-to-file website handoff. Regenerate after mark changes. Website integrates approved files through Next.js icon/manifest conventions and tests URLs; missing/unapproved set blocks production.
