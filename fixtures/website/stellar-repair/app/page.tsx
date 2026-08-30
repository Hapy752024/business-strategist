import { ExperimentCta } from "./experiment-cta";
import { FlagValues } from "flags/react";
import { resolveCtaVariant } from "../lib/flags";

const proof = ["Clear fixed-price scope", "Named specialist before arrival", "Photo-backed completion record"];

export default async function Home({ searchParams }: { searchParams: Promise<{ variant?: string | string[] }> }) {
  const requested = (await searchParams).variant;
  const variant = await resolveCtaVariant(Array.isArray(requested) ? requested[0] : requested);
  return (
    <main>
      <FlagValues values={{ primary_cta_label: variant }} />
      <a className="skip" href="#request">Skip to request</a>
      <header><p className="eyebrow">STELLAR / HOME REPAIR</p><nav aria-label="Primary"><a href="#process">How it works</a><a href="#proof">Why Stellar</a><a className="nav-cta" href="#request">Request a visit</a></nav></header>
      <section className="hero" aria-labelledby="hero-title">
        <div><p className="kicker">For homes that deserve a cleaner finish</p><h1 id="hero-title">The clearest way to get small repairs done properly.</h1><p className="lede">Stellar pairs considered craft with an exact scope before work begins—so your home feels looked after, not processed.</p><div className="actions"><ExperimentCta variant={variant} /><a className="secondary" href="#proof">See the standard</a></div></div>
        <aside className="signature" aria-label="Stellar quality signal"><span>01</span><strong>Measured repair.<br />Visible care.</strong><p>Every finish is documented before we leave.</p></aside>
      </section>
      <section id="proof" className="proof" aria-labelledby="proof-title"><p className="eyebrow">WHAT MAKES THE DIFFERENCE</p><h2 id="proof-title">Confidence comes from specificity.</h2><ul>{proof.map((item) => <li key={item}>{item}</li>)}</ul></section>
      <section id="process" className="process" aria-labelledby="process-title"><p className="eyebrow">A CALMER PROCESS</p><h2 id="process-title">Three deliberate steps.</h2><ol><li><strong>Describe the repair</strong><span>Share a photo and the outcome you want.</span></li><li><strong>Confirm the scope</strong><span>Receive a clear plan before we arrive.</span></li><li><strong>Keep the record</strong><span>See what was completed and how to care for it.</span></li></ol></section>
      <section id="request" className="request" aria-labelledby="request-title"><p className="eyebrow">START WITH A CLEARER PLAN</p><h2 id="request-title">Tell us what needs attention.</h2><p>No account, payment, or submission is required in this fixture.</p><button type="button" aria-describedby="request-note">Request a visit</button><small id="request-note">Demo interaction only — no data is sent.</small></section>
      <footer><span>© Stellar Repair</span><a href="#request">Accessibility</a></footer>
    </main>
  );
}
