# Topic Workspaces

Create one directory per researched business topic with:

```bash
python3 scripts/evidence_scout/init_topic.py --topic "<topic>" --customer-segment "<segment>"
```

The workspace manifest is the source of truth for stage, gates, blockers, artifacts, and next action. Existing legacy runs under `research/evidence-scout/` remain immutable historical evidence; migrate or reference them deliberately rather than guessing that similarly named runs belong to the same thesis.
