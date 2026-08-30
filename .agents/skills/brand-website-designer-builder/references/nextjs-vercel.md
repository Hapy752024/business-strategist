# Next.js and Vercel

- Resolve `next@latest` stable at scaffold time and pin exact versions; reject canary/RC/beta.
- Use App Router, TypeScript, server components by default, `next/font`, `next/image`, metadata, sitemap, and robots where applicable.
- Run locked install, lint, type-check, tests, and `next build` in GitHub CI.
- Connect a user-selected GitHub repository to Vercel only with authorization. Review the immutable Preview deployment before protected-branch production.
- Keep secrets in Vercel settings or local environment, never Git. The default site has no runtime FAL dependency.
- Record Preview/Production/rollback state with `python3 scripts/brand/release_manifest.py <website-manifest> --status preview|production|rolled_back --commit <sha> --url <https-url>`. Preview requires a passing build. Production requires all QA fields to pass, `--confirm-production`, and recorded `--github-repo`, `--github-branch`, and `--vercel-project`. The command atomically records state only; it never deploys or changes traffic.
