# CartClue analysis report

**Data provenance:** SIMULATED DEMO DATA (NOT GA4 REAL DATA)

**Date range:** 2020-11-01 through 2020-12-26
**Unique sessions:** 15,648
**Strict purchasing sessions:** 745
**Session conversion:** 4.76%
**Included purchase revenue:** $65,834.78

## Sequential funnel

| Step | Sessions | Step conversion | Prior-step loss |
|---|---:|---:|---:|
| Sessions | 15,648 | 100.00% | 0 |
| Product views | 11,274 | 72.05% | 4,374 |
| Added to cart | 2,990 | 26.52% | 8,284 |
| Checkout started | 1,533 | 51.27% | 1,457 |
| Purchased | 745 | 48.60% | 788 |

## Data quality

- **input_rows:** 15648
- **usable_sessions:** 15648
- **missing_key_or_date:** 0
- **duplicate_session_rows:** 0
- **funnel_sequence_inconsistencies:** 0
- **unusable_or_missing_revenue:** 0
- **negative_revenue_rows:** 0
- **revenue_excluded_from_strict_funnel:** 0.0

## Hypotheses and next steps

- **Largest absolute observed loss: before added to cart:** 8,284 sessions did not advance to this stage (73.5% of the prior step). Next: Verify event instrumentation and check product UX, traffic intent, and device-specific paths. Treat this as a hypothesis, not a proven cause.
- **Lower conversion for device: mobile:** 9,299 sessions; 3.40% conversion, -3.36 pp vs the rest (FDR q=1.01e-21). Next: Investigate composition and tracking; design a controlled A/B experiment before claiming improvements.
- **Lower conversion for first-user source: social:** 2,312 sessions; 3.59% conversion, -1.37 pp vs the rest (FDR q=0.0144). Next: Investigate composition and tracking; design a controlled A/B experiment before claiming improvements.

## Descriptive anomaly screen

0 flagged days (unadjusted exploratory test, not verified causes).

> No results here demonstrate causal attribution or actual incremental revenue.
