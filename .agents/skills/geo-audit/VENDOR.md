# Vendored source

- Upstream: https://github.com/Auriti-Labs/geo-optimizer-skill (GEO Optimizer by Juan Camilo Auriti)
- Pinned commit: `7ecec864690ee430e954a95352130cf47e2c92cc` (2026-10-30, release 4.19.9)
- License: MIT. The upstream `LICENSE` is copied unchanged into this directory and must stay with any copy.
- License check: `LICENSE` at the pinned commit read on 2026-10-31; GitHub reports `mit`.
- Names: upstream `TRADEMARKS.md` asks derived work not to present itself as "GEO Optimizer" or "GeoReady".
  This skill is named `geo-audit` and describes itself as based on GEO Optimizer.

## What was taken and what changed

- Adapted from upstream `SKILL.md`: the audit workflow, AI crawler tiers, score categories, Google
  readiness checks and the `geo audit` CLI usage.
- Not vendored: the Python package source, upstream reference files, hosted-service links and the
  upstream "allow all AI bots" robots.txt template (this repo requires an owner-selected per-vendor policy).
- Changed: audit-only scope (no `geo fix --apply`), llms.txt and JSON-LD treated as hygiene with cited
  evidence, outputs handed to the website workflow's improvement queue, and a thin wrapper that reports
  `tool_unavailable` instead of installing anything.

## Installing the pinned CLI (never globally)

```bash
uv venv .cache/geo-audit-venv
uv pip install --python .cache/geo-audit-venv/bin/python \
  "geo-optimizer-skill @ git+https://github.com/Auriti-Labs/geo-optimizer-skill@7ecec864690ee430e954a95352130cf47e2c92cc"
export GEO_AUDIT_BIN="$PWD/.cache/geo-audit-venv/bin/geo"
```

Refresh: read the new upstream `LICENSE`, diff upstream `SKILL.md`, update the commit here and in
`scripts/geo_audit.py`, then rerun `python3 -m pytest tests/test_geo_audit.py`.
