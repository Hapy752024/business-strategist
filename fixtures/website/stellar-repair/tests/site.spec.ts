import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("renders deterministic control and server-side preview treatment", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator('[data-experiment="primary_cta_label"]')).toHaveAttribute("data-variant", "control");
  await expect(page.locator('[data-experiment="primary_cta_label"]')).toHaveText("Request a visit");
  await page.goto("/?variant=treatment");
  await expect(page.locator('[data-experiment="primary_cta_label"]')).toHaveAttribute("data-variant", "treatment");
  await expect(page.locator('[data-experiment="primary_cta_label"]')).toHaveText("Get a clear repair plan");
});

test("has no serious accessibility violations and exposes keyboard focus", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter((item) => item.impact === "serious" || item.impact === "critical")).toEqual([]);
  for (let index = 0; index < 10; index += 1) {
    await page.keyboard.press("Tab");
    if (await page.locator('[data-experiment="primary_cta_label"]:focus').count()) break;
  }
  await expect(page.locator('[data-experiment="primary_cta_label"]')).toBeFocused();
});

test("stays within a small fixture performance budget", async ({ page }) => {
  await page.addInitScript(() => {
    (window as typeof window & { __cls?: number }).__cls = 0;
    new PerformanceObserver((entries) => {
      for (const entry of entries.getEntries() as (PerformanceEntry & { value: number; hadRecentInput: boolean })[]) {
        if (!entry.hadRecentInput) (window as typeof window & { __cls?: number }).__cls! += entry.value;
      }
    }).observe({ type: "layout-shift", buffered: true });
  });
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  const metrics = await page.evaluate(() => ({
    cls: (window as typeof window & { __cls?: number }).__cls ?? 0,
    transferBytes: performance.getEntriesByType("resource").reduce((sum, entry) => sum + ((entry as PerformanceResourceTiming).transferSize || 0), 0),
  }));
  expect(metrics.cls).toBeLessThanOrEqual(0.1);
  expect(metrics.transferBytes).toBeLessThanOrEqual(750_000);
});

for (const viewport of [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1440, height: 1000 },
]) {
  test(`is responsive at ${viewport.name}`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await testInfo.attach(`${viewport.name}-page`, { body: await page.screenshot({ fullPage: true }), contentType: "image/png" });
  });
}
