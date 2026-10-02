# Venture-capital investment signals

Use this when a founder targets venture scale, expects to raise VC, asks whether
investors are funding a topic, or when investor activity could materially alter
the financing assumptions. Do not make it a mandatory step for a local,
bootstrapped, lifestyle, or otherwise non-VC business unless the user asks.

## What this evidence answers

Funding rounds and investor participation can indicate where capital is
currently flowing and whether attention appears to be rising, steady, or
cooling. They do not show that customers have the problem, will pay, that the
market is attractive, that a company is successful, or that this founder can
raise. Keep the VC signal lane separate from customer voice, demand, market
size, and comparable-company outcomes.

## Research sequence

1. Translate the idea into one or more provider industry tags. Preserve the
   founder's wording, the mapped Parsers VC tag(s), and why each mapping fits.
   Treat multiple plausible tags as alternatives; do not pick only the tag
   with the strongest funding result.
2. If the founder asks where investors are active generally, scan the leading
   provider industry tags and explain that this is a bounded discovery sample,
   not an exhaustive taxonomy.
3. Compare equal-length current and preceding periods. Report recorded rounds,
   investor-joined-round signals, disclosed amount samples, target geography,
   sample limits, query dates, and credits. Prefer a 12-month comparison; use
   shorter windows only for a stated reason.
4. If a query reaches its cap, call the count a lower bound and suppress
   acceleration labels for that comparison. Do not compare capped and uncapped
   counts as if they were complete.
5. For material examples, find the company's or participating fund's own
   dated announcement or a relevant filing. Keep provider-reported data
   attributed to Parsers VC until checked. Funding announcements can be
   delayed, corrected, syndicated, undisclosed, or misclassified.
6. Interpret both absolute activity and change. A small category can show a
   large percentage increase from a tiny baseline; a large category can remain
   active while slowing. Explain which pattern applies rather than calling a
   sector "hot" based on one number.
7. Assess investor fit separately from topic activity: likely stage and ticket,
   geography, business model, fund thesis, capital intensity, growth potential,
   and founder's financing objective. VC interest is not automatically useful
   for a business that does not need institutional capital.
8. Reconcile with customer and operating evidence. Strong capital activity with
   weak customer evidence remains an unvalidated opportunity; weak visible VC
   activity is not evidence that the customer problem is absent.

## Parsers VC implementation

The bounded source client is:

```bash
python3 scripts/market_research/scan_vc_topics.py --max-topics 12 --window-days 365 \
  --signals-per-query 20 --max-credits 400 \
  --out '<case>/market_research/investor_activity/parsersvc-topic-scan.json'
```

For an idea-specific check, map it to exact provider tags and pass each with
`--topic '<tag>'`; add `--country '<country>'` for a target-geography view.
The tool checks the remaining API-credit balance and estimated run spend before
making signal queries. Keep `--max-credits` within the account's authorized
spend. API credentials alone do not authorize paid overage.

The scan compares `round.recorded` and `investor.joined_round` signals using
equal-length periods, and records original responses, request parameters,
provider timestamps, and provider record identifiers. Its activity hints are
transparent heuristics, not a calibrated forecast. Read the provider's current
API documentation and pricing before changing query volume:
[API reference](https://parsers.vc/api_page/reference/),
[pricing](https://parsers.vc/api_page/pricing/).

## Output

Include:

- Mapped topic tags and geography, with scope and mapping uncertainty.
- Current/prior period round and investor-participation counts and their limits.
- Any disclosed funding amounts as partial samples, not total capital invested.
- Verified example investors and rounds with primary-source dates and links.
- An interpretation of activity level and direction, separate from company
  success, customer demand, and fundraising fit.
- Remaining data-coverage gaps and the next evidence that could change the
  financing assessment.
