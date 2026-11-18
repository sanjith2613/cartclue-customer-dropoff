"""CartClue sprint helper: automate local setup, SQL batches, QA, and reports.

Run from the project root:
  python scripts/sprint.py demo
  python scripts/sprint.py sql --start 2020-11-01 --end 2020-12-12 --days 7
  python scripts/sprint.py ingest --folder data/ga4_exports --publish-sample
  python scripts/sprint.py check
  python scripts/sprint.py launch

The Google public data is HISTORICAL. SQL files must be run in your own BigQuery
Sandbox; use fetch_bigquery.py for optional credential-based automation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# When executed as `python scripts/sprint.py`, add the repo root for package imports.
sys.path.insert(0, str(ROOT))
GA4_START = date(2020, 11, 1)
GA4_END = date(2021, 1, 31)


def date_ranges(start: date, end: date, days: int) -> list[tuple[date, date]]:
    if days < 1:
        raise ValueError('days must be >= 1')
    if start > end:
        raise ValueError('start must be <= end')
    if start < GA4_START or end > GA4_END:
        raise ValueError('The public GA4 dataset spans 2020-11-01 through 2021-01-31')
    windows = []
    cursor = start
    while cursor <= end:
        stop = min(cursor + timedelta(days=days - 1), end)
        windows.append((cursor, stop))
        cursor = stop + timedelta(days=1)
    return windows


def render_sql(start: date, end: date) -> str:
    sql = (ROOT / 'sql' / '02_export_sessions.sql').read_text(encoding='utf-8')
    old = "_TABLE_SUFFIX BETWEEN '20201101' AND '20201107'"
    if old not in sql:
        raise ValueError('Expected date clause not found in SQL template')
    return sql.replace(old, f"_TABLE_SUFFIX BETWEEN '{start:%Y%m%d}' AND '{end:%Y%m%d}'")


def run_python(*params: str) -> None:
    subprocess.run([sys.executable, *params], cwd=ROOT, check=True)


def cmd_demo(_args: argparse.Namespace) -> None:
    run_python('scripts/build_demo.py')
    run_python('-m', 'pytest', '-q')
    run_python('scripts/generate_report.py')
    print('\nREADY: run `python scripts/sprint.py launch` to view your synthetic demonstration.')
    print('NEXT: run `python scripts/sprint.py sql` to generate real GA4 extraction queries.')


def cmd_sql(args: argparse.Namespace) -> None:
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    windows = date_ranges(start, end, args.days)
    folder = ROOT / args.output
    folder.mkdir(parents=True, exist_ok=True)
    manifest = []
    for a, b in windows:
        dest = folder / f'ga4_{a:%Y%m%d}_{b:%Y%m%d}.sql'
        dest.write_text(render_sql(a, b), encoding='utf-8')
        manifest.append({'start': a.isoformat(), 'end': b.isoformat(), 'sql_file': dest.name})
        print('Created', dest.relative_to(ROOT))
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Created {len(windows)} SQL batches. Run each in BigQuery Sandbox, then download CSV into data/ga4_exports/.')
    print('CSV exports may truncate sessions across date-window boundaries. Inspect QA and methodology notes.')


def cmd_ingest(args: argparse.Namespace) -> None:
    from cartclue.analytics import prepare_data
    from scripts.generate_report import generate

    folder = ROOT / args.folder
    files = sorted(folder.glob('*.csv'))
    if not files:
        raise SystemExit(f'No .csv files found in {folder}. Export BigQuery query results there first.')
    frames = []
    for path in files:
        frame = pd.read_csv(path, low_memory=False)
        frames.append(frame)
        print(f'Loaded {path.name}: {len(frame):,} rows')
    raw = pd.concat(frames, ignore_index=True)
    cleaned, qa = prepare_data(raw)
    if cleaned.empty:
        raise SystemExit('No usable sessions after validation. Inspect input schema.')

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(out, index=False, date_format='%Y-%m-%d')
    qa_path = ROOT / 'reports' / 'ga4_quality.json'
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    audit = {'source_files': [p.name for p in files], 'provenance': 'User-supplied GA4-format exports; verify they came from Google public BigQuery sample',
             'covered_dates': [str(cleaned.date.min().date()), str(cleaned.date.max().date())], **qa}
    qa_path.write_text(json.dumps(audit, indent=2), encoding='utf-8')
    report_path = ROOT / 'reports' / 'ga4_analysis.md'
    generate(out, report_path, 'User-supplied GA4-format query exports; verify provenance and public dataset window')
    print(f'Wrote validated data: {out.relative_to(ROOT)} ({len(cleaned):,} sessions)')
    print(f'Wrote QA audit: {qa_path.relative_to(ROOT)}')
    print(f'Wrote analysis: {report_path.relative_to(ROOT)}')
    if qa['duplicate_session_rows'] or qa['funnel_sequence_inconsistencies']:
        print('WARNING: duplicate keys or funnel inconsistencies detected. Investigate date-window boundaries and instrumentation before publishing metrics.')
    if args.publish_sample:
        k = min(args.sample_rows, len(cleaned))
        public = cleaned.sample(n=k, random_state=42).sort_values('date').reset_index(drop=True)
        # Never commit public GA4 pseudo-user/session identifiers to the repo.
        public['session_key'] = [f'public_ga4_{i:07d}' for i in range(1, k + 1)]
        dest = ROOT / 'data' / 'public_ga4_sessions.csv'
        public.to_csv(dest, index=False, date_format='%Y-%m-%d')
        print(f'Created public-demo sample: {dest.relative_to(ROOT)} ({k:,} sessions).')
        print('ATTENTION: It is a sample, not the complete dataset. Validate its provenance and report sampled denominators.')
    print('NEXT: open the dashboard, review actual results, and hand-verify three insights.')


def cmd_check(_args: argparse.Namespace) -> None:
    run_python('-m', 'pytest', '-q')
    run_python('-m', 'compileall', '-q', 'app.py', 'cartclue', 'scripts')
    print('Local test and syntax checks passed. Public deployment still requires separate browser verification.')


def cmd_launch(_args: argparse.Namespace) -> None:
    run_python('-m', 'streamlit', 'run', 'app.py')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='Build synthetic demo, run tests and generate report').set_defaults(fn=cmd_demo)
    q = sub.add_parser('sql', help='Generate ready-to-paste GA4 SQL date batches')
    q.add_argument('--start', default='2020-11-01')
    q.add_argument('--end', default='2020-12-12')
    q.add_argument('--days', type=int, default=7, help='days per SQL extract, default 7')
    q.add_argument('--output', default='sql/generated')
    q.set_defaults(fn=cmd_sql)
    i = sub.add_parser('ingest', help='Merge BigQuery CSV files, validate, report and optionally create public demo')
    i.add_argument('--folder', default='data/ga4_exports')
    i.add_argument('--output', default='data/ga4_sessions_clean.csv')
    i.add_argument('--publish-sample', action='store_true', help='Create a 20k-row ID-redacted public GA4-derived demo')
    i.add_argument('--sample-rows', type=int, default=20000)
    i.set_defaults(fn=cmd_ingest)
    sub.add_parser('check', help='Run automated tests and syntax checks').set_defaults(fn=cmd_check)
    sub.add_parser('launch', help='Launch the Streamlit dashboard').set_defaults(fn=cmd_launch)
    args = parser.parse_args()
    if getattr(args, 'sample_rows', 1) <= 0:
        parser.error('--sample-rows must be positive')
    args.fn(args)


if __name__ == '__main__':
    main()
