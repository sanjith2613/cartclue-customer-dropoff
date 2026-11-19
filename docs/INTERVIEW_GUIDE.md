# CartClue — Resume and Interview Guide

## 45-second recruiter pitch
I built CartClue, an ecommerce analytics app using SQL, Python, pandas, statistics and Streamlit. I analyzed the public historical GA4 sample by reconstructing 25,417 sessions, building conversion KPIs and exploring customer segments. My most important discovery was that a strict funnel incorrectly reported zero purchases because add-to-cart events were mostly absent. I checked the original BigQuery event counts, corrected the pipeline to preserve 231 purchasing sessions and $18,833 of recorded event revenue, and labeled event coverage honestly. I published a live demo and automated tests through GitHub Actions. The next step would be a tracking audit and a controlled experiment, not an unsupported claim of recovered revenue.

## 90-second technical walkthrough
1. **Business need:** An ecommerce team needs reliable conversion and acquisition diagnostics.
2. **Source:** Google public obfuscated GA4 sample in BigQuery, restricted to Nov 1–7, 2020.
3. **Engineering:** SQL extracts session-level event flags and revenue. Python validates records and computes KPIs. Streamlit displays metrics, comparisons, warnings and scenarios.
4. **Hardest challenge:** Original ordered funnel showed no purchases, but raw BigQuery had 273 purchase events / 231 purchasing sessions. Missing add-to-cart records caused overfiltering. I used an event-coverage mode rather than fake drop-off math.
5. **Statistics:** The `google` first-user group had 0.68% conversion vs 1.03% across other groups (q=0.0138), but the result is exploratory and affected by attribution gaps.
6. **Decision:** Prioritize instrumentation and attribution audits, then longer-run adjustment/experimentation. Live public app defaults to labeled simulated data; local real-data analysis is documented separately.

## Resume bullets — select 2 (do not claim production deployment/financial uplift)

- Developed **CartClue**, an end-to-end ecommerce analytics application using **BigQuery SQL, Python/pandas, Plotly and Streamlit** to reconstruct **25K+ historical GA4 sessions**, validate event coverage and visualize purchase conversion and customer segments.
- Diagnosed a **funnel instrumentation/data-modeling issue** that incorrectly excluded **231 purchasing sessions**; reconciled against raw GA4 events, updated the extraction and dashboard logic, and documented analysis limitations.
- Implemented **two-proportion statistical comparisons**, multiple-testing correction, an exploratory revenue scenario simulator, and **16 automated tests with GitHub Actions**, deploying a public synthetic-data demo via Streamlit Community Cloud.

## Interview questions and truthful responses

**Why SQL if Python can clean data?** Because GA4 nested events are already in BigQuery; one SQL extract minimizes data movement. Python handles validation, statistics and the UI.

**How did you know the original funnel was wrong?** I compared processed zeros against raw event counts and found hundreds of purchase events but almost no add-to-cart events, meaning strict sequential gating was inappropriate.

**What does q=0.0138 prove?** It is an adjusted screening result under test assumptions, not a causal effect or reason to reduce Google ad spend.

**Did you recover $4,144?** No. That figure is a transparent what-if model assuming +0.20 percentage points of conversion improvement and constant volume/revenue per purchasing session.

**Did you train and validate ML?** The app includes an optional Isolation Forest screen, but my seven-day real-data sample is too short to make a validated ML performance claim.

**Why is the public app simulated?** To provide an instant, safe interactive demo without publishing or querying session-level source data. The separate real-data case study uses source-checked aggregate results.

**What would you improve next?** Tracking completeness, longer reliable period, user-clustered uncertainty, attribution validation, pre-registered experiment, and reproducible public aggregate dataset.
