"""OPTIONAL: authenticated BigQuery -> CSV automation, with no paid AI API.

Requires:
  pip install -r requirements-bigquery-optional.txt
  Install Google Cloud CLI and run `gcloud auth application-default login`.
  Use a project in BigQuery Sandbox to avoid enabling paid billing.

Example:
  python scripts/fetch_bigquery.py --project YOUR_SANDBOX_PROJECT_ID \
    --start 2020-11-01 --end 2020-12-12 --batch-days 7

Queries Google public historical data. Google Cloud Sandbox/free-tier quotas apply.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sprint import ROOT, date_ranges, render_sql


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--project', required=True, help='Your own Google Cloud BigQuery Sandbox project ID')
    ap.add_argument('--start', default='2020-11-01')
    ap.add_argument('--end', default='2020-12-12')
    ap.add_argument('--batch-days', type=int, default=7)
    ap.add_argument('--max-gib-per-query', type=float, default=2.0)
    ap.add_argument('--output', default='data/ga4_exports')
    args = ap.parse_args()
    if args.max_gib_per_query <= 0:
        ap.error('--max-gib-per-query must be > 0')
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise SystemExit('Install optional dependency: pip install -r requirements-bigquery-optional.txt') from exc
    try:
        client = bigquery.Client(project=args.project)
    except Exception as exc:
        raise SystemExit('Google Cloud login failed. Check `gcloud auth application-default login`, project ID and BigQuery API.') from exc
    windows = date_ranges(date.fromisoformat(args.start), date.fromisoformat(args.end), args.batch_days)
    folder = ROOT / args.output
    folder.mkdir(parents=True, exist_ok=True)
    cap = int(args.max_gib_per_query * 1024 ** 3)
    for a, b in windows:
        sql = render_sql(a, b)
        name = f'ga4_sessions_{a:%Y%m%d}_{b:%Y%m%d}.csv'
        path = folder / name
        if path.exists():
            print(f'SKIP existing export {name}; delete it if you need to regenerate.')
            continue
        dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
        estimated = int(dry.total_bytes_processed or 0)
        print(f'{a} to {b}: estimated {estimated/1024**3:.2f} GiB of data scanned')
        if estimated > cap:
            raise SystemExit(f'Query would process more than {args.max_gib_per_query} GiB. '
                             'Reduce --batch-days or increase cap after checking Sandbox quota.')
        config = bigquery.QueryJobConfig(maximum_bytes_billed=cap)
        job = client.query(sql, job_config=config)
        rows = job.result(page_size=1000)
        columns = [field.name for field in rows.schema]
        if not columns:
            raise SystemExit(f'BigQuery returned no schema for {name}')
        # Write incomplete output as .partial until query and streaming succeed.
        temp = path.with_suffix('.partial')
        count = 0
        with temp.open('w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([row[col] for col in columns])
                count += 1
        temp.replace(path)
        print(f'Saved {name}: {count:,} session rows')
    print('Next: python scripts/sprint.py ingest --folder data/ga4_exports --publish-sample')
    print('WARNING: partial session journeys at batch boundaries can affect funnel counts; inspect QA notes.')


if __name__ == '__main__':
    main()
