# Build CartClue from zero — a 24-session learning roadmap

Use ~2 hours per session. Allocate another 5–15 hours for debugging, real GA4 analysis and polishing; expect 45–65 hours total. Do not claim the sample demo reflects real conversion behavior.

## Phase A: Be a product analyst (Sessions 1–3)
**Session 1 — Business brief.** Write a five-line problem statement: An e-commerce company has traffic but struggles to understand declines in session purchase conversion. Define your users (growth lead, ecommerce PM, marketing analyst), their decision (which journey step to investigate), and what the dashboard cannot answer (causal root cause without experiments). Deliverable: product brief in README.

**Session 2 — Metric definitions.** Calculate session conversion = distinct sessions with strict checkout purchase / distinct eligible sessions. AOV = purchase revenue / purchases. Stage reach = unique sessions that passed every previous stage. Explain why '100k visits, 2k purchases' alone is not evidence that checkout is broken. Deliverable: one-page metric dictionary.

**Session 3 — Create a repo.** Install Python 3.11 and Git. Unzip starter, create a `.venv`, install requirements, run nine tests and run Streamlit. Explore the **simulated** default dashboard and confirm the data warning.

## Phase B: Become a SQL detective (Sessions 4–8)
**Session 4 — BigQuery Sandbox.** Create a no-billing sandbox project, open the public GA4 sample, run `sql/01_inspect_events.sql`. Learn `SELECT`, `WHERE`, `GROUP BY`, `COUNT`, `COUNT(DISTINCT...)`, and the `_TABLE_SUFFIX` date filter. Deliverable: screenshot of event counts.

**Session 5 — GA4 events.** Inspect `event_name`, `event_date`, `event_timestamp`, `user_pseudo_id`, `device.category`, `geo.country`, and nested `event_params`. Explain why counting event rows is not counting distinct customers or sessions. Deliverable: annotated notebook/SQL comments.

**Session 6 — UNNEST and session key.** Explain extracting `ga_session_id` from `UNNEST(event_params)` and concatenating with the pseudo-user ID to avoid collisions. Run SQL 02 for a week; download the flat CSV. Deliverable: first real-data screenshot.

**Session 7 — Funnel order.** Walk through first timestamps for view, cart, checkout, and purchase. Compare un-ordered event counts with sequential session counts. Write a caveat about repeated events and missing tracking. Deliverable: notes and alternative SQL strategy.

**Session 8 — Data QA.** Review null IDs, duplicates, dates, non-monotonic stages and missing revenue. Explain how date-window boundaries can truncate sessions. Deliverable: exact counts in quality tab plus one new test.

## Phase C: Become a Python and statistics analyst (Sessions 9–15)
**Session 9 — pandas.** In `cartclue/analytics.py`, explain what `.groupby`, `.agg`, `.loc`, `.isna`, `.astype`, `.sort_values` do. Reproduce daily session counts and conversion in a notebook or Python script.

**Session 10 — Build the funnel.** Reproduce the funnel table manually for a 1-day slice. Identify the biggest **absolute** loss and biggest **percentage** loss; these can be different. Deliverable: a short interpretation paragraph.

**Session 11 — Segment comparison.** Break conversion down by device, country, first-user source. Explain that source is **first-user** attribution; it is not current-session channel and cannot prove marketing ROI. Deliverable: 3 screenshots and denominators.

**Session 12 — Statistical testing.** Interpret the two-proportion z-test and sample guard. Construct a confidence interval or compare rates in scipy. Be able to explain p-value is not the probability a hypothesis is true. Deliverable: why one observed difference may be inconclusive.

**Session 13 — Multiple comparisons.** Explain why many statistical tests generate false discoveries. Inspect `q_value_fdr` to see Benjamini–Hochberg correction. Deliverable: one observation where raw p and adjusted q tell different stories (if available).

**Session 14 — Anomaly detection.** Inspect prior-seven-day baseline alerts; explain seasonality, missing days, small sample size, false alarm rate and how label delays affect alerts. Deliverable: top three caveats.

**Session 15 — Machine learning.** Train/inspect IsolationForest and its feature scaling. Note that training + evaluating on all days is not predictive validation. Stretch: inject known synthetic shocks, reserve last 20% of dates, assess precision, recall and false alarm rate. Deliverable: model card with limitations.

## Phase D: Build a business decision product (Sessions 16–20)
**Session 16 — Make the dashboard useful.** Test each tab; rename vague charts, add clear units and denominator definitions, and include annotations for zero-conversion dates. Deliverable: 3 dashboard screenshots.

**Session 17 — A/B experiment design.** Example hypothesis: simplifying a mobile checkout step increases purchase conversion. Randomize eligible mobile sessions or users into variants without contaminating groups. Primary metric: purchase conversion; guardrails: refund rate, revenue per session, page error rate. Specify a sample-size/power calculation and duration before launch. Do NOT claim an observational mobile gap proves the cause.

**Session 18 — Revenue scenario.** Calculate simple what-if: 100,000 sessions, +0.5 percentage-point conversion, AOV $80 → 500 hypothetical extra orders and $40,000 hypothetical incremental gross sales *if assumptions hold*. This is not observed recovered revenue, nor profit. Deliverable: a decision memo with assumptions.

**Session 19 — Recommendations.** Write 'Observed / possible explanations / data needed / next action' for the highest drop-off and strongest supported segment. Include alternative explanations such as device mix, traffic intent, sale periods, tracking and payment failures.

**Session 20 — Case study.** Draft one page: Context, Data, Metric Definitions, Methods, Three Findings, Rival Explanations, Proposed Experiment, Limitations, Next Steps. Populate with actual GA4 derived numbers only after independently validating the export.

## Phase E: Engineering and job search (Sessions 21–24)
**Session 21 — Testing.** Add three tests beyond those supplied: null session IDs, zero revenue, and out-of-order events. Confirm `python -m pytest -q` passes.

**Session 22 — Automation.** Run `python scripts/generate_report.py --input your_export.csv --output reports/ga4_summary.md`. Confirm it describes the data source. Push to GitHub and confirm GitHub Actions executes tests automatically on every push. This is reliable, useful automation, without fake 'live data' refresh.

**Session 23 — Free deployment.** Push a public repo (demo data only) and deploy on Streamlit Community Cloud. Confirm the public app loads demo mode, its CSV upload, all tabs and the what-if controls. If no Streamlit server is available on the build machine, this check must be completed from your local environment.

**Session 24 — Interview readiness.** Prepare a 90-second explanation of the business problem, architecture, SQL sessionization, statistical choices, limits of anomaly detection and proposed experiment. Record a 2-minute demo. Add repo link and app link to resume and LinkedIn.

## Example SQL teaching prompt
Before using the query, answer: What does `UNNEST(event_params)` do? Why do we need a user+session composite key? Why does `_TABLE_SUFFIX` reduce query data scanned? Why can the first view/cart/checkout timestamps not represent a perfect customer journey?

## Acceptance gates
- [ ] Real GA4 SQL query executed in free BigQuery Sandbox.
- [ ] Real GA4 CSV imported, 30+ calendar days if using ML.
- [ ] Date/session grain and data quality validated.
- [ ] At least one numerical observation with a denominator, segment size and caveat.
- [ ] A meaningful statistical comparison with interpretation and appropriate warnings.
- [ ] A hypothesis that can be tested experimentally rather than claimed as a cause.
- [ ] A working public Streamlit app and GitHub CI checks.
- [ ] README screenshots + one-page real-data case study + screen recording.
