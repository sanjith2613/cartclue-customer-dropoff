# CartClue — Extended Build Sprint (Optional, 24–32 Hours)

> **2 hours/day on Windows?** This is the older extended track. Start with [`DAY1_WINDOWS.md`](DAY1_WINDOWS.md) and the streamlined 8–12-hour MVP instead.

**Objective:** ship a public, reproducible analytics portfolio project that explains observed GA4 customer journeys without claiming unsupported causes or realized revenue improvements.

**Time:** 24–32 focused hours. Six-day path below assumes 4–6 hours/day. Four-day path combines Days 1+2 and Days 4+5 with 6–8 hours/day. Real source data extraction and deployment are external steps; this kit does not claim they were completed.

## What each tool does (and what you should understand)

| Tool | Role | Why use it | Minimum interview explanation |
|---|---|---|---|
| Python | General project language | Automate analysis, transformations, reports | What runs when you enter a Python command |
| pandas | In-memory tables | Clean, filter, group event/session data | `DataFrame`, `groupby`, `agg`, missing data, row grain |
| BigQuery Sandbox | Hosted analytics database | Query real obfuscated GA4 event export without storing giant tables locally | `SELECT`, `WHERE`, `COUNT`, `GROUP BY`, `UNNEST`, `_TABLE_SUFFIX` |
| SQL | Data transformation | Turn many events into one row per session and enforce funnel sequence | Why event count != session count; composite session key |
| NumPy | Numerical operations | Fast mathematical calculations | Arrays and vectorized computations |
| SciPy | Statistical tests | Check whether observed conversion differences might be noise | Null hypothesis, p-value, statistical assumptions |
| scikit-learn | ML toolkit | Run retrospective Isolation Forest outlier screen | Features, anomaly score, false alarms, holdout limitations |
| Plotly | Interactive visualization | Clarify trends, funnel losses and segments | Each chart's numerator, denominator and caveats |
| Streamlit | App framework | Build UI with Python quickly | How filters, sidebar, tabs and data cache work |
| pytest | Unit tests | Catch faulty metrics before publishing | One specific bug a test would detect |
| Git + GitHub | Version control/public code | Reproducibility and recruiter visibility | Commit history, branch, public README |
| GitHub Actions | Continuous integration | Automatically execute tests on every push | What the workflow checks vs. what it cannot check |
| ChatGPT | Analytics mentor and reviewer | Explain SQL/statistics, critique business conclusions, draft case study | Never pass off AI prose as verified data |
| Claude | Pair programming/debugging | Refactor or troubleshoot modules with tests | Explain AI-authored code after reviewing it |
| Grok | Optional independent review | Critique business hypotheses or interview questions | Challenge assumptions; no need to integrate into app |

**Cost:** core framework is free. Use ChatGPT/Claude/Grok *chat subscriptions* interactively rather than calling paid APIs from the deployed app. Subscription and API charges are not generally interchangeable. BigQuery Sandbox has quotas; Streamlit Community Cloud supports free deployment; public GitHub standard Actions runners are free.

## Which tasks should be automated?

| Task | Automation provided | What you personally validate |
|---|---|---|
| Create synthetic training dataset | `scripts/sprint.py demo` | It is labeled **SIMULATED** |
| Prepare GA4 date-sliced SQL | `scripts/sprint.py sql` | Dates, event selection, session-key grain |
| Download GA4 query results | Optional `scripts/fetch_bigquery.py` with Google Cloud credentials | Credentials, project, query bytes, dataset provenance |
| Combine CSV exports | `scripts/sprint.py ingest` | Overlap/duplicates, row counts, window truncation |
| Detect invalid records | `cartclue.analytics.prepare_data` | Whether cleaning changes metric meaning |
| Calculate funnel/KPIs | Analytics module | Numerators, denominators, ordering logic |
| Compare groups | Proportion tests + FDR correction | Statistical vs business significance |
| Screen anomalies | Isolation Forest | In-sample screen, not future prediction |
| Generate hypotheses/report | `generate_report.py` | Causal claims, sample limitations, misleading metrics |
| Review app changes | `scripts/sprint.py check` + GitHub Actions | Test cases can miss bugs; manually inspect charts |
| Deploy after pushes | Streamlit Community Cloud GitHub linkage | Actually open URL and test each tab |

