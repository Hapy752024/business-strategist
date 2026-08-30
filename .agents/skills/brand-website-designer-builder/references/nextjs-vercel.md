# Next.js and Vercel

- Resolve `next@latest` stable at scaffold time and pin exact versions; reject canary/RC/beta.
- Use App Router, TypeScript, server components by default, `next/font`, `next/image`, metadata, sitemap, and robots where applicable.
- Run locked install, lint, type-check, tests, and `next build` in GitHub CI.
- Connect a user-selected GitHub repository to Vercel only with authorization. Review the immutable Preview deployment before protected-branch production.
- Keep secrets in Vercel settings or local environment, never Git. The default site has no runtime FAL dependency.
- Record Preview/Production/rollback state with `python3 scripts/brand/release_manifest.py <website-manifest> --status preview|production|rolled_back --commit <sha>`. Production records require an explicit `--confirm-production`; this records state only and never deploys.
