# Motion Concept (early gate)

Run this AFTER typography and BEFORE imagery/tokens. Output: `stages/motion-concept/motion-concept.md`. The later `motion` stage (tokens + reference implementations) consumes this approved concept; it does not re-open these decisions.

Motion is brand voice in motion — define it while imagery and components are still undecided, so signature moments can steer asset choices (e.g. a hover crossfade from illustration to photograph requires producing both versions of the same image).

## Concept template

1. **Motion principles** — 3 short principles tied to the approved brand territories (e.g. "calm, never hurried" for a trust brand; "reveal, don't decorate").
2. **Primitives**:
   - Duration bands: micro (hover/press, 150–250 ms), UI (250–450 ms), scene (page/hero, 450–800 ms). Cap UI motion at ~500 ms.
   - Easing: name 1–2 curves after the brand concept (e.g. standard ease-out for entrances, gentle ease-in-out for ambient loops). Provide cubic-bezier values.
   - Distance/scale deltas (e.g. 8–16 px translate, 1.0→1.02 scale) so motion stays subtle.
3. **Signature moments** — 1–3 named, memorable interactions, each with: trigger, from-state, to-state, duration/easing, and asset implications. Example: "The Reveal — hero image crossfades from line-art to full photograph on hover, 600 ms; implies every hero ships in illustrated + photographic versions."
4. **Scroll + page behavior** — reveal policy (what animates on scroll, stagger rules), page-transition style.
5. **Reduced-motion policy** — `prefers-reduced-motion` fallback for every animated pattern (typically: instant swap or simple opacity fade); no parallax or vestibular-triggering motion without fallback.

## Approval checklist

- [ ] 3 principles trace to approved strategy/territories
- [ ] Duration bands and easing curves have concrete values
- [ ] Each signature moment lists its asset implications (so imagery production can plan for them)
- [ ] Reduced-motion fallback defined per pattern
- [ ] User approved the concept doc before tokenization
