import type { CtaVariant } from "../lib/flags";

const labels: Record<CtaVariant, string> = {
  control: "Request a visit",
  treatment: "Get a clear repair plan",
};

export function ExperimentCta({ variant }: { variant: CtaVariant }) {
  return (
    <a className="primary" href="#request" data-experiment="primary_cta_label" data-variant={variant}>
      {labels[variant]}
    </a>
  );
}
