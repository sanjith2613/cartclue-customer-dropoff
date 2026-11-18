# CartClue methodology and decision log

## Business question
When ecommerce session purchase conversion declines, which observed journey stages and segments should an analyst investigate first?

**Important:** This is a diagnostic/decision-support dashboard, not a proven causal inference engine. The historical Google demo export is obfuscated. Simulation numbers are synthetic and are labelled as such in the interface.

## Data lineage
- External: `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` (2020-11-01 to 2021-01-31).
- SQL 01: event discovery and tracking audit.
- SQL 02: one row per combination of `user_pseudo_id` and `ga_session_id`; uses observed event presence because the GA4 sample may omit funnel events.
- `measurement_mode=observed_events`: source coverage mode for GA4 exports. The `simulated` example stays in legacy strict nested funnel mode.
- `app.py`: local CSV input (can accept more than one short export) or synthetic demo fallback.
- `cartclue/analytics.py`: repeatable cleaning, descriptive analysis, statistical review, ML screening, and scenario analysis.

## GA4 observed-event presence (recommended for public sample)
- The Nov 1–7, 2020 raw diagnostic had 4 add-to-cart events, but 1,411 checkout-start events and 273 purchase events. This makes a strict stage-to-stage purchase funnel unsuitable.
- Every session-level event flag independently records whether that event occurred at least once, not whether the shopper advanced from the previous step. A purchase may have no `add_to_cart` or `begin_checkout` event in the same observed session.
- The dashboard shows *event reach* (sessions containing each event) with a common denominator of all reconstructed sessions, and does not infer stage-to-stage abandonment.
- Purchase conversion = sessions with at least one recorded purchase event / included reconstructed sessions, not Google Analytics UI session conversion.
- Revenue = sum of available `ecommerce.purchase_revenue` on purchase events. It is not audited transaction revenue. A revenue scenario divides by purchase *sessions*, not by distinct orders.
- The upload includes `measurement_mode=observed_events`. Mixing these records with old strict funnel exports is rejected to prevent corrupted conclusions.
- Event gaps and missing session starts are reported as limitations, not necessarily user drop-offs.

## Simulated example: strict sequential funnel definitions
- Sessions: unique `user_pseudo_id` + `ga_session_id` composites with at least one selected tracked event.
- Product view: a `view_item` in this session.
- Add to cart: a first `add_to_cart` at or after the session's first `view_item`.
- Checkout started: first `begin_checkout` at or after first `add_to_cart`.
- Purchase: first `purchase` at or after first `begin_checkout`.
- Conversion rate: sessions reaching strict purchase / included sessions.
- Drop-off for stage i: prior stage sessions minus stage i sessions.
- AOV: recorded revenue in strict purchasing sessions / strict purchasing sessions.

Do NOT label all excluded events as business abandonments. Incomplete analytics instrumentation, skipped stages, multiple visits, multi-day behavior, browser restrictions, and repeated events can affect these measures.

**Ordering distinction:** The current SQL 02 does **not** compare first-event timestamps; it preserves independent event presence because this source cannot support a reliable conventional cart funnel. The simulated demo is intentionally nested. An advanced product could use event-array sequence matching on a sufficiently complete, consistent dataset.

**Window boundary:** Weekly SQL extracts include only events whose daily tables are inside the chosen suffix range. Session rows near boundaries may have incomplete sequences; export a date overlap or query a wider interval and audit session completeness. Combining exported CSVs deduplicates by session key and keeps the first copy. Do not rely on that for accurate boundary stitching; best export sufficiently wide complete windows where possible.

**Acquisition:** `traffic_source.source` is FIRST-USER attribution, not the source for the current session. Do not claim channel-level ROI or a per-session acquisition source without using appropriate attribution fields.

**Revenue:** GA4 obfuscation can create inconsistencies. For observed-event mode, summed `ecommerce.purchase_revenue` is preserved in sessions with recorded purchase events regardless of cart instrumentation. `NULL` purchase revenue is coalesced to zero in SQL, so nonzero revenue is indicative only and apparent zero revenue is NOT proof of no sales. Before reporting business impact, reconcile transaction IDs, purchase events, refunds and currency with trusted order systems.

## Segment statistics
Each segment is compared against *all sessions outside that segment* using a pooled two-proportion z-test. The test runs only when the approximation has >=5 expected successes and failures in both groups, and segment and remainder each have >=30 sessions. Benjamini-Hochberg false-discovery-rate adjustment (q-value) is made within each currently selected segmentation. P-values are descriptive screening evidence, not causal proof.

## Monitoring
Day-over-baseline alerts compare conversion rate to the prior seven observed days; an unadjusted two-sided p-value <0.01 and decline triggers a flag with >=50 current-day sessions. Many repeated tests inflate the rate of false positives; use this for exploration, not automated operational decisions. Consider weekday-matched baselines, multiplicity correction, data delays and minimum effect size in an advanced version.

Isolation Forest is fitted on all selected daily observations from three dimensions: sessions, conversion %, revenue. It needs >=30 days. It is retrospective unsupervised outlier detection, not future prediction; no holdout evaluation has yet been performed. Add time-series holdout and synthetic anomaly injection to assess precision, recall and false-alert rate before presenting the model as production-ready.

## Business-impact simulation
Extra revenue = session count × absolute percentage-point conversion lift × average observed order value. These are assumptions. This is not observed realized lift, causal attribution, uplift-model output or profit. Change scenarios only to show decision sensitivity, not to claim recovered revenue.

## Privacy and costs
The project requires no real user PII. Public demo data and obfuscated Google public data are intended for training. Do not upload private company exports to a public repository. Prefer local small CSV extracts for Streamlit hosting; BigQuery Sandbox does not support scheduled transfers, DML or streaming. Dataset tables created in Sandbox expire after 60 days; raw Google public tables are maintained by Google.

## Recruiter evaluation checklist
- [ ] Run the app from a clean clone.
- [ ] Demonstrate SQL event unnested session-id parsing and date suffix filter.
- [ ] Show 3+ validation tests and a boundary/attribution caveat.
- [ ] Identify observed event coverage gaps and explain why sparse add-to-cart records prohibit a defensible abandonment calculation.
- [ ] Compare segments using adjusted significance and sufficient sample size.
- [ ] Explain one real-world hypothesis and the experiment needed to test it.
- [ ] Explain why ML anomalies are not causes or predictions.
- [ ] Present scenario uplift honestly as hypothetical, not achieved results.
- [ ] Share a public deployed app and concise GitHub README with a screenshot.
