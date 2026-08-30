# Simple A/B experiment

Use Vercel Flags with a typed `control`/`treatment` flag and server evaluation. Declare one hypothesis, one changed variable, one primary conversion event, audience, allocation, guardrails, start/stop rule, and cleanup owner. Emit the flag value with `FlagValues` and attach it to the approved event; send no PII.

Override both variants in Preview before requesting production activation. Never claim a winner from low traffic, repeated peeking, or a metric that was not declared in advance. Keep a control-only fallback when Flags or Web Analytics is unavailable. Remove the losing branch and archive the flag after the decision.