## Day 1 — Run the working product and learn the business (4–5h)

1. Install Python 3.11+, VS Code, and Git. Extract the kit, open its project root in VS Code.
2. Create virtual environment; activate it; install requirements:
   ```bash
   python -m venv .venv
   # macOS/Linux: source .venv/bin/activate
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
3. Run:
   ```bash
   python scripts/sprint.py demo
   python scripts/sprint.py launch
   ```
4. Click each tab. Explain sessions, product view, add-to-cart, checkout, purchases, conversion rate, and step drop-off in your own words.
5. Take two screenshots of the working synthetic demo, clearly labeled as synthetic.

**Acceptance:** local app opens; 12+ tests pass; you can calculate 2 conversion and drop-off rates by hand.

**AI prompt:** "Teach me the CartClue event -> session -> funnel architecture as a beginner. Quiz me on the numerator and denominator of each KPI. Do not assume simulated data is real."

## Day 2 — Get historical GA4 data with SQL (4–6h)

1. Create a **no-billing BigQuery Sandbox project** at https://console.cloud.google.com/bigquery .
2. Run `sql/01_inspect_events.sql` in BigQuery; screenshot results.
3. Generate ready-to-run batches:
   ```bash
   python scripts/sprint.py sql --start 2020-11-01 --end 2020-12-12 --days 7
   ```
4. **Easy/no extra software:** paste files from `sql/generated/` into BigQuery, run, download each result as CSV and place them in `data/ga4_exports/`. If the results exceed CSV UI limits, use shorter date windows or optional automatic export.
5. **Optional automated export:** install `requirements-bigquery-optional.txt` and Google Cloud CLI, run `gcloud auth application-default login`, then:
   ```bash
   python scripts/fetch_bigquery.py --project YOUR_SANDBOX_PROJECT_ID --start 2020-11-01 --end 2020-12-12 --batch-days 7
   ```
   The script estimates scan size, enforces a maximum processed-data threshold per query, writes files atomically and skips downloads already completed. This was NOT validated against live Google credentials in this environment.
6. Explain why `UNNEST(event_params)` is necessary and why a composite user+session ID is used.

**Acceptance:** at least 30 observed dates of GA4-format exports in CSV; query screenshots; data provenance documented. If getting real data is blocked, do not label synthetic screenshots as Google results.

**AI prompt:** "Explain this BigQuery SQL one CTE at a time; explain first-event ordering edge cases and how to audit null user IDs. Suggest only a minimal testable change, then review output." 

## Day 3 — Automate data prep, QA and business metrics (4–5h)

1. Merge/validate all extracts:
   ```bash
   python scripts/sprint.py ingest --folder data/ga4_exports --publish-sample
   ```
   Outputs: `data/ga4_sessions_clean.csv`, `reports/ga4_quality.json`, `reports/ga4_analysis.md`. `--publish-sample` creates **up to 20,000 sampled records** for the public app, replacing session identifiers; it is not representative of the whole event universe unless independently assessed.
2. Check duplicates, missing revenue, funnel inconsistencies, and session-boundary issues. **Do not silently regard deduplicated records as perfect.**
3. Manually calculate one day's session conversion and compare with the app.
4. Compare mobile vs desktop (and/or country/source) only where sample sizes support interpretation.
5. Log two **observations**, their denominators, and at least two plausible alternative explanations.

**Acceptance:** real-data analysis report generated; no fabricated root-cause language; at least one manual reconciliation completed.

**AI prompt:** "Act as a skeptical product analyst. Review the following QA output and funnel counts. Ask me three questions that could invalidate my conclusion. Do not invent data."

## Day 4 — Statistics, ML and recommendations (4–5h)

1. Read `proportion_pvalue`, `segment_comparison`, `statistical_alerts`, `ml_anomalies` in `cartclue/analytics.py`.
2. Explain difference between statistical and business significance. P-values do not prove causation; FDR correction limits discovery rate across a family of tests.
3. Observe any retrospective ML anomaly dates. Explain why isolation forest finds unusual *patterns* but not causes.
4. Document one proposed A/B test: hypothesis, randomization unit, primary KPI, guardrail metrics, sample-size/power to calculate before launch.
5. Use the scenario simulator to report **conditional hypothetical sales**, not proven dollars recovered.

**Acceptance:** one defensible statistical comparison, one anomaly-model limitation, and one experiment proposal in your case study.

**AI prompt:** "Review my observed conversion-rate gap. Tell me if the sample sizes support a z-test and what multiple testing, selection bias, weekday/seasonality and tracking changes could explain. Draft an A/B plan, not a causal claim."

## Day 5 — Deploy and make recruiter-ready (4–6h)

1. Run `python scripts/sprint.py check`.
2. Create a public GitHub repo named `cartclue-customer-dropoff`. Exclude `data/ga4_exports`, private credentials and complete raw exports. Opt in to `data/public_ga4_sessions.csv` only after examining it and verifying source provenance.
3. Push the repo. Confirm GitHub Actions test workflow completes with a green check.
4. Visit https://share.streamlit.io/ , link the repo, point to `app.py`, deploy.
5. Open the public link on a separate browser/device. Verify dashboard loads, upload works, counts match, no stack traces, and five feature areas behave correctly.
6. Add a screenshot + deployed URL to the README, explaining sample-vs-full-data provenance.

**Acceptance:** working public URL and GitHub URL, reproducible instructions, CI green, no credentials exposed.

**AI prompt:** "Audit this GitHub README like a U.S. data science hiring manager: find vague business impact claims, misleading statistics, missing proof, reproducibility gaps and overclaiming. Rewrite concisely without changing factual results."

## Day 6 — Case study and interview rehearsal (3–5h)

1. Write a one-page case study with: business decision, dataset dates, SQL grain, KPI definitions, QA, 3 evidenced findings, alternative explanations, actionable experiment, caveats.
2. Prepare a 90-second demo and a 3-minute walk-through. Capture a short screen recording if desired.
3. Ask ChatGPT to interview you on 10 topics (UNNEST, SQL grain, data quality, pandas, funnel, z-test, FDR, Isolation Forest, scenario assumptions, deployment).
4. Create resume bullets only about what you actually built and observed. Example:
   > Built CartClue, an interactive GA4 customer-journey diagnostic app using BigQuery SQL, Python, statistical tests, and Streamlit; automated data validation, exploratory anomaly screening, and CI checks.
5. Put project URL and GitHub URL on resume + LinkedIn.

**Acceptance:** fully reproducible repo, documented empirical results, 90-second pitch, clear limitations.

## Four-day emergency version

| Day | Combine | Priority |
|---|---|---|
| 1 | Six-day Days 1 + 2 | Running app, first real GA4 extraction |
| 2 | Six-day Days 3 + 4 | Validated data, statistics, ML critique |
| 3 | Six-day Day 5 | Public deployment and automation |
| 4 | Six-day Day 6 + fixes | Case study, screenshots, README, interview rehearsal |

**Cut these before cutting correctness:** custom CSS, external API/LLM integration, authentication, database hosting, forecasting, real-time monitoring, extra ML models, microservices, elaborate frontend, external Airflow/dbt deployment. This is an analytics product, not a full production commerce platform.

## Interview gate: five questions you must answer without AI

1. What's the difference between a GA4 event, user and session, and why does the SQL build `session_key`?
2. How is purchase conversion calculated and how might incomplete tracking bias it?
3. How can you find the largest absolute drop-off while not treating it as a proven UX problem?
4. What does your statistical test assume, what does an FDR-adjusted q-value mean, and why doesn't it prove causation?
5. Why did you choose Isolation Forest, and why can a flagged point be a false alarm?

## Honest limitations

- This is historical obfuscated GA4 sample data from Nov 2020–Jan 2021; it is not contemporary customer behavior.
- Only the source code and local tests are preverified. You still have to authenticate BigQuery, run queries, inspect real outputs and perform deployment validation.
- CSV export windows may split sessions; `prepare_data` keeps the first duplicate. Inspect this bias, or reduce boundaries by using longer API queries.
- The public `--publish-sample` is an opt-in random session-level subset with replaced identifiers. Its volume-based totals are *sample* totals.
- No live forecasting, causal root-cause determination or realized revenue gains are implied.
