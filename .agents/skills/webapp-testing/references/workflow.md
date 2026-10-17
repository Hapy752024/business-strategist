# Browser Workflow

1. Resolve the target application and requested behavior. Read its instructions, scripts and test configuration; use an existing browser runner where possible.
2. Confirm the local URL and readiness. If starting servers, discover the actual commands and ports. The optional `../scripts/with_server.py` helper supports multiple servers; run its help before use and stop processes started for the task afterward.
3. Inspect rendered content and accessible roles before choosing locators. Prefer role/label locators and assertions that wait for the expected element or state. Network-idle is not a universal readiness condition, especially with polling or streaming.
4. Exercise the requested journey, validation and relevant failure states. Use the target's supported viewport sizes and languages. Keep all transactions synthetic and verify provider test mode before payment exercises.
5. Capture relevant screenshots, console errors and failure traces without secrets or personal data. Use the target project's evidence convention or a task-specific temporary directory.
6. Report expected versus observed behavior, reproduction steps, commands, environment and evidence. Distinguish browser checks from unit tests and production verification.

