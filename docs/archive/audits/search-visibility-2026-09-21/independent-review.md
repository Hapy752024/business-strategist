# Superseding review — owner price correction, 2026-09-23

**Current recommendation: accept the local removal of the wrong price; keep offer-scope approval unresolved.** The owner's statement, “The price is 49 USD. The plan price is WRONG,” supersedes old repository constants and the prior review below. The prior approval of a $49 review versus a $149 plan was mistaken: agreement among existing files did not establish owner approval. Do not reuse that finding, its screenshots containing $149, or its approval as current commercial evidence.

Re-reviewed actual current diffs for `app/legal.ts`, `app/about/page.tsx`, `app/book/page.tsx`, `app/guide/page.tsx`, `app/faq/page.tsx`, `app/legal-pages/terms/page.tsx`, `app/mobile-sticky-cta.tsx` and `tests/search-visibility.spec.ts` against the unchanged source. Source search found no remaining `149` or `planPrice` reference in `app/`. Current `OPERATOR.price` is `$49 USD`; no replacement plan price has been invented. Removing the unsupported separate price across the offer and terms is consistent with the owner's correction.

**Unresolved commercial scope:** the user has not yet clarified whether 49 USD includes the full written plan or only a call and recap. Existing terms still call the full plan an “optional follow-on”; book/about/FAQ still describe a credit toward a later plan/package. Those statements are retained legacy scope, not newly validated facts. Guide/booking copy describing a short recap likewise does not resolve what else the 49 USD includes. The current draft must not be presented as a final approved scope or published on the strength of this review. Once the owner answers, align those statements and related deliverable promises consistently; do not infer a second product price or a new guarantee.

The mobile sticky CTA now sits inside `nav aria-label="Quick booking"`, addressing the prior landmark finding in source. The added mobile Axe assertion exercises that landmark; shorter mobile heights and wrong-price absence are included in regression checks. Independent rendered recheck after the rebuild passed: `/guide` at 390×844 with optional cookies rejected has zero Axe violations and a visible Quick booking navigation link. `/book` at 375×667 has zero Axe violations, zero horizontal overflow, a visible $49 USD price, no 149 text, and the primary action spans y 511.81–584.59, fully within the viewport. Fresh viewport screenshots `/tmp/visibility-critic-final-guide.png` and `/tmp/visibility-critic-final-book.png` were inspected. The scope answer remains pending; rendered success does not approve unresolved commercial scope. Previous screenshot and Axe results below describe the earlier revision only.

No additional scoped code defect found in this source re-review. Existing launch dependencies and missing live uplift evidence remain unchanged. The three supplied-facts transfer exercises below remain valid; they did not depend on Italy's disputed offer scope.

---

# Historical review — superseded on commercial price/scope approval

# Independent scoped review — 2026-09-22

## Findings and recommendation

No HIGH or MEDIUM defect found in the scoped implementation or reusable decision procedure. Recommend approval of the local edits, subject to the existing launch blockers. This is not deployment approval or evidence of visibility/conversion uplift.

Compared actual `/tmp/search-visibility-italy-site/app/{book,guide}/page.tsx` against the unchanged project source; reviewed `tests/search-visibility.spec.ts`, `app/legal.ts`, search-visibility-decisions.md, ai-answer-recordings.md, owner-actions.md and website AEO/GEO and DEO procedures. Did not read the creator's rationale or plan.

The guide distinguishes the $49 short recap from the $149 full move plan, matching the existing operator constants and booking offer. It removes an unsupported blanket freshness statement and gives the topic-card h3 headings a parent h2. The new booking action reuses the original email request template and explicitly explains that it neither takes payment nor confirms booking. It preserves the existing page offer, visual system and fallback email route.

The reusable procedure allows no change when evidence does not justify one, respects quote pricing, distinguishes missing data from zero, and keeps manual improvement work independent from optional instrumentation. It does not authorize account connections, publication, recurring commitments or invented live answer recordings. Owner-only actions preserve existing authorization and do not turn optional recommendations into blockers.

## Independent browser evidence

Inspected freshly captured mobile/desktop booking screenshots. No scoped clipping, overlapping text or hidden action found. With optional cookies rejected:

| Viewport | New action bounds | Horizontal overflow |
|---|---|---|
| 375 × 667 | y 540.61–613.39 | 0 px |
| 390 × 844 | y 507.02–559.41 | 0 px |
| 1440 × 900 | y 516.88–569.27 | 0 px |

Screenshots: `/tmp/visibility-critic-book-375.png`, `/tmp/visibility-critic-book-390.png`, `/tmp/visibility-critic-book-1440.png`. These shorter mobile-height checks supplement the committed test's 900 px height. Initial Chromium execution was sandbox-blocked; approved execution outside the sandbox succeeded. No booking email was sent.

