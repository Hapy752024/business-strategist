# Element Motion Taxonomy

## Purpose
Define the 8 categories of element-level motion the skill knows about. The user picks in-scope categories + priority order; the skill iterates them one at a time using the same ask -> 2-3 demos -> feedback -> lock loop as pillar tuning.

## Categories

### 1. Press / Tap Feedback
- Elements: buttons, cards, list items, toggles.
- Typical spec: scale (0.95-0.98), box-shadow lift, haptic on mobile.
- Pillar reference: usually Responsive.

### 2. Page / Route Transitions
- Elements: route changes, modals, drawers, sheets.
- Typical spec: translate + opacity; View Transitions API where supported.
- Pillar reference: usually Directional.

### 3. Data Reveal
- Elements: charts, counters, KPI numbers, tables, lists.
- Typical spec: clip-path wipe, staggered fade-in, count-up for numbers.
- Pillar reference: usually Natural or Continuous.

### 4. Morph / Grow
- Elements: card expand, detail panel open, image zoom.
- Typical spec: shared element transition, FLIP technique, scale + translate.
- Pillar reference: usually Continuous.

### 5. Drag and Reorder
- Elements: list reordering, swipe, drag-to-dismiss.
- Typical spec: spring on release, opacity fade on dismiss.
- Pillar reference: usually Expressive.

### 6. Loading States
- Elements: skeletons, shimmer, spinners, progress bars.
- Typical spec: shimmer keyframes, skeleton pulse, indeterminate progress.
- Pillar reference: usually Natural.

### 7. Notifications
- Elements: toasts, snackbars, banners.
- Typical spec: slide-in + fade-out; auto-dismiss timing.
- Pillar reference: usually Directional or Responsive.

### 8. Scroll-Driven Motion
- Elements: parallax, sticky headers, reveal-on-scroll.
- Typical spec: scroll-linked transforms, IntersectionObserver-triggered reveals.
- Pillar reference: usually Continuous.

## Custom Categories
- The user may add a custom category. The skill captures: element list, typical spec, pillar reference, and iteration plan.

## Iteration Procedure Per Category
1. Ask the user which elements within the category are in scope (e.g., for Press / Tap Feedback: just buttons, or buttons + cards + toggles?).
2. For each in-scope element, use `scripts/generate-demo.py --category <name> --element <name> --pillar <pillar-name>` to scaffold 2-3 HTML+CSS demos under `stages/motion/elements/<category>/<element>/option-N.html`.
3. Each demo must reference pillar tokens by name in its CSS (`var(--motion-duration-<pillar>-<variant>)`, `var(--motion-ease-<pillar>-<variant>)`).
4. Tell the user to open each demo in a browser and report which feels closest.
5. Iterate on the chosen option until approved.
6. Lock the element spec; write it to `stages/motion/elements/<category>/<element>/spec.json` with fields: `category`, `element`, `pillar`, `description`, `cssProperties` (list), `overrides` (list of {property, value, justification} - empty if none).

## Coherence Rule
- Overrides are allowed only with explicit justification recorded in `spec.json`. The coherence review (see `references/coherence-review.md`) flags any spec with overrides.
