# Coherence Review

## Purpose
After all pillars are tuned and all in-scope elements are specified, scan for token drift and produce a coherence verdict before final reference implementations are written.

## Procedure
1. Load every `stages/motion/pillars/<pillar>/tokens.json` and `stages/motion/elements/<category>/<element>/spec.json`.
2. For each element spec, check:
   - Does it reference a pillar by name that exists in the pillar set?
   - Are all overrides (in the `overrides` list) accompanied by a non-empty `justification`?
   - Do any CSS properties in the spec use durations or easings that don't match any pillar token (a sign of hardcoded values bypassing the system)?
3. Flag any spec with overrides as `coherent-with-caveats` and list the justifications.
4. Flag any spec with hardcoded values that bypass pillar tokens as `needs-rework` and list the specific properties.
5. Produce `stages/motion/coherence-review.md` with this structure:

```markdown
# Motion Coherence Review

## Pillars Locked
- <pillar-name>: durations=<count>, easings=<count>, springs=<count>, benchmark=<pattern name>

## Element Specs Reviewed
- <category>/<element>: pillar=<pillar-name>, overrides=<count>, verdict=<coherent|coherent-with-caveats|needs-rework>

## Overall Verdict
<coherent | coherent-with-caveats | needs-rework>

## Required Rework (if any)
- <category>/<element>: <description of issue>
```

6. If the overall verdict is `needs-rework`, do not proceed to final reference implementations. Surface the rework list to the user and ask whether to fix now or accept the caveats.

## Coherence Verdict Definitions
- **coherent**: every element spec references a valid pillar, no overrides.
- **coherent-with-caveats**: every element spec references a valid pillar, some overrides exist but all have justifications.
- **needs-rework**: at least one element spec references a missing pillar, has unjustified overrides, or has hardcoded values bypassing the token system.
