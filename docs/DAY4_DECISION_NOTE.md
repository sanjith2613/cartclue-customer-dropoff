# CartClue — Day 4 Investigation & Decision Note

**Status:** Exploratory analysis; proposed actions only (not implemented or validated)

**Source:** Google Analytics GA4 obfuscated sample ecommerce events, reconstructed into session rows; November 1–7, 2020. Counts from the user's corrected CartClue dashboard and BigQuery inspection. These are not audited store results.

## Business question
Which part of our ecommerce measurement and customer acquisition deserves the next investigation, based on purchase-session rates and reliability of tracked events?

## KPI definitions
- **Analyzed session:** one composite pseudonymous user/session key represented in the extracted data.
- **Purchasing session:** a session with at least one observed purchase event.
- **Purchase-session rate:** purchasing sessions / analyzed sessions.
- **Recorded revenue:** sum of purchase-event revenue in source extract, *not* profit or audited sales.
- **First-user source:** initial acquisition source recorded for a user, *not* necessarily the source that brought them into the purchasing session.

## Verified descriptive results
| Measure | Result |
|---|---:|
| Analyzed sessions | 25,417 |
| Purchasing sessions | 231 |
| Purchase-session rate | 0.91% |
| Recorded purchase-event revenue | $18,833 |
| Sessions with recorded add-to-cart | 1 |
| Sessions with recorded begin-checkout | 877 |
| First-user source = google | 8,916 sessions; 61 purchasing sessions; 0.68% purchase-session rate |
| All other first-user source groups combined | 16,501 sessions; 170 purchasing sessions; 1.03% purchase-session rate |
| Google vs other groups, adjusted q | 0.0138 (within tested first-user source groups) |
| Unknown + (data deleted) source labels | 8,486 sessions; 33.4% of analyzed sessions |

**Evidence interpretation:** In this sample, Google's first-user source group has a lower observed purchase-session rate than the other groups combined. The adjusted test result warrants *investigation*, not a causal or marketing-spend conclusion. Sessions may be dependent because users can have multiple sessions; source labels and ecommerce events are obfuscated.

## Decision priority
**P0 — Measurement validation.** Inspect missing add-to-cart event coverage; check whether source labels and internal referrals are correctly configured. In this dataset, independent event-presence counts **cannot** be used to calculate sequential cart abandonment.

**P1 — Source composition investigation (only after P0).** Examine whether the lower purchase-session rate for the `google` first-user group persists by date, device and geography. Investigate traffic intent, landing page experience and attribution quality. Avoid changing budgets based on this extract.

## Hypotheses (unproven)
1. Purchase-intent mix differs among first-user sources.
2. Device and geography composition differs by source.
3. Attribution labels or obfuscation distort apparent source performance.
4. Missing funnel events are a tracking/data-coverage artifact rather than shopper abandonment.

## Proposed validation and experimentation
1. **Tracking audit:** In a controlled staging/QA environment, execute product-view → add-to-cart → checkout → purchase journeys; verify expected events, timestamps, user/session keys, transaction IDs and revenue fields. Document any missing steps.
2. **Attribution audit:** Verify how first-user source, session source, unknown/deleted labels, and possible internal referrals are populated. Compare to trusted transaction/order records if such records exist. They are not available in this public sample.
3. **Further analysis:** Increase the observed date window, re-check the same source differences and adjust for important covariates. Consider user-level dependence and uncertainty; do not treat simple session z-tests as definitive causal inference.
4. **If a credible opportunity remains, design an A/B experiment:** Randomly allocate eligible visitors between current and updated landing experience; choose a single primary purchase metric at the correct randomization unit, guardrail metrics (tracking completeness, errors, page performance), and predefine sample size, minimum detectable effect, and duration. No A/B test has been performed in CartClue.

## Scenario — *hypothetical, not a forecast*
The CartClue Decision lab slider adds an **absolute percentage-point** uplift to the baseline purchase-session rate and assumes unchanged traffic and recorded revenue per purchasing session.

| Assumed uplift | Hypothetical additional purchasing sessions | Hypothetical extra revenue |
|---|---:|---:|
| +0.1 percentage points | 25.4 | $2,072 |
| +0.2 percentage points | 50.8 | $4,144 |
| +0.5 percentage points | 127.1 | $10,361 |

Formula: 25,417 sessions × uplift expressed as decimal × ($18,833 / 231 purchasing sessions). These are model outputs, **not** verified incremental sales, expected A/B effects or profit.

## Limitations to disclose
- Only 7 historical days of deliberately obfuscated public GA4 data.
- Purchase events and add-to-cart events are **not** a reliable nested funnel here.
- Session-based tests may overstate precision when users have multiple sessions.
- First-user acquisition source is not session attribution; categories such as `(data deleted)` and `Unknown` are not reliable campaign labels.
- Revenue is an event-field total, not a financial ledger or audited actual.
- Seven days do not support the app's Isolation Forest screen (requires at least 30 distinct dates).

## Suggested portfolio conclusion
> I built CartClue, a Python/SQL/Streamlit analytics application, and analyzed 25,417 reconstructed sessions from the public obfuscated GA4 ecommerce sample. After reconciling source events, I found that strict sequential funnels hid valid purchases. I corrected the pipeline to preserve 231 purchasing sessions and $18,833 in recorded purchase-event revenue and surfaced independent event coverage instead of false cart abandonment. Segmentation identified a lower rate in the Google first-user source group (0.68% vs. 1.03% for other groups; adjusted q=0.0138), but attribution gaps and event inconsistencies limited causal interpretation. I prioritized measurement validation, source-mix analysis, and a future controlled experiment rather than prescribing unsupported marketing changes.

## Day 4 handoff
- [ ] Save screenshots of Decision lab assumptions and the source comparison.
- [ ] Generate `reports/ga4_day4_report.md` using `scripts/generate_report.py` with `--input data/ga4_sessions_clean.csv`.
- [ ] Keep this note in `docs/DAY4_DECISION_NOTE.md` for the GitHub case study.
- [ ] Day 5: run local tests, inspect repository files, publish a GitHub repo, deploy Streamlit and verify every tab.
