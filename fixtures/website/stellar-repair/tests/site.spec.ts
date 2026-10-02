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

test("primary CTA completes the local demo form and server validates without echoing input", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-experiment="primary_cta_label"]').click();
  await expect(page.getByRole("heading", { name: "Tell us what needs attention." })).toBeVisible();
  await page.getByLabel("What needs repair?").fill("A loose kitchen cabinet door");
  await page.getByLabel("Email for a reply").fill("fixture@example.test");
  await page.getByRole("button", { name: "Send demo request" }).click();
  await expect(page.getByRole("status")).toContainText("No service request was sent or saved.");

  const invalid = await page.request.post("/api/demo-request", { multipart: { repair: "short", email: "bad" } });
  expect(invalid.status()).toBe(400);
  const body = await invalid.json();
  expect(JSON.stringify(body)).not.toContain("bad");
});

test("keeps form available through pending state, failure, and retry", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("What needs repair?").fill("A loose kitchen cabinet door");
  await page.getByLabel("Email for a reply").fill("fixture@example.test");
  let calls = 0;
  await page.route("**/api/demo-request", async (route) => {
    calls += 1;
    if (calls === 1) { await new Promise((resolve) => setTimeout(resolve, 100)); await route.abort("failed"); }
    else await route.continue();
  });
  await page.getByRole("button", { name: "Send demo request" }).click();
  await expect(page.getByRole("button", { name: "Sending…" })).toBeDisabled();
  await expect(page.getByRole("status")).toContainText("please retry");
  await expect(page.getByLabel("What needs repair?")).toHaveValue("A loose kitchen cabinet door");
  await page.getByRole("button", { name: "Send demo request" }).click();
  await expect(page.getByRole("status")).toContainText("No service request was sent or saved.");
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
