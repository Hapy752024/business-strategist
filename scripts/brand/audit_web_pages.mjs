#!/usr/bin/env node
// Read-only browser audit. Dependencies come from the site's own dev environment.
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

const [project, baseArg, inventoryPath] = process.argv.slice(2);
if (!project || !baseArg || !inventoryPath) {
  console.error('Usage: node scripts/brand/audit_web_pages.mjs <next-project> <base-url> <routes.json>');
  process.exit(2);
}
const errors = [], pages = [];
let browser;
const safeUrlLabel = raw => {
  try {
    const url = new URL(raw);
    return `${url.origin}${url.pathname}`;
  } catch {
    return '[invalid URL]';
  }
};
try {
  const base = new URL(baseArg);
  if (!['http:', 'https:'].includes(base.protocol) || base.username || base.password || base.search || base.hash || base.pathname !== '/') throw Error('base must be a credential-free HTTP(S) origin');
  const inventory = JSON.parse(readFileSync(inventoryPath, 'utf8'));
  if (!Array.isArray(inventory) || !inventory.length) throw Error('nonempty route inventory required');
  const seen = new Set();
  const consentRejectRows = inventory.filter(row => row?.consentReject !== undefined);
  if (consentRejectRows.length > 1 || (consentRejectRows.length === 1 && typeof consentRejectRows[0].consentReject !== 'string')) {
    throw Error('at most one route may define a consentReject selector');
  }
  for (const row of inventory) {
    const routeUrl = row && typeof row.path === 'string' ? new URL(row.path, base) : null;
    if (!routeUrl || !row.path.startsWith('/') || row.path.startsWith('//') || routeUrl.origin !== base.origin || routeUrl.search || routeUrl.hash || seen.has(routeUrl.pathname)) throw Error('routes require unique same-origin paths without query strings or fragments');
    if (typeof row.conversion !== 'boolean') throw Error('each route requires explicit conversion boolean');
    const redirectUrl = row.redirect && typeof row.redirect.to === 'string' ? new URL(row.redirect.to, base) : null;
    if (row.redirect && (!Number.isInteger(row.redirect.status) || ![301,302,303,307,308].includes(row.redirect.status) || !redirectUrl || redirectUrl.origin !== base.origin || redirectUrl.search || redirectUrl.hash)) throw Error('redirect needs expected status and same-origin destination without query strings or fragments');
    if (row.conversion && (!row.cta || !row.stickyCta)) throw Error('conversion routes require cta and stickyCta selectors');
    seen.add(routeUrl.pathname);
  }
  const require = createRequire(resolve(project, 'package.json'));
  const {chromium} = require('playwright');
  browser = await chromium.launch({headless: true});
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const resourceErrors = new Set();
  page.on('response', response => { if (response.status() >= 400) resourceErrors.add(`${response.status()} ${safeUrlLabel(response.url())}`); });
  page.on('requestfailed', request => resourceErrors.add(`request failed ${safeUrlLabel(request.url())}`));
  const localLinks = new Set();
  if (consentRejectRows.length) {
    await page.goto(new URL(consentRejectRows[0].path, base).href, {waitUntil: 'load'});
    const reject = page.locator(consentRejectRows[0].consentReject).first();
    if (!await reject.isVisible()) errors.push('configured consent reject control is not visible');
    else await reject.click();
  }
  for (const row of inventory) {
    if (row.redirect) {
      const response = await context.request.get(new URL(row.path, base).href, {maxRedirects: 0});
      const location = response.headers().location;
      if (response.status() !== row.redirect.status || !location || new URL(location, new URL(row.path, base)).href !== new URL(row.redirect.to, base).href) errors.push(`${row.path}: redirect status/destination mismatch`);
      continue;
    }
    for (const width of [320, 375, 390, 768, 1440]) {
      await page.setViewportSize({width, height: 900});
      const response = await page.goto(new URL(row.path, base).href, {waitUntil: 'load'});
      if (!response || response.status() !== 200) errors.push(`${row.path}: expected 200`);
      await page.locator('body').waitFor();
      const observed = await page.evaluate(() => ({
        title: document.title.trim(),
        description: document.querySelector('meta[name="description"]')?.content?.trim(),
        og: document.querySelector('meta[property="og:image"]')?.content,
        canonical: document.querySelector('link[rel="canonical"]')?.href,
        overflow: document.documentElement.scrollWidth > innerWidth + 1,
        missingAlt: [...document.images].filter(i => !i.hasAttribute('alt')).length,
        brokenImages: [...document.images].filter(i => i.complete && !i.naturalWidth).length,
        links: [...document.querySelectorAll('a[href]')].map(a => a.href),
      }));
      if (!observed.title) errors.push(`${row.path}: missing title`);
      if (!observed.description) errors.push(`${row.path}: missing description`);
      if (!observed.og) errors.push(`${row.path}: missing OG image`);
      if (!observed.canonical && row.indexable !== false) errors.push(`${row.path}: missing canonical`);
      if (observed.overflow) errors.push(`${row.path}@${width}: overflow`);
      if (observed.missingAlt || observed.brokenImages) errors.push(`${row.path}@${width}: missing alt or broken image`);
      if (width === 1440) pages.push({path: row.path, ...observed, links: undefined});
      for (const href of observed.links) {
        const u = new URL(href);
        if (u.origin !== base.origin || !['http:', 'https:'].includes(u.protocol)) continue;
        if (u.search) {
          errors.push(`${row.path}: internal link contains query parameters and was not fetched: ${u.pathname}`);
          continue;
        }
        if (!seen.has(u.pathname)) {
          errors.push(`${row.path}: internal link target is not inventoried and was not fetched: ${u.pathname}`);
          continue;
        }
        localLinks.add(u.pathname);
      }
      if (row.conversion) {
        const cta = page.locator(row.cta).first();
        const box = await cta.boundingBox();
        if (!await cta.isVisible() || !box || box.y < 0 || box.y + box.height > 900 || !await cta.isEnabled()) errors.push(`${row.path}@${width}: CTA not usable above fold`);
        if (width < 768) {
          await page.evaluate(() => {
            const footerHeight = document.querySelector('footer')?.getBoundingClientRect().height ?? 0;
            const beforeFooter = Math.max(0, document.documentElement.scrollHeight - innerHeight - footerHeight - 24);
            scrollTo(0, Math.min(innerHeight, beforeFooter));
          });
          const sticky = page.locator(row.stickyCta).first();
          const b = await sticky.boundingBox();
          const position = await sticky.evaluate(el => getComputedStyle(el).position);
          if (!await sticky.isVisible() || !await sticky.isEnabled() || !b || b.y < 0 || b.y + b.height > 900 || !['fixed', 'sticky'].includes(position)) errors.push(`${row.path}@${width}: sticky CTA missing after scroll`);
        }
      }
    }
  }
  for (const field of ['title', 'description']) {
    const values = new Map();
    for (const p of pages) {
      if (p[field] && values.has(p[field])) errors.push(`duplicate ${field}: ${values.get(p[field])}, ${p.path}`);
      values.set(p[field], p.path);
    }
  }
  for (const path of localLinks) {
    const response = await context.request.get(new URL(path, base).href, {timeout: 10000});
    if (response.status() >= 400) errors.push(`broken internal link ${response.status()}: ${path}`);
  }
  for (const p of pages) {
    if (p.og) {
      const u = new URL(p.og, base);
      let auditUrl = u.href;
      if (u.origin !== base.origin) {
        let canonicalOrigin;
        try { canonicalOrigin = new URL(p.canonical).origin; } catch {}
        if (u.origin !== canonicalOrigin) {
          errors.push(`${p.path}: external OG requires manual verification (not fetched)`);
          continue;
        }
        // A local preview commonly emits production-origin metadata. Verify the
        // canonical site's own asset through the tested preview deployment.
        auditUrl = new URL(u.pathname + u.search, base).href;
      }
      const response = await context.request.get(auditUrl);
      if (response.status() !== 200 || !response.headers()['content-type']?.startsWith('image/')) errors.push(`${p.path}: OG image unavailable or wrong MIME`);
    }
  }
  const robots = await context.request.get(new URL('/robots.txt', base).href);
  if (robots.status() !== 200 || !/user-agent:/i.test(await robots.text())) errors.push('robots.txt missing or malformed');
  const sitemap = await context.request.get(new URL('/sitemap.xml', base).href);
  if (sitemap.status() !== 200 || !/<(?:urlset|sitemapindex)\b/.test(await sitemap.text())) errors.push('sitemap.xml missing or malformed');
  const missing = await context.request.get(new URL('/__audit_missing_' + Date.now(), base).href);
  if (missing.status() !== 404) errors.push('unknown route does not return 404');
  errors.push(...resourceErrors);
} catch (error) {
  errors.push(error.message);
} finally {
  if (browser) await browser.close();
}
console.log(JSON.stringify({status: errors.length ? 'fail' : 'pass', pages, errors: [...new Set(errors)],
  manual_checks: ['inventory completeness', 'metadata/alt meaning', 'favicon provenance', '404 design', 'sitemap URL coverage', 'robots policy', 'CTA obstruction/keyboard', 'consent network transitions', 'form states', 'legal/contact truth', 'performance via Lighthouse and field data'],
  boundary: 'observed automated checks only; no launch assessment promotion'}, null, 2));
process.exitCode = errors.length ? 1 : 0;
