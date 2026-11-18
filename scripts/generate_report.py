"""One-command evidence summary. SIMULATED unless --input is explicitly supplied.

Examples:
  python scripts/generate_report.py
  python scripts/generate_report.py --input path/to/bigquery_export.csv --output reports/ga4_summary.md
"""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from cartclue.analytics import (daily_metrics, funnel_table, event_reach_table,
                                observed_events_mode, prepare_data, recommendations,
                                statistical_alerts)


def generate(input_csv: Path, output: Path, provenance: str) -> None:
    raw = pd.read_csv(input_csv)
    df, quality = prepare_data(raw)
    event_mode = observed_events_mode(df)
    fun = event_reach_table(df) if event_mode else funnel_table(df)
    d = daily_metrics(df)
    recs = recommendations(df)
    lines = [
        '# CartClue analysis report',
        '',
        f'**Data provenance:** {provenance}',
        '',
        f'**Date range:** {df.date.min().date()} through {df.date.max().date()}',
        f'**Unique sessions:** {len(df):,}',
        f'**Sessions with purchase event:** {df.purchased.sum():,}' if event_mode else f'**Strict purchasing sessions:** {df.purchased.sum():,}',
        f'**Session conversion:** {100*df.purchased.mean():.2f}%',
        f'**Included purchase-event revenue:** ${df.revenue.sum():,.2f}',
        '',
    ]
    if event_mode:
        lines += ['## Recorded event reach (NOT a sequential funnel)', '',
                  '| Recorded event | Sessions containing event | % of all sessions |',
                  '|---|---:|---:|']
    else:
        lines += ['## Sequential funnel', '',
                  '| Step | Sessions | Step conversion | Prior-step loss |',
                  '|---|---:|---:|']
    for _, row in fun.iterrows():
        if event_mode:
            lines.append(f'| {row.event} | {row.sessions:,} | {row.pct_of_all_sessions:.2f}% |')
        else:
            lines.append(f'| {row.stage} | {row.sessions:,} | {row.step_conversion_pct:.2f}% | {row.dropoff:,} |')
    lines.extend(['', '## Data quality', ''])
    for key, value in quality.items():
        lines.append(f'- **{key}:** {value}')
    lines.extend(['', '## Hypotheses and next steps', ''])
    for rec in recs:
        lines.append(f'- **{rec["finding"]}:** {rec["evidence"]} Next: {rec["next_step"]}')
    alerts = statistical_alerts(d)
    lines.extend(['', '## Descriptive anomaly screen', ''])
    if alerts.empty:
        lines.append('Insufficient observed days for 7-day statistical baseline.')
    else:
        flagged = alerts[alerts.decline_alert]
        lines.append(f'{len(flagged)} flagged days (unadjusted exploratory test, not verified causes).')
        for _, row in flagged.iterrows():
            lines.append(f'- {pd.Timestamp(row.date).date()}: conversion {row.conversion_pct:.2f}%, '
                         f'prior 7-day baseline {row.baseline_pct:.2f}%')
    lines.extend(['', '> No results here demonstrate causal attribution or actual incremental revenue.', ''])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Created {output} (source: {provenance})')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path(__file__).resolve().parents[1] / 'data' / 'demo_sessions.csv')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'reports' / 'demo_findings.md')
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f'CSV not found: {args.input}')
    provenance = 'SIMULATED DEMO DATA (NOT GA4 REAL DATA)' if args.input.resolve() == (Path(__file__).resolve().parents[1] / 'data' / 'demo_sessions.csv').resolve() else f'User-provided CSV: {args.input.name} (verify source)'
    generate(args.input, args.output, provenance)
