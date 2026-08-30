import { flag } from "flags/next";

export type CtaVariant = "control" | "treatment";

export const primaryCtaVariant = flag<CtaVariant>({
  key: "primary_cta_label",
  description: "One-variable CTA copy experiment; inactive by default.",
  options: [
    { value: "control", label: "Request a visit" },
    { value: "treatment", label: "Get a clear repair plan" },
  ],
  defaultValue: "control",
  decide: async (): Promise<CtaVariant> => "control",
});

export async function resolveCtaVariant(previewOverride?: string): Promise<CtaVariant> {
  // Query overrides are preview/test-only. Production remains control until an
  // approved provider allocation replaces the deterministic decide function.
  if (process.env.VERCEL_ENV !== "production" && (previewOverride === "control" || previewOverride === "treatment")) {
    return previewOverride;
  }
  return primaryCtaVariant();
}
