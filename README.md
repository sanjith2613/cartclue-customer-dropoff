# 🛒 CartClue — Customer Drop-Off Detective

**Tagline:** Find where shoppers stop progressing, what changed, and what to investigate next.

*A free, beginner-friendly but recruiter-presentable data science project. Python • pandas • BigQuery SQL • SciPy statistics • scikit-learn anomaly detection • Plotly • Streamlit • pytest • GitHub Actions.*

## Day 2 GA4 event-coverage fix (important)

**After checking actual sample events, we found almost no `add_to_cart` events in the Nov 1–7, 2020 extract, despite many checkout and purchase events.** The old strict-funnel SQL incorrectly reported zero purchases because it required missing earlier events. **Use the UPDATED [`sql/02_export_sessions.sql`](sql/02_export_sessions.sql),** then re-export and ingest the data. Preserve the new `measurement_mode=observed_events` column. The real-data Journey tab now shows **independent event reach**, not step-to-step abandonment. The simulated demo still has an intentional strict funnel for learning.

See [the 10-step Windows repair guide](docs/DAY2_GA4_FIX.md) and [methodology](docs/METHODOLOGY.md). Never mix CSVs produced by the old strict query and the new event-presence query in `data/ga4_exports`.

## WINDOWS FIRST? START HERE (2 HOURS ON DAY 1)

Download and extract this **Windows Day 1 Ready** ZIP. Open `cartclue_portfolio`, then double-click `START_CARTCLUE_WINDOWS.cmd` after installing the official **Python 3.13 (64-bit)**. Or follow the transparent commands in [`docs/DAY1_WINDOWS.md`](docs/DAY1_WINDOWS.md). Today only uses **SIMULATED** demo data; BigQuery is for a later day. To restart without reinstalling, use `REOPEN_CARTCLUE_WINDOWS.cmd`.

**Time budget note:** The older `docs/SPRINT_6_DAY.md` describes an optional, more extensive **24–32-hour** study plan, not the current **2 hours/day** fast-track. For now, follow `docs/DAY1_WINDOWS.md` and focus on publishing a minimal, defensible MVP over 8–12 hours.

## 0. Important truth-in-data note
The included `data/demo_sessions.csv` is **100% simulated**; it is NOT Google data or observed business performance. To analyze Google's real (obfuscated) historical 2020–2021 GA4 sample, execute `sql/02_export_sessions.sql` in BigQuery Sandbox and upload the exported CSV in the app. Findings are descriptive. Claims about recovered revenue must never be inferred from the simulator.

## ⚡ New: 4–6 day AI-assisted fast-track

The [six-day sprint guide](docs/SPRINT_6_DAY.md) explains *why* each tool is used, how to hand-check results, and when ChatGPT, Claude, or Grok can safely accelerate the work. It reduces repetitive steps with `scripts/sprint.py` and offers an **optional** credential-based BigQuery download helper.

```bash
python scripts/sprint.py demo  # synthetic demo + tests + report
python scripts/sprint.py sql   # generate six weeks of ready-to-run GA4 SQL batches
# After exporting BigQuery CSVs into data/ga4_exports/: 
python scripts/sprint.py ingest --folder data/ga4_exports --publish-sample
python scripts/sprint.py check
python scripts/sprint.py launch
```

`--publish-sample` prepares an ID-redacted **sample**, not full-population numbers. Inspect dataset provenance before committing that file to a public repo. Real BigQuery queries and deployment cannot run without your Google/GitHub account access.

