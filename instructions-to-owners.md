# Instructions to owners

What only a human can do for this setup and for the Italy for Retirees site, how to do it, and in what order. Agents never send mail, create accounts, buy links, deploy or spend on ads; every item below is yours. Written 31 October 2026. Secrets go in `~/.secrets` (or the shell that starts Claude Code), never in this repo, which is public.

## To-do recap

Do in this order. Time is a rough estimate.

| # | Task | Time | Blocks |
|---|---|---|---|
| 1 | Push the repo: `git push origin main` | 1 min | nothing, but 112 unpushed commits |
| 2 | Clean `.claude/settings.local.json` (remove 5 stale MCP servers; decide `enableAllProjectMcpServers`) | 2 min | the one failing test |
| 3 | Add `export REDDIT_USERNAME=<your Reddit username>` to `~/.secrets` | 1 min | polite Reddit requests |
| 4 | Website: commit and deploy the Semrush fixes in `projects/us-retirees-italy/web-site` | 10 min | sitemap and llms.txt warnings |
| 5 | Verify the site in Google Search Console, submit the sitemap, request indexing | 20 min | knowing whether pages are indexed at all |
| 6 | Subscribe to Source of Sources, Qwoted (free) and Featured (free) with your own account; label the mails `press-requests` in Gmail | 15 min | journalist-request step |
| 7 | Authorise the Gmail connector in Claude Code (read + drafts) | 5 min | pitch drafts and request triage |
| 8 | Pick 5 prospects from the pre-check list and tell the agent; send the pitches it drafts; record each send | 1 h | first real links |
| 9 | Seed your own photos on Unsplash/Pexels/Flickr with a credit link (only photos you took) | 30 min once | image-credit links |
| 10 | Approval signing key for marketing actions (before any campaign) | 10 min | signed approvals |
| 11 | Postiz on GzaraNet (only when scheduled social posts start) | 1-2 h | social scheduling |
| 12 | Meta token (only when a paid campaign is near) | 15 min | paused-campaign creation |
| 13 | Decide: statistics page and 7%-town checker for the site (agent plans from a brief) | decision | linkable content |
| 14 | Add a "How did you hear about us?" question (with an AI-assistant option) to the booking flow; when analytics is on, add the AI-referrer channel | 30 min | AI attribution |
| Monthly | Re-run competitor backlinks, `diff`, `link_ledger check`, read the ledger report | 20 min | link gap and lost links |

## 1. Repository

**Push.** From `/home/habib/work/general/business-strategist`: `git push origin main`. This publishes old commits that contain third-party text (you accepted this).

**Local MCP settings.** Open `.claude/settings.local.json`. In `enabledMcpjsonServers` remove `filesystem`, `sqlite`, `google-trends`, `reddit`, `youtube-transcript` (no longer defined in `.mcp.json`). Then set `"enableAllProjectMcpServers": false` and list only the servers you want (for example `brave-search`, `firecrawl`, `dialog-mcp`, `apify`, `dataforseo`); `true` switches on every project server, including Meta Ads, Postiz and Google Ads. Afterwards `python3 -m pytest -q tests/test_claude_hooks.py` should pass.

**Reddit.** Registration of the app with Reddit did not work for an app-only (no user login) app; skip it. Add `export REDDIT_USERNAME=<your Reddit username>` to `~/.secrets` so requests identify as `python:business-strategist-hapy:0.1 (by /u/<username>)`. When Reddit cuts the public API (from 12 January 2027 for unregistered apps, March 2027 for all), the collectors fall back to Apify, ScrapeCreators and Arctic Shift on their own; a cutoff is recorded as a coverage gap, never as "no demand".

## 2. Website: technical SEO

Your understanding is right: the technical side is hygiene that keeps the content eligible; the content earns the ranking. The site repo is `projects/us-retirees-italy/web-site` (its own git).

**Deploy the Semrush fixes.** Uncommitted there: `app/sitemap.ts` (home URL with trailing slash, `/updates` removed), `app/updates/page.tsx` (noindex while signup is closed), `qa/routes.json`, `public/llms.txt`. All 59 launch tests pass.

```bash
cd projects/us-retirees-italy/web-site
git add app/sitemap.ts app/updates/page.tsx qa/routes.json public/llms.txt
git commit -m "seo: sitemap home URL, noindex placeholder updates page, add llms.txt"
# then deploy as you usually do
```

