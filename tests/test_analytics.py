import numpy as np
import pandas as pd
import pytest

from cartclue.analytics import (
    prepare_data, funnel_table, daily_metrics, segment_comparison, statistical_alerts,
    ml_anomalies, revenue_scenario, proportion_pvalue,
    event_reach_table, observed_events_mode,
)
from cartclue.demo import make_demo


def sample():
    return pd.DataFrame([
        ['2020-11-01','a','mobile','US','google', True,True,True,True, 45],
        ['2020-11-01','b','desktop','US','direct', True,True,False,False, 0],
        ['2020-11-02','c','mobile','CA','google', True,False,False,False, 0],
        ['2020-11-02','d','desktop','CA','direct', False,False,False,False, 0],
    ], columns=['date','session_key','device','country','first_user_source',
                'viewed_item','added_to_cart','began_checkout','purchased','revenue'])


def test_prepare_and_funnel():
    df, qa = prepare_data(sample())
    assert qa['usable_sessions'] == 4
    assert funnel_table(df).sessions.tolist() == [4,3,2,1,1]


def test_dates_and_daily():
    df, _ = prepare_data(sample())
    d = daily_metrics(df)
    assert len(d) == 2
    assert d.orders.tolist() == [1,0]
    assert d.conversion_pct.iloc[0] == 50


def test_duplicate_detection():
    frame = pd.concat([sample(), sample().iloc[[0]]], ignore_index=True)
    _, qa = prepare_data(frame)
    assert qa['duplicate_session_rows'] == 1


def test_out_of_order_funnel_rejected():
    frame = sample()
    frame.loc[3, 'purchased'] = True
    frame.loc[3, 'revenue'] = 99
    df, qa = prepare_data(frame)
    assert qa['funnel_sequence_inconsistencies'] == 1
    assert df.purchased.sum() == 1
    assert qa['revenue_excluded_from_strict_funnel'] == 99


def test_missing_column_rejected():
    with pytest.raises(ValueError, match='Missing columns'):
        prepare_data(sample().drop(columns=['date']))


def test_segments_sum_to_total():
    df, _ = prepare_data(sample())
    groups = segment_comparison(df, 'device')
    assert groups.sessions.sum() == len(df)
    assert groups.orders.sum() == df.purchased.sum()


def test_prop_test_small_counts_unknown():
    assert np.isnan(proportion_pvalue(1,5,2,8))
    assert proportion_pvalue(100,1000,300,1000) < 0.001


def test_scenario_is_not_observed_revenue():
    df, _ = prepare_data(sample())
    out = revenue_scenario(df, 1.0)
    assert out['hypothetical_extra_revenue'] > 0
    assert out['aov'] == 45


def test_demo_determinism_and_ml():
    one, _ = prepare_data(make_demo(days=42, sessions_per_day=200, seed=7))
    two, _ = prepare_data(make_demo(days=42, sessions_per_day=200, seed=7))
    assert one.equals(two)
    d = daily_metrics(one)
    assert len(d) == 42
    assert len(statistical_alerts(d)) == 35
    ml = ml_anomalies(d)
    assert ml.ml_anomaly.any()


def test_ga4_event_presence_retains_purchases_and_revenue_without_cart():
    frame = sample()
    frame["measurement_mode"] = "observed_events"
    frame.loc[3, "purchased"] = True
    frame.loc[3, "revenue"] = 99
    df, qa = prepare_data(frame)
    assert observed_events_mode(df)
    assert int(df.purchased.sum()) == 2
    assert float(df.revenue.sum()) == 144
    assert qa["purchase_without_checkout_event_sessions"] == 1
    assert qa["funnel_sequence_inconsistencies"] == 0  # not a funnel
    assert qa["sessions_with_non_nested_event_flags"] >= 1
    with pytest.raises(ValueError, match="sequential funnel"):
        funnel_table(df)


def test_observed_event_reach_uses_all_sessions_as_denominator():
    frame = sample()
    frame["measurement_mode"] = "observed_events"
    frame.loc[3, "purchased"] = True
    frame.loc[3, "revenue"] = 99
    df, _ = prepare_data(frame)
    r = event_reach_table(df)
    assert r.sessions.tolist() == [4, 3, 2, 1, 2]
    assert r.pct_of_all_sessions.tolist() == [100.0, 75.0, 50.0, 25.0, 50.0]


def test_mixing_old_and_new_csv_is_rejected():
    frame = sample()
    frame["measurement_mode"] = ["strict", "observed_events", "strict", "observed_events"]
    with pytest.raises(ValueError, match="mixed measurement_mode"):
        prepare_data(frame)


def test_revenue_scenario_after_ga4_event_presence():
    frame = sample()
    frame["measurement_mode"] = "observed_events"
    frame.loc[3, "purchased"] = True
    frame.loc[3, "revenue"] = 99
    df, _ = prepare_data(frame)
    out = revenue_scenario(df, 0.5)
    assert out["aov"] == 72.0
    assert out["revenue_usable"] is True
