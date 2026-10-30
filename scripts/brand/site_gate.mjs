#!/usr/bin/env node
// Browser step of the site gate (orchestrated by scripts/brand/site_gate.py).
// Read-only: loads each route, runs axe-core, and checks a small deterministic SUBSET of the
// Vercel web interface guidelines that is observable in the rendered DOM. Rules are written
// here; nothing is fetched at gate time. Guideline source:
// https://github.com/vercel-labs/web-interface-guidelines (README, reviewed 2026-10-30).
// Dependencies resolve from scripts/brand/package.json (npm ci in scripts/brand).
import {createRequire} from 'node:module';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

const [baseArg, routesPath, outPath, toolingDir] = process.argv.slice(2);
if (!baseArg || !routesPath || !outPath) {
  console.error('Usage: node scripts/brand/site_gate.mjs <base-url> <routes.json> <out.json> [tooling-dir]');
  process.exit(2);
}
const write = data => writeFileSync(outPath, JSON.stringify(data, null, 2));
const require = createRequire(toolingDir ? resolve(toolingDir, 'package.json') : import.meta.url);
let chromium, AxeBuilder;
try {
  ({chromium} = require('playwright'));
  const axe = require('@axe-core/playwright');
  AxeBuilder = axe.AxeBuilder || axe.default || axe;
} catch (error) {
  write({tool_unavailable: `playwright/@axe-core/playwright not installed in the tooling directory: ${error.message.split('\n')[0]}`});
  process.exit(0);
}

const GUIDELINE_SUBSET = {
  'named-controls': 'Accessible content / Icon-only buttons are named',
  'labels-everywhere': 'Labels everywhere',
  'images-alt': 'Accessible content (images carry alt text or are marked decorative)',
  'no-positive-tabindex': 'Keyboard works everywhere',
  'respect-zoom': 'Respect zoom (viewport meta present, zoom not disabled)',
  'mobile-input-size': 'Mobile input size (>=16px unless maximum-scale=1)',
  'no-horizontal-overflow': 'Responsive coverage / No excessive scrollbars (375px wide)',
};

const domRules = () => {
  const text = el => (el?.textContent || '').replace(/\s+/g, ' ').trim();
  const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length) && getComputedStyle(el).visibility !== 'hidden';
  const label = el => {
    const sel = el.tagName.toLowerCase() + (el.id ? `#${el.id}` : '') + (el.getAttribute('name') ? `[name="${el.getAttribute('name')}"]` : '');
    return sel.slice(0, 120);
  };
  const named = el => {
    if ((el.getAttribute('aria-label') || '').trim()) return true;
    const ids = (el.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
    if (ids.some(id => text(document.getElementById(id)))) return true;
    if (el.labels && [...el.labels].some(l => text(l))) return true;
    if (['submit', 'button', 'reset'].includes(el.type) && el.tagName === 'INPUT' && (el.value || '').trim()) return true;
    if (el.tagName !== 'INPUT' && el.tagName !== 'SELECT' && el.tagName !== 'TEXTAREA' && text(el)) return true;
    if ([...el.querySelectorAll('img[alt]')].some(i => i.alt.trim())) return true;
    return !!(el.getAttribute('title') || '').trim();
  };
  const issues = [];
  const controls = [...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,[role=button],[role=link]')].filter(visible);
  for (const el of controls) if (!named(el)) issues.push({rule: 'named-controls', target: label(el)});
  const fields = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]),select,textarea')].filter(visible);
  for (const el of fields) {
    const has = (el.labels && el.labels.length) || (el.getAttribute('aria-label') || '').trim() || (el.getAttribute('aria-labelledby') || '').trim();
    if (!has) issues.push({rule: 'labels-everywhere', target: label(el)});
  }
  for (const img of document.images) if (!img.hasAttribute('alt')) issues.push({rule: 'images-alt', target: (img.getAttribute('src') || 'img').slice(0, 120)});
  for (const el of document.querySelectorAll('[tabindex]')) if (Number(el.getAttribute('tabindex')) > 0) issues.push({rule: 'no-positive-tabindex', target: label(el)});
  const viewport = document.querySelector('meta[name="viewport"]')?.content || '';
  if (!viewport) issues.push({rule: 'respect-zoom', target: 'meta[name=viewport] missing'});
  else if (/user-scalable\s*=\s*(no|0)\b/i.test(viewport)) issues.push({rule: 'respect-zoom', target: `viewport disables zoom: ${viewport}`});
  return {issues, viewport, maxScaleOne: /maximum-scale\s*=\s*1(\.0+)?\b/i.test(viewport)};
};

const mobileRules = maxScaleOne => {
  const issues = [];
  if (document.documentElement.scrollWidth > innerWidth + 1) issues.push({rule: 'no-horizontal-overflow', target: `scrollWidth ${document.documentElement.scrollWidth} > ${innerWidth}`});
  if (!maxScaleOne) {
    for (const el of document.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]),select,textarea')) {
      const size = parseFloat(getComputedStyle(el).fontSize);
      if (size < 16) issues.push({rule: 'mobile-input-size', target: `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''} font-size ${size}px`});
    }
  }
  return issues;
};

const result = {axe: {routes: []}, guidelines: {subset: GUIDELINE_SUBSET, source: 'https://github.com/vercel-labs/web-interface-guidelines', routes: []}};
let browser;
try {
  const base = new URL(baseArg);
  const routes = JSON.parse(readFileSync(routesPath, 'utf8'));
  if (!Array.isArray(routes) || !routes.length) throw Error('nonempty route list required');
  try {
    browser = await chromium.launch({headless: true});
  } catch (error) {
    write({tool_unavailable: `Playwright Chromium could not launch: ${error.message.split('\n')[0]}`});
    process.exit(0);
  }
  const context = await browser.newContext({viewport: {width: 1280, height: 900}});
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  for (const path of routes) {
    const url = new URL(path, base);
    if (url.origin !== base.origin) throw Error(`route leaves the audited origin: ${path}`);
    await page.setViewportSize({width: 1280, height: 900});
    const response = await page.goto(url.href, {waitUntil: 'load'});
    const status = response ? response.status() : null;
    const axe = await new AxeBuilder({page}).analyze();
    result.axe.routes.push({path, status, violations: axe.violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length})),
      axe_version: axe.testEngine?.version || null});
    const dom = await page.evaluate(domRules);
    await page.setViewportSize({width: 375, height: 812});
    await page.waitForTimeout(100);
    const mobile = await page.evaluate(mobileRules, dom.maxScaleOne);
    result.guidelines.routes.push({path, status, issues: [...dom.issues, ...mobile]});
  }
} catch (error) {
  result.error = error.message.split('\n')[0];
} finally {
  if (browser) await browser.close();
}
write(result);
