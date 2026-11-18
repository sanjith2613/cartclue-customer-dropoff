"""Generate a reproducible synthetic demo CSV."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cartclue.demo import make_demo

if __name__ == '__main__':
    output = Path(__file__).resolve().parents[1] / 'data' / 'demo_sessions.csv'
    output.parent.mkdir(parents=True, exist_ok=True)
    demo = make_demo()
    demo.to_csv(output, index=False)
    print(f'Wrote {len(demo):,} SIMULATED sessions to {output}')
