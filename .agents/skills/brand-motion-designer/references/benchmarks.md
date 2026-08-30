# Motion Benchmarks

## Purpose
Catalog of named polished-motion patterns drawn from apps known for "magical" UX (Airbnb, iOS, Apple Pay, Linear, Vercel, Stripe). Each entry is a reverse-engineered spec the skill can reference during pillar tuning and element iteration.

## Patterns

### Airbnb Card Hover
- Used on: listing cards on airbnb.com.
- Motion: `scale(1.02)` + `box-shadow: 0 8px 24px rgba(0,0,0,0.12)`.
- Duration: 200ms.
- Easing: `ease-out`.
- Why it feels good: subtle scale + soft shadow reads as "lift", not "popup"; 200ms is fast enough to feel responsive but slow enough to register.

### iOS Spring (Sheet/Modal Open)
- Used on: bottom sheets, modal dialogs in iOS.
- Motion: `spring(stiffness=300, damping=30)`.
- Why it feels good: spring physics model real-world inertia; the small overshoot reads as "settling", not "stopping".

### Apple Pay Button Press
- Used on: Apple Pay confirmation button.
- Motion: `scale(0.95)` over 100ms + haptic feedback (mobile).
- Easing: `ease-out`.
- Why it feels good: 100ms is at the threshold of "instant" but the scale-down gives physicality; haptic closes the loop on mobile.

### Linear Command Palette Entry
- Used on: Linear's command palette popover.
- Motion: `opacity 0 → 1` + `translateY(8px → 0)` over 120ms.
- Easing: `ease-out`.
- Why it feels good: 8px translate is just below the eye's saccade threshold for "movement" — it registers as arrival, not travel.

### Vercel Deployment Success
- Used on: Vercel dashboard deployment success state.
- Motion: checkmark stroke draw + confetti burst (Canvas), 600ms total.
- Easing: `ease-in-out` for stroke, `ease-out` for confetti.
- Why it feels good: stroke draw gives the checkmark agency; confetti is restrained (12 particles, not 100).

### Stripe Chart Reveal
- Used on: Stripe dashboard charts.
- Motion: `clip-path` wipe left-to-right + axis fade-in, 600ms.
- Easing: `ease-in-out`.
- Why it feels good: wipe reads as "data arriving", not "chart drawing"; axis fade-in grounds the chart before data lands.

### iOS Swipe-to-Dismiss
- Used on: iOS list cells (Mail, Messages).
- Motion: `translateX` follows finger; on release, spring back if <50% or animate out if >50%.
- Spring: `spring(stiffness=400, damping=40)`.
- Why it feels good: 1:1 finger tracking is the most natural interaction possible; the 50% threshold + spring gives a clear "committed" vs "cancelled" feel.

## Using Benchmarks
- During pillar tuning, the user may say "make it feel like X". The skill looks up X in this catalog and uses the spec as the starting point for the first demo option.
- The Stop hook requires at least one benchmark pattern cited per chosen pillar in `motion-guidelines.md`. Citation format: `Benchmark: <pattern name> from references/benchmarks.md`.

## Adding New Benchmarks
- When the user references a pattern not in this catalog, the skill reverse-engineers it (durations, easings, transforms) and appends a new entry to this file before using it. The new entry must include: name, used on, motion, duration, easing, why it feels good.
