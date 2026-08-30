# FAL asset workflow

Use the repository-level shared `scripts/fal_assets.py` adapter only at build time. Read `FAL_AI_API_KEY` server-side, never expose it as `NEXT_PUBLIC_*` or ship it in website code. Dry-run the model, prompt, number of variants, maximum cost, dimensions, and retention before confirmation.

Record endpoint/model, request ID, seed, prompt, negative prompt, dimensions, lifecycle headers, local hash, and rights/provenance. Finalize a completed response with `python3 scripts/brand/finalize_fal_assets.py --response <result.json> --output-dir <local-assets> --record <asset-record.json> --expected-width <px> --expected-height <px>`. It immediately downloads trusted FAL media, validates size/MIME/dimensions, and writes URL-free local records. Optimize approved files into `public/`; never hotlink temporary URLs. Do not send private customer data or unreleased assets without explicit approval.
