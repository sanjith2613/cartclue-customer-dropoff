# CartClue — Real-data Ecommerce Investigation

**Case study type:** Exploratory product analytics and data-quality investigation  
**Dataset:** Public, obfuscated GA4 ecommerce event sample, Nov 1–7, 2020  
**Status:** Completed descriptive analysis; no live experiment, causal effect, or realized revenue gain

## 1. Business request
An ecommerce team wants to understand what customer-journey and acquisition issues deserve investigation when purchase conversion appears low. The objective is **not** to find a sensational drop-off at any cost; it is to produce **reliable**, decision-ready observations.

## 2. Data and design
The source was `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` in BigQuery. SQL extracted relevant events and reconstructed a **pseudonymous user/session composite identifier** to produce a flat table at **one row per reconstructed session**. Python validated keys, duplicates, funnel flags, revenue and time coverage. Streamlit calculates KPIs and segment tests from that table. The real study covered 7 dates and 25,417 reconstructed sessions.

The **public app's default dataset is synthetic**. The local historical GA4 extract was analyzed separately and is not committed to GitHub. This distinction is deliberate.

## 3. The key debugging discovery
**Original problem:** The first version enforced a sequential `view_item → add_to_cart → begin_checkout → purchase` journey. It reported 0 purchases and $0 revenue.

**Source reconciliation:** The raw event diagnostic showed 273 purchase events across 231 identifiable sessions and $18,833 of event-field purchase revenue, but only 4 `add_to_cart` events across 1 identifiable session. There were 1,411 checkout events across 877 identifiable sessions. Thus a strict nested funnel was inappropriate for this source slice.

**Correction:** Preserve observed purchase events and recorded revenue in the session extract; flag **independent event presence** for each stage rather than pretending all stages are observed in order. The corrected app clearly labels this mode and warns that **cart abandonment cannot be inferred** from these counts.

**Data-quality lesson:** A cleaned dataset can show zero duplicates or format errors while the metric logic remains invalid. Both technical validation and source-to-output reconciliation are necessary.

## 4. Observed KPIs

| KPI | Value | Meaning |
|---|---:|---|
| Reconstructed sessions | 25,417 | Unique session keys in processed extract |
| Purchasing sessions | 231 | Sessions with ≥1 purchase event |
| Purchase-session conversion | 0.91% | 231 / 25,417 |
| Recorded revenue | $18,833 | Sum of observed purchase-event revenue; not audited sales |
| Sessions with `view_item` | 5,566 | Independent event presence |
| Sessions with `add_to_cart` | 1 | Independent event presence (instrumentation caution) |
| Sessions with `begin_checkout` | 877 | Independent event presence |

## 5. Segment comparisons

**Device:** Desktop 140/14,647 (0.96%), mobile 85/10,206 (0.83%), tablet 6/564 (1.06%). No device segment was flagged at q < 0.05 by the app's segment-vs-rest comparisons.

**Countries:** U.S. 108/11,071 (0.98%), India 23/2,455 (0.94%), Canada 22/1,897 (1.16%), U.K. 6/871 (0.69%). Major groups in the screenshot were not statistically flagged after the app's correction.

**First-user acquisition source:** `google` was 61/8,916 (0.68%); all other groups combined were 170/16,501 (1.03%). The within-source-dimension Benjamini–Hochberg adjusted q-value shown by the app was **0.0138**. This is an **association and screening result**, not evidence that the source caused lower conversion. `Unknown` (6,650 sessions) and `(data deleted)` (1,836) account for **33.4% of analyzed sessions**. The latter cannot be interpreted as a marketing source.

**Statistical caveat:** The app's two-proportion z-tests assume approximate independence. Repeated sessions from a user and source mix can compromise that assumption; p-values should not be treated as definitive.

## 6. Decisions and hypotheses

1. **First priority: audit measurement.** Verify ecommerce tags in a controlled checkout, required session keys, event timestamps, and purchase revenue; investigate potential source/attribution label errors and internal referrals.
2. **Second priority: investigate Google-first-user source difference.** Check device, geography, intent, and landing-page mix after instrumentation is sound. Ask whether the gap persists across a longer window and after accounting for confounders.
3. **Do not:** claim a specific cart-abandonment percentage, change ad budgets on first-user labels alone, or label the simulated improvement as realized profit.

## 7. What-if model (not a forecast)

A **hypothetical** +0.20 percentage-point increase on 25,417 sessions gives `25,417 × 0.002 ≈ 50.8` additional purchasing sessions. At `$18,833 / 231 ≈ $81.53` observed revenue per purchasing session, this corresponds to roughly **$4,144** of *modeled* additional event-field revenue at the same volume and revenue/session. No action has been proven to achieve that uplift.

## 8. Proposed experiment (not executed)

After correcting tracking and validating a specific landing-page hypothesis, randomize eligible users into control vs treatment. Predefine the primary purchase outcome, assignment unit, sample size/minimum detectable effect, test duration and guardrails (errors, latency, instrumentation completeness). Analyze by assigned group and do not claim causal impact until the experiment is completed.

## 9. Limitations

- Public sample covers 2020–2021; this analysis is one historical week.
- Obfuscation may make event relationships incomplete/inconsistent.
- Independent event coverage is **not** a sequential funnel.
- First-user source cannot establish session-channel ROI.
- Source labels include ambiguous categories; observed revenue is not accounting truth.
- Seven distinct days do not support a validated 30+ day anomaly analysis.

## 10. Outcome

**Delivered:** A reproducible SQL-to-Python-to-Streamlit workflow, explicit event-coverage fallback, statistical segment explorer, exploratory scenario calculator, data-quality warnings, tests, GitHub Actions CI, and a public demo. The main demonstrated impact is **avoiding an incorrect zero-purchase business conclusion**—not a measured sales lift.

[Live demo](https://cartclue-growth-investigator.streamlit.app/) · [Architecture](ARCHITECTURE.md) · [Detailed decision note](DAY4_DECISION_NOTE.md)
