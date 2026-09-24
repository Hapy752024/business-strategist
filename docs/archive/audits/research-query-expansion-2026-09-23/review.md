# Adversarial review: research query expansion

Date: 23 September 2026. Independent review by the explicitly requested `adversarial_research_review` subagent; reproductions rerun by the parent. No implementation files changed during review. All provider responses are synthetic; no network calls were made.

**Verdict: BLOCK acceptance of the provider expansion pending two confirmed retention fixes.** The 61 new regression tests pass but do not detect these failures.

## P1: Requested YouTube transcripts are fetched and then discarded

Locations: `scripts/evidence_scout/collect.py:1596` (outer retention slice), `scripts/evidence_scout/collect.py:2332` (transcript construction).

Trigger: one scheduled query with a five-record allowance, one video with at least four comments, and transcripts enabled. Metadata and comments fill the allowance; the transcript is appended afterward and removed by the new outer slice.

Observed: retained evidence contains one video and four comments; transcript summary reports `attempted=1`, `fetched=1`, `statuses={"ok":1}` and provider status `ok`. Raw transcript metadata records only video ID, status and character count. The actual transcript text is absent from both normalized evidence and raw capture. The global transcript allowance is nevertheless consumed. The pre-change collector retained the transcript as a sixth record under the same synthetic response.

Recommended correction: reserve capacity for explicitly requested enrichment or define a separate transcript allowance. Persist fetched transcript text before selection and distinguish fetched, retained and skipped counts. Regression coverage must assert retained text, not just successful fetching.

## P2: Social allocation starves later platforms and mislabels valid results

Locations: `scripts/evidence_scout/collect.py:2778` (fixed endpoint order), `scripts/evidence_scout/collect.py:2851` (shared allocation), `scripts/evidence_scout/collect.py:2897` (incorrect disposition).

Trigger: one query, three-record allowance, `social_per_endpoint=3`, three valid posts from each of TikTok, Instagram and Threads, and social comments enabled.

Observed: all three searches run, but only the three TikTok posts are retained. Instagram and Threads report `ok;items_without_text;records=0`, despite returning valid text. Provider status remains `ok`. No Instagram comment requests are scheduled because its posts never reach the comment-candidate list.

This is a retained-evidence coverage failure, not an unattempted-search failure. Raw search responses remain available.

Recommended correction: allocate across platform lanes explicitly or select results round-robin. Distinguish exclusions due to allocation from records without text, and preserve intended comment-source coverage.

## Reproduction and scope

Run from the repository root:

```bash
python3 docs/audits/research-query-expansion-2026-09-23/reproduce.py
```

The reproduction uses the expansion tests' synthetic argument fixtures. Current output is saved in `results.txt`. Baseline comparison also runs if the original snapshot remains at `/tmp/research-expansion-baseline/scripts/evidence_scout/collect.py`; it is optional for reproducing both current failures.

Reviewed the six implementation files, shared schema/guidance, expansion tests and pre-change differences. No additional material regression was established in the market wrapper, founder, competitor or community changes. This is neither exhaustive proof of correctness nor live-provider/native-language validation.
