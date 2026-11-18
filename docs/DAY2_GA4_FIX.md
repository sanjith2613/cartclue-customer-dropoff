# Day 2 — Fix for GA4 sample's incomplete add-to-cart events

## What happened
For 2020-11-01 to 2020-11-07, the raw-event diagnostic showed:

| Event | Raw events | Sessions containing the event |
|---|---:|---:|
| `session_start` | 25,141 | 25,134 |
| `view_item` | 33,746 | 5,566 |
| `add_to_cart` | 4 | 1 |
| `begin_checkout` | 1,411 | 877 |
| `purchase` | 273 | 231 |

Raw purchase-event revenue across this date window was **$18,833**. These are observations from your BigQuery results, not values independently validated against transactions.

The original strict CartClue SQL required an `add_to_cart` event before counting a checkout or purchase, and it discarded revenue in excluded sessions. This produced a misleading 0% purchase conversion. The original data-quality tab did not flag the issue because the SQL had already removed the unmatched stages.

## Corrected method

- Each distinct `user_pseudo_id` + `ga_session_id` is one reconstructed analytic session.
- `viewed_item`, `added_to_cart`, `began_checkout`, and `purchased` indicate **whether at least one event of that type was recorded in the session**.
- There is **no assumed order and no required earlier event**.
- **Recorded purchase-event revenue** is preserved even if the session has no cart/checkout event.
- `measurement_mode='observed_events'` tells the dashboard to show *event coverage*, not a sequential funnel.
- The app reports session purchase conversion and segmentation, but **does not calculate stage-to-stage abandonment** from unreliable event instrumentation.
- The event presence bar chart is descriptive: a session can have a purchase without an observed cart event.
- Keep the older simulated strict funnel as a separate, explicitly labeled teaching example.

## Windows: 10 steps

1. Close the running Streamlit app by pressing `Ctrl+C` in the terminal.
2. **Back up** your `cartclue_portfolio` folder (copy it to `cartclue_portfolio_backup`).
3. Download and unzip the Day 2 fix package.
4. Copy the contents **inside** `cartclue_portfolio` from the fix package into your existing `cartclue_portfolio` folder; choose **Replace files in destination** when prompted. Do not replace the whole folder, or you may lose your local data.
5. In your existing project's `data/ga4_exports`, **move** the OLD seven-day CSV to a separate backup folder such as `data/old_exports_backup`. It must not remain in `ga4_exports`, or ingest will combine the old and new definitions.
6. Open `sql/02_export_sessions.sql` in VS Code, copy the whole SQL, paste into a **new BigQuery query** and click **Run**. Dates are 2020-11-01 to 2020-11-07 by default.
7. In BigQuery **Save results → CSV (local file)**. Put the new CSV into your project's `data/ga4_exports` folder. If BigQuery's local download exceeds its limit, use smaller non-overlapping date ranges.
8. Open a VS Code terminal from your project root; in Windows Command Prompt run:

   ```bat
   .venv\Scripts\python.exe scripts\sprint.py ingest --folder data/ga4_exports
   .venv\Scripts\python.exe scripts\sprint.py check
   ```

9. Reopen the application using `REOPEN_CARTCLUE_WINDOWS.cmd`, or:

   ```bat
   .venv\Scripts\python.exe scripts\sprint.py launch
   ```

10. Upload `data/ga4_sessions_clean.csv` through the app's left-hand file uploader. You should now see **nonzero purchasing sessions and recorded purchase revenue**, and the Journey tab should say **Recorded event presence (not a sequential funnel)**. The Data quality tab should show measurement mode `observed_events`.

## What to expect if the query and filtering are identical

- Approx. **25,417 reconstructed sessions**
- Approx. **231 sessions with a purchase event** → **0.91% observed purchase-session rate**
- Approx. **$18,833 purchase-event revenue**
- Approx. **1 session with an add-to-cart event**, contrasted with 877 with checkout-start events. This is a **tracking/coverage warning**, not 99.98% cart abandonment.

These checks are expectations based on your diagnostic screenshot, **not guarantees**: SQL date filters, source selection, or later changes may affect totals. A purchase event can occur in a session without a `session_start` event, and ecommerce revenue is not fully audited.

## Portfolio statement

> I discovered that the obfuscated GA4 sample contained only four add-to-cart events despite hundreds of purchase events. Instead of reporting a false abandonment rate, I audited source events, removed an unsupported strict-funnel assumption, preserved purchase and revenue metrics, and created a transparent event-coverage dashboard with measurement limitations. Results are exploratory, not causal.
