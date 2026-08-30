# Business + Brand Integration Plan Review

## Score: 90/100 — FLAG

### BLOCK items (must fix before implementation)

- None.

### FLAG items (should fix, but can proceed)

- The required code-review graph was unavailable, so blast radius was checked through direct repository inspection rather than a dependency graph. Re-run the impact-radius review before changing shared workspace, validation, and harness files.
- The dedicated `security-review` and `brand-compliance` skills were unavailable. The expanded plan now touches FAL, GitHub/Vercel permissions, Preview/Production deployment, analytics, and feature flags. It therefore keeps the first website milestone local/Preview-only, analytics-off, unauthenticated, and non-transactional and requires those specialist reviews before production activation ([plan, Workstream H3](./2026-08-30-business-brand-integration.md#h3-security-boundaries)).

### Category breakdown

| Category | Score |
|---|---:|
| Architecture | 20/25 |
| Security | 25/30 |
| Data Flow | 20/20 |
| UX | 15/15 |
| Testing | 10/10 |

### Recommended review order

1. Baseline both dirty worktrees, map shared-file impact, and approve the import inventory.
2. Implement and test schemas, revision-checked manifest writes, routing, explicit approvals, the shared FAL adapter, and the local Next.js visual-build path before connecting external services.
3. Run dedicated security and brand-compliance reviews before GitHub/Vercel production access, analytics, or flags; then complete blind screenshot and behavioral old/new evaluation before rollout.

Review scope note: fallback review used the source brand project's visual, accessibility, asset-provenance, and trusted-tool references; the destination's provider/security policies; and current official Next.js, Vercel, FAL, v0, and web.dev documentation. This is sufficient for planning, but it does not replace the unavailable specialist reviews or a current entitlement/security check immediately before external setup.
