"use client";

import { useEffect, useState } from "react";

type Variant = "control" | "treatment";

const labels: Record<Variant, string> = {
  control: "Request a visit",
  treatment: "Get a clear repair plan",
};

function resolveVariant(): Variant {
  const requested = new URLSearchParams(window.location.search).get("variant");
  if (requested === "control" || requested === "treatment") return requested;
  const saved = window.localStorage.getItem("stellar-repair-cta-variant");
  if (saved === "control" || saved === "treatment") return saved;
  return Math.random() < 0.5 ? "control" : "treatment";
}

export function ExperimentCta() {
  const [variant, setVariant] = useState<Variant>("control");

  useEffect(() => {
    const assigned = resolveVariant();
    window.localStorage.setItem("stellar-repair-cta-variant", assigned);
    setVariant(assigned);
  }, []);

  return <a className="primary" href="#request" data-experiment="primary_cta_label" data-variant={variant}>{labels[variant]}</a>;
}
