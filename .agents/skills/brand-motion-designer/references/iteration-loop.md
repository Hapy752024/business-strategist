# Iteration Loop

## Purpose
Define the mechanics of the ask → 2-3 demos → feedback → next iteration loop used in both pillar tuning and element-level motion specs.

## Loop Steps
1. **Ask.** Pose one question to the user about the desired feel. Provide 2-3 multiple-choice options when possible (e.g., "Should this feel: 1. Snappy and immediate, 2. Smooth and organic, 3. Bouncy and playful?").
2. **Generate.** Based on the answer, use `scripts/generate-demo.py` to produce 2-3 distinct HTML+CSS demo files. Each demo must be a standalone `.html` file (no build step) that the user can open directly in a browser.
3. **Present.** Tell the user: "Open these in your browser and tell me which feels closest: 1. <path option-1.html> 2. <path option-2.html> 3. <path option-3.html>. Or describe what's off and I'll iterate."
4. **Feedback.** Wait for the user's response. Acceptable responses: a number (1/2/3), a description ("option 2 but slower"), or a redirect ("let's try a different direction entirely").
5. **Iterate.** If the user picked an option with refinements, regenerate just that option with the refined tokens. If the user wants a new direction, regenerate all 2-3 options with different starting tokens.
6. **Lock.** When the user says "approved" / "lock it" / "ship it", record the locked token set to the appropriate `stages/motion/...` path and move to the next pillar or element.

## Loop Termination
- Hard cap: 3 iteration rounds per pillar or element. If not approved after round 3, surface to the user: "We've iterated 3 times. Want to (1) accept the latest, (2) skip this pillar/element for now, or (3) take a different approach?"
- This cap prevents the loop from consuming the entire session budget on a single decision.

## State Persistence
- After each round, write the current state to `stages/motion/iteration-state.json` (path: `stages/motion/iteration-state.json`):
  ```json
  {
    "phase": "pillar|element",
    "current_pillar": "<name or null>",
    "current_category": "<name or null>",
    "current_element": "<name or null>",
    "round": <int>,
    "options_under_review": ["<path>", "<path>", "<path>"],
    "last_user_feedback": "<text>"
  }
  ```
- The PreCompact hook saves this file; PostCompact restores from it.
