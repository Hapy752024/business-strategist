# Brand designer import path map

| Source | Destination | Treatment |
| --- | --- | --- |
| `/mnt/c/coding/general/brand_designer/.agents/skills/brand-*` | `.agents/skills/brand-*` | Imported skill directories; entrypoints compacted to a 30-line router and full procedures retained in `references/workflow.md`. |
| `/mnt/c/coding/general/brand_designer/.agents/skills/setup-multiharness-project` | `.agents/skills/setup-multiharness-project` | Imported unchanged in scope, with the same compact-router treatment. |
| `/mnt/c/coding/general/brand_designer/tests` | `tests/brand_designer` | Copied and adapted to the destination root; filenames normalized for pytest discovery. |
| `/mnt/c/coding/general/brand_designer/scripts/sync-mcp-config.py` | `scripts/sync-brand-mcp-config.py` | Copied as an explicit, non-overwriting migration utility. |
| Source `brand-projects/` outputs | Not moved | Historical outputs remain in the source repository; new work is linked through `projects/` and optional `brand-projects/` workspaces. |

The business strategist remains the routing owner. Branding is independently invocable, while a validated business can provide an explicit immutable `business-to-brand.json` snapshot. Website implementation is a separate preference-led skill and does not force research.