## 1. Run the app for $0
Install [Python 3.11](https://www.python.org/downloads/) and [Git](https://git-scm.com/downloads), then in this directory:

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/build_demo.py
python scripts/generate_report.py  # automatically creates reports/demo_findings.md
python -m pytest -q
streamlit run app.py
```

The app will open in your browser. Start with the clearly marked synthetic data. Try moving the date filter to the last nine days to investigate the deliberately introduced mobile checkout decline.

## 2. Real data: Google GA4 BigQuery public sample
1. Open [BigQuery Studio](https://console.cloud.google.com/bigquery) with a Google account.
2. Create a **BigQuery Sandbox** project; avoid enabling paid billing if $0 is a firm constraint.
3. Open `sql/01_inspect_events.sql`, paste into the query editor and run. Check the counts of `view_item`, `add_to_cart`, `begin_checkout`, `purchase`.
4. Open `sql/02_export_sessions.sql`. It initially covers **2020-11-01 to 2020-11-07**. Run it.
5. Use **Save results → CSV** in BigQuery (flat schema). Name it `ga4_sessions_20201101_20201107.csv`.
6. Upload it using **Upload session-level GA4 CSV file(s)** in the Streamlit app sidebar.
7. For 30+ days of anomaly review, rerun SQL 02 after updating both `_TABLE_SUFFIX` dates to adjacent weeks. Upload all CSV slices together. **Important:** local CSV downloads have a documented size limit (10 MB at the time of writing). Use shorter periods if you hit it; be careful with session-boundary truncation.
8. Inspect `Data quality`, compare **independent event coverage** and purchase-session rates by device and first-user source, and read statistical caveats in `docs/METHODOLOGY.md`. Do not infer cart abandonment from the sparse add-to-cart events.

Dataset: `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` — 2020-11-01 through 2021-01-31. Google warns that obfuscation limits internal consistency. This is not live data.

Official references: [GA4 public dataset](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset) · [BigQuery Sandbox](https://docs.cloud.google.com/bigquery/docs/sandbox) · [BigQuery query-results CSV limit](https://docs.cloud.google.com/bigquery/docs/writing-results).

## 3. How the pipeline works

```text
Real GA4 public event tables --BigQuery SQL--> flat session CSV -----┐
                                                                    ├--> data validation / independent event reach
Deterministic SIMULATED sessions (local app demo) -------------------┘             |
                                                                               v
                                                    daily KPIs + segment tests + demo funnel
                                                                               |
                                                    anomaly screening + business hypotheses
                                                                               |
                                                 Streamlit dashboard + what-if simulator
                                                                               |
                                                      pytest + GitHub Actions CI checks
```

Generate an automatically written analyst report using `python scripts/generate_report.py --input path/to/export.csv --output reports/my_findings.md`. **Inspect and verify all suggested hypotheses** before using the report externally.

There is no automatic daily GA4 refresh: the sample is historical and fixed. The app automatically re-runs analysis on uploaded CSVs and filters, the demo generator creates reproducible fake data, and CI automatically tests changes on GitHub pushes. A future production data source could implement scheduled extracts subject to provider cost/access constraints.

## 4. Key skills this demonstrates
- **SQL:** nested `UNNEST(event_params)`, session reconstruction, event timestamps, filtering by `_TABLE_SUFFIX`, aggregation and conditional logic.
- **Data engineering:** provenance, idempotent session de-duplication, data quality checks, flat analytical grain.
- **Exploratory & product analytics:** independent GA4 event reach, simulated sequential funnel, denominator awareness, channel-attribution caution, segment investigation.
- **Statistics:** conditional rates, two-proportion z-tests, FDR adjustment, sample-size guards, exploratory alerts.
- **ML:** IsolationForest retrospective anomaly detection (with honest limitations).
- **Analytics product:** responsive dashboard, upload mode, filters, priority recommendations, sensitivity analysis.
- **Engineering:** package modules, unit tests, CI, version control, documentation, free deployment.

## 5. Deploy for free
1. Create a **public** GitHub repository, e.g. `cartclue-customer-dropoff`.
2. Commit and push this repository, including the simulated demo CSV (not your private data).
3. Open [Streamlit Community Cloud](https://share.streamlit.io/), sign in with GitHub, and select repository plus `app.py` as the entry file.
4. Deploy and test the public link. Add it and a screenshot to this README.
5. Confirm a recruiter can use demo mode without authentication or cloud credentials.

The default demo is **not** an automated claim about Google data. If you want the public demo to use actual GA4 derived aggregates, review data sizes and usage rights and document that provenance explicitly. The app supports visitor CSV upload at runtime; there is no BigQuery password or service-account key in this repo.

## 6. Milestone plan (45–65h beginner estimate)
| Phase | Deliverable | Time |
|---|---|---|
| 1 | Business brief, metric definitions, GitHub setup | 4–6h |
| 2 | BigQuery event audit and SQL session export | 8–12h |
| 3 | Python cleaning, SQL/Python cross-checks, EDA | 7–10h |
| 4 | Funnel analysis, segment tests and statistical alerts | 8–12h |
| 5 | ML anomaly screen and scenario design | 6–9h |
| 6 | UI polish, unit tests, deploy, README and interview walkthrough | 12–16h |

For the detailed 24-session guided lessons and acceptance criteria, see [`docs/BUILD_GUIDE.md`](docs/BUILD_GUIDE.md).

## 7. What to do beyond the supplied starter
- Analyze multiple actual GA4 slices and document **real** findings with counts and denominators.
- Write a one-page case study with 1 business hypothesis, 2 rival explanations, a randomized experiment design and decision threshold.
- Create a 2-minute screen recording showing the dashboard, quality checks and limitations.
- Evaluate anomaly false-alert rate with injected synthetic anomalies in held-out days.
- Run funnel checks at the event sequence level, improving the SQL first-occurrence approximation.
- Only after proving value, consider Airflow/dbt/LLM/RAG/real-time pipelines. They are not needed for this first portfolio.

## 8. Suggested resume bullets (edit when verified)
- Built **CartClue**, an end-to-end ecommerce journey analytics application using BigQuery SQL, Python, pandas and Streamlit to analyze session-level funnels and conversion by behavioral segments.
- Implemented automated data validation, anomaly screening and statistically adjusted segment comparisons with reproducible pytest checks and GitHub Actions CI.
- Developed a scenario simulator and evidence-based investigation framework to prioritize checkout optimization hypotheses without misrepresenting simulated revenue as realized impact.

## 9. Honest limitations
See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md). Key points: 2020–2021 obfuscated dataset, first-user source is not session source, first-occurrence session funnel approximation, CSV slice boundary issues, small-sample statistical tests, in-sample unsupervised anomaly screen, and no causal proof.

## 10. Source attributions
- GA4 example data © respective owners; accessed through Google's public BigQuery dataset. No raw private Google store data is bundled here.
- All included sample rows are our own deterministic synthetic illustration.
- This example code is MIT licensed for portfolio/education use.


## Published portfolio case study — historical GA4
- **Date window:** 2020-11-01 to 2020-11-07 (public obfuscated GA4 sample).
- **Analyzed sessions:** 25,417; **purchasing sessions:** 231; **purchase-session rate:** 0.91%.
- **Recorded purchase-event revenue:** $18,833 (not audited store revenue or profit).
- The original strict funnel hid purchases because the source contained only four add-to-cart events. The corrected application uses **independent event coverage** for these GA4 exports rather than falsely claiming cart abandonment.
- Google first-user source purchase-session rate: 0.68%, compared with 1.03% for all other first-user source groups; adjusted q-value 0.0138. This is exploratory association, not evidence of causation.
- **Live app defaults to simulated demo data**; historical observations above came from separately analyzed public GA4 extracts. Full local session-level exports are not included in this repository.
- [Investigation and decision note](docs/DAY4_DECISION_NOTE.md)
- **App URL:** Add your Streamlit URL here after deployment.