Missing live evidence is not a code defect: no production search impressions/citations, customer-conversion baseline, delivered-email proof or observed uplift was supplied. Mailto success depends on the visitor's email setup; the pre-existing direct email fallback remains available. Legal/operator placeholders and existing launch dependencies remain unchanged and are not cleared by this review. External vendor factual claims in the reusable references were not independently refreshed during these supplied-facts-only transfer tasks.

## Transfer task 1 — quote-based B2B translation service

**Scoped audit finding:** The supplied facts establish variable pricing by language and length and an already readable quote request. They establish no broken route or deficient visibility. Keep the quote model and existing request path; do not invent a fixed price, force Product/Offer markup, or recommend new analytics/accounts solely to fill the audit.

| Page/customer task | Dated observation and uncertainty/source | Change | Expected outcome | Agent work | Owner-only dependency | Priority/effort | Acceptance | Review/stop |
|---|---|---|---|---|---|---|---|---|
| Request a translation estimate | 2026-09-22 supplied scenario: request visible; price varies by language/length; no analytics. Actual page, logs and search performance not supplied. | No content change yet. Inspect the supplied page and quote destination when available; verify that any visible pricing explanation accurately preserves the variable estimate. | Detect an actual obstruction if present; benefit otherwise unknown. | Review HTML/rendering, navigation, quote destination and any already authorized first-party exports/logs; report unavailable metrics as unknown. | Only unavailable firsthand commercial facts or a new connection/publication decision if it becomes necessary. No owner action accepted by this exercise. | Bounded one-off page check; no ongoing monitoring program. | Quote request remains readable and usable; no unsupported fixed-price claim; any findings cite actual page evidence. | Close after the one-off inspection if no material defect is found. Reopen when page/offer facts change or relevant performance evidence arrives. |

No new research workspace, instrumentation, schema or live AI panel is justified by the supplied facts. A visibility outcome cannot be measured from this scenario.

## Transfer task 2 — exactly two replacement headings

Garden Maintenance Services

Contact Us

## Transfer task 3 — ecommerce price mismatch and stale export

**Next action:** Prepare a local correction from 29 EUR to the approved inventory price of 35 EUR, preserving the exact product/variant identity. Compare the page's visible price and any existing price markup against the approved inventory record. Rebuild a draft feed from a verified current authoritative source; do not reuse the stale export or publish anything.

| Page/customer task | Dated observation and uncertainty/source | Change | Expected outcome | Agent work | Owner-only dependency | Priority/effort | Acceptance | Review/stop |
|---|---|---|---|---|---|---|---|---|
| Assess the product's price | 2026-09-22 supplied scenario: page 29 EUR, approved inventory 35 EUR, stale last feed. Product identifier, source timestamp and freshness limit not supplied. | Draft local price correction and a fresh candidate export; keep stale data out of publication. | Consistent customer price expectation; conversion effect unknown. | Verify product/variant and current inventory authority/freshness; reconcile visible price, existing markup and candidate feed, document diff. | Only missing owner-only commercial truth if authoritative records cannot resolve it; no need to reconfirm the already approved 35 EUR. Publishing is excluded. | High priority for misleading price; narrow correction, effort depends on access. | Same product/variant shows 35 EUR in all draft applicable surfaces, current source and freshness recorded, no stale-export propagation. | Stop after validated local handoff; no upload/scheduler/publishing. If current source freshness cannot be established, retain the draft and block feed release. |

Before any future feed publication, the existing feed contract's freshness, deletion/replacement, acknowledgement/rejection and retry safeguards must be satisfied. This task does not start that integration or publish a feed.

## Transfer result

All three tasks could be completed within their requested scope using the reusable procedure. It produced no invented demand or outcome evidence, no unwanted fixed pricing, no extra heading deliverables, and no publication. These are independent scenario executions using supplied facts, not claims of broad empirical reliability.

## Accessibility follow-up

Independent Axe at 390×844 found zero violations on `/book`. On `/guide` it reports one moderate `region` warning for the existing `.mobile-sticky-cta` link outside a landmark. This shared mobile component was not introduced by the scoped edits; the changed guide's new heading structure is correct. Record this as a pre-existing LOW accessibility issue for local approval, not a blocker or a clean whole-site accessibility claim. Fresh viewport screenshots `/tmp/visibility-critic-guide-viewport.png` and `/tmp/visibility-critic-book-viewport.png` were inspected. The scoped elements are legible, responsive and visually consistent.
