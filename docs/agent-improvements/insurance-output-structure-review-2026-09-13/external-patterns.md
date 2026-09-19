# External patterns for agent output organization

Review date: 2026-09-13. Initial retrieval: web search of official agent-project documentation and repositories. These are analogues, not evidence that a layout has been tested with this founder or with insurance opportunity portfolios. Publication dates are not inferred from crawl dates.

Firecrawl's requested search returned HTTP 402; the user was asked about top-up versus the available web tool. An already-issued web search returned the references below. No Firecrawl page content was used and no additional provider request was issued after the pause. The returned material supports the bounded analogies in this review; unestablished implementation details remain explicitly limited below.

## 1. GitHub Spec Kit: umbrella roadmap and independent sub-specifications

Source: https://github.com/github/spec-kit/blob/main/docs/concepts/spec-of-specs.md — official project documentation, retrieved 2026-09-13.

Observed: its decomposition approach uses an overarching roadmap plus smaller independently specified features. Each child runs its own specify/plan/tasks/implement cycle; the roadmap records paths and statuses. The documentation warns that this is the highest-overhead approach and recommends lighter options first.

Transfer: an insurance umbrella can compare research cases while each case retains its own question, evidence assessment and next action. This supports proposal B's physical-case option and proposal A/C's restraint about premature full decomposition.

Limit: software feature decomposition does not solve overlapping customer evidence or prove business validation. Independent cycles need an explicit scope contract in this repo; they cannot be created just by copying a folder tree.

## 2. GitHub Spec Kit: explicit project and feature scopes

Source: https://github.com/github/spec-kit/blob/main/docs/guides/monorepo.md — official project documentation, retrieved 2026-09-13.

Observed: each directory-scoped member project has its own configuration and specifications. Project selection and feature selection are distinct; invalid explicit project destinations fail rather than falling back to the repository root. A shared Git repository still has a shared branch namespace.

Transfer: separate umbrella and case identity. If scoped case execution is added, resolve the destination before dispatch and reject unknown IDs instead of silently writing to shared research.

Limit: separate member projects are a software architecture analogy. Their independence is excessive for every language cohort in one venture. A directory's existence does not establish independent authority here.

## 3. BMad Method: bounded artifacts for different planning questions

Sources: https://docs.bmad-method.org/cs/plan/choose-a-planning-path/ and https://docs.bmad-method.org/cs/plan/plan-inside-an-organization/ — official documentation, retrieved 2026-09-13.

Observed in retrieved excerpts: brainstorming, cited research, brief/PRFAQ, and specifications have different deliverables. The planning-path guidance calls for only the preparation the project needs. Organization guidance describes shared architectural decisions coordinating separately developed epics and a change-of-course process for material plan changes.

Transfer: distinguish an investigated idea, a cited research report and an execution specification. Keep a concise umbrella comparison and separately scoped detail; do not create all downstream workstreams for every brainstormed variant.

Limit: the initial retrieval does not establish exact configurable output-directory behavior. Do not attribute a specific insurance folder tree or automatic evidence reuse to BMad. Two pages from one project are one external implementation family, not independent corroborations.

## 4. GPT Researcher: report-oriented research runs

Source: https://github.com/assafelovic/gpt-researcher/blob/main/README.md — official repository, retrieved 2026-09-13.

Observed: the multi-agent workflow describes topic research from planning through publication and exports a report in several formats.

Transfer: preserve dated research runs and their report outputs separately from the current comparison of ideas. A run is useful provenance but is not a permanent idea identity.

Limit: the retrieved README does not establish a durable portfolio hierarchy, per-hypothesis gates or exact on-disk paths. Treat it as a run/report pattern, not proof that it already solves this user's problem.

## Synthesis for reviewers

Three implementation families provide useful partial patterns: Spec Kit offers scope and decomposition; BMad offers proportionate planning artifacts; GPT Researcher offers bounded research reports. None of the retrieved sources demonstrates the complete business-idea portfolio solution needed here. Our proposed idea registry, applicability bindings and treatment of overlapping variants are design inferences informed by the local failures, not copied proven behavior.