**What the remaining Semrush items mean.** Text-to-HTML ratio 1-7.5%: caused by Next.js page data and the inlined stylesheet (`inlineCss: true`, a deliberate speed choice). Not a Google ranking factor; leave it unless a speed test shows inlining no longer helps. 11 external 403s: Italian consulate pages that block Semrush's crawler; they load in a browser; keep them. 8 blocked pages: your noindex pages, correct. Low word count and single-link pages: noindexed or canonicalised, ignore.

**Search Console.** Verify `https://www.italyforretirees.com` (DNS or HTML-file method; only the domain owner can), submit `/sitemap.xml`, request indexing for the home page, `/guide` and the newest guides. A 30 October check found no indexed pages. Monthly: export the Links report (CSV) and import it: `python3 scripts/marketing/earned_media.py import-links <links.csv> --source-column <col> --target-column <col> --property https://www.italyforretirees.com --exported-at <date> --out <file>` then `python3 scripts/marketing/link_ledger.py --base projects/us-retirees-italy import-links <file>`.

**Keep doing.** HTTPS, security headers, mobile layout and speed are already tested in the site's launch contract; re-run `npx playwright test tests/launch.spec.ts` after changes.

## 3. Website: content that earns links

Agents now plan this by default (`references/linkable-assets.md`): for each stage of the customer journey, one statistics page, calculator or checklist, built from official sources with dates and a refresh owner. Your decisions:

- **Statistics page** "Retiring in Italy: the numbers (2026)": costs by region, visa income bar, pension taxation, healthcare, expat counts, each with source and date. Agent drafts the public-resource brief; you approve before it is built.
- **Second calculator**: "Does my town qualify for the 7% pensioner regime?" (the existing `/check` covers the visa income bar). Same path: brief, approval, build, tests.
- **Your own photos**: upload photos you took of Italian towns to Unsplash, Pexels or Flickr with a credit link to the site. Do not re-upload licensed stock (see the site's image-credits page). Later the agent can reverse-image-search them to ask for missing credits.

**AI visibility measurement (item 14).** The one reliable signal is self-reported: ask "How did you hear about us?" on `/book` with options including "ChatGPT or another AI assistant". If analytics is ever enabled, add a channel for AI referrers (chatgpt.com, perplexity, gemini.google.com, copilot.microsoft.com, claude.ai); several assistants send no referrer, so it undercounts. Check robots.txt does not block GPTBot, OAI-SearchBot, ClaudeBot or PerplexityBot unless you decide to, and look at 404s that keep receiving AI referrals: those are made-up URLs to redirect.

## 4. Backlinks: the routine

Data for the Italy project is at `projects/us-retirees-italy/marketing/earned_media/`:

- `competitor-backlinks-2026-10-31/candidates.json`: 202 domains linking to four competitors; 80 flagged (69 are link sellers; the competitors buy links), 122 clean.
- `prequalify-2026-10-31/prequalified.json`: first 40 prospects fetched; 25 live pages still carry the competitor link, with the quoted sentence and contact routes. Strongest: The Local Italy, Financial Planning, ThinkAdvisor (expert quotes); Badass Digital Nomads, Traveling with Kristin, A New Life in Italy (podcast guests); Investropa, Expat Focus (resource citations). Small "family reunification visa" blogs with generic bylines are paid content farms; expect a price.
- `link-ledger.json` and `link-ledger.md`: 122 prospects, 80 rejected, 0 live.

**Your weekly loop (about 1 hour).**
1. Pick up to 5 prospects from `prequalified.json` and tell the agent which. It runs `earned-media-builder` preparation and writes each pitch (recipient, page, exact sentence to add, why it helps their reader).
2. Send the pitch from your own mailbox. Record it: `python3 scripts/marketing/link_ledger.py --base projects/us-retirees-italy set --source <their page URL> --stage pitched --target <your page URL> --note "email 1"`.
3. One follow-up after 7 days, recorded the same way (`--stage pitched --note "follow-up"`). Never a third.
4. Replies: `--stage promised` or `--stage declined`. Live is never set by hand; `python3 scripts/marketing/link_ledger.py --base projects/us-retirees-italy check --max 20` verifies promised and live rows and moves them.
5. `python3 scripts/marketing/link_ledger.py --base projects/us-retirees-italy report --markdown` shows counts, overdue follow-ups and lost links.

**Journalist requests (one reply a day).** Subscribe with your own account to Source of Sources (free newsletter), Qwoted (free tier) and Featured (free tier). Let the mails land in Gmail under a `press-requests` label. Once the Gmail connector is authorised in Claude Code, the agent can filter them daily to retirement, Italy, expat and money topics and put one drafted answer, with a sourced number from your guides, in your drafts. You check and send. Agents do not log in to these platforms.

**Podcasts.** Three podcasts in the prospect list host relocation guests. Pitching yourself as a guest is a human action; the agent drafts the pitch and records the show-notes link once live.

**Monthly.**
```bash
python3 scripts/marketing/competitor_backlinks.py --competitor whywaititaly.com --competitor smartmoveitaly.com --competitor italyblueprint.com --competitor mitosrelocation.com --own italyforretirees.com --out projects/us-retirees-italy/marketing/earned_media/competitor-backlinks-<YYYY-MM-DD>
python3 scripts/marketing/link_prospects.py diff --previous <last run>/candidates.json --current <new run>/candidates.json
python3 scripts/marketing/link_ledger.py --base projects/us-retirees-italy import-candidates <new run>/candidates.json
```
About 0.15 USD per run (DataForSEO, pre-authorised research spend).

**Do not.** Buy links, join link exchanges or "backlink networks", pay for guest posts without a `sponsored` tag, use PBNs or paid indexing services. Your competitors do; it is why 69 of their 202 linking domains are link sellers.

## 5. Accounts and credentials

**Gmail connector (steps 6-7).** In Claude Code, authorise the Gmail connector when asked (read mail, create drafts). This unlocks pitch drafts in your mailbox and journalist-request triage. Nothing is sent by the agent.

**Approval signing key (step 10).** Needed before any marketing execution (campaign creation, platform writes). In your own terminal, never through Claude:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/marketing_approval -C marketing-approval      # set a passphrase; never ssh-add this key
mkdir -p ~/.config/business-strategist
echo "<principal> namespaces=\"marketing-approval\" $(cat ~/.ssh/marketing_approval.pub)" >> ~/.config/business-strategist/allowed_signers
sudo chown root:root ~/.config/business-strategist ~/.config/business-strategist/allowed_signers
sudo chmod 0755 ~/.config/business-strategist && sudo chmod 0644 ~/.config/business-strategist/allowed_signers
```
`<principal>` is the name you will pass as `--by` when signing (letters, digits, `. _ @ + -`). After the `chown`, changes need `sudo`.

**Postiz (step 11).** Install on GzaraNet, not locally: scheduled posts need an always-on host and the social logins need a public HTTPS callback. Clone `github.com/gitroomhq/postiz-docker-compose`, pin a version tag, set `MAIN_URL`, `FRONTEND_URL`, `NEXT_PUBLIC_BACKEND_URL` and a long `JWT_SECRET`, run behind your reverse proxy on a subdomain, create your account, then set `DISABLE_REGISTRATION=true`. Connect channels in the UI, copy the API key from Settings > Developers > Public API, and on your machine export `POSTIZ_BASE_URL` and `POSTIZ_API_KEY`. Back up Postgres and uploads.

**Meta (step 12).** Only when a paid campaign is close: in Business Settings create an Employee-role system user (Admin tokens are unsupported), generate a token with `ads_read` and `ads_management`, export it as `META_ACCESS_TOKEN`. Campaigns are created paused with a spend cap (Meta minimum about 100 USD). Ad spend needs your explicit approval each time.

**ScrapeCreators (optional).** A second paid Reddit fallback besides Apify; `SCRAPE_CREATORS_API_KEY` in `~/.secrets`. Not required.

## 6. What the agents now do without you

- Evidence-first research with early desk steps (search journey, competitor content, keyword volumes, social topics) and labelled fallbacks; one hard rule: no final recommendation without a claim challenge.
- Competitor backlink prospecting with link-seller flags; prospect pre-checks with quoted context and contact routes; unlinked-mention search (case-sensitive; the brand name is also an ordinary phrase, so read the results); month-to-month link-gap diff.
- A per-project link ledger where only a verified page check can mark a link live or lost.
- Planning of statistics pages, calculators and checklists per journey stage from the wired statistics sources.

Everything that touches other people (mail, accounts, publication, payment) stays with you.
