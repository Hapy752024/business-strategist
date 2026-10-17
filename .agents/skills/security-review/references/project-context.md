# Discover the Target Project

- Resolve the project or subproject selected by the user. Read its instructions, dependency manifests, architecture and relevant code before assuming frameworks or providers.
- Identify entry points, identity/session model, tenants or ownership boundaries, data stores, third parties and deployment boundaries.
- Classify actual sensitive data and retention requirements; regulated data and payment processing are conditional, not defaults.
- Discover authoritative server-side pricing and order records when payments exist. Confirm how retries and concurrent requests are handled durably.
- Find existing security tests and CI scanners and report what was actually run. Do not assume a particular cloud host, error tracker, migration framework or test layout.
- Preserve applicable project and Business gates. Standalone technical security review does not initiate customer research or authorize a launch.
