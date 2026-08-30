# FAL asset workflow

Use the repository-level shared `scripts/fal_assets.py` adapter only at build time. Read `FAL_AI_API_KEY` server-side, never expose it as `NEXT_PUBLIC_*` or ship it in website code. Dry-run the model, prompt, number of variants, maximum cost, dimensions, and retention before confirmation.

Record endpoint/model, request ID, seed, prompt, negative prompt, dimensions, lifecycle headers, local hash, and rights/provenance. Download approved media immediately, validate type/dimensions, optimize into `public/`, and never hotlink temporary FAL URLs. Do not send private customer data or unreleased assets without explicit approval.
