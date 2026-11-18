"""Testable, deterministic analysis layer for CartClue.

All results are descriptive or hypothesis-generating; none establishes causality.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

STAGE_NAMES = [
    ("Sessions", None),
    ("Product views", "viewed_item"),
    ("Added to cart", "added_to_cart"),
    ("Checkout started", "began_checkout"),
    ("Purchased", "purchased"),
]
REQUIRED = {
    "date", "session_key", "device", "country", "first_user_source",
    "viewed_item", "added_to_cart", "began_checkout", "purchased", "revenue",
}
STAGE_COLS = ["viewed_item", "added_to_cart", "began_checkout", "purchased"]


def _boolean(series: pd.Series) -> pd.Series:
    """Normalize boolean CSV exports including BigQuery TRUE/FALSE strings."""
    return series.astype("string").str.lower().str.strip().isin(["true", "1", "yes"])


def prepare_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Validate session-level exports. Preserve nonsequential GA4 observed-event reach."""
    missing = sorted(REQUIRED.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    mode_field = "measurement_mode"
    if mode_field in frame.columns:
        modes = set(frame[mode_field].fillna("strict").astype(str).str.strip())
        if not modes.issubset({"strict", "observed_events"}) or len(modes) != 1:
            raise ValueError("Unknown or mixed measurement_mode values. Do not mix old strict-funnel CSVs with new observed-event CSVs.")
        mode = next(iter(modes))
    else:
        mode = "strict"
    result = frame[list(sorted(REQUIRED))].copy()
    result["measurement_mode"] = mode
    input_count = len(result)
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.normalize()
    result["session_key"] = result["session_key"].astype("string").str.strip()
    invalid_key = (result["session_key"].isna() | (result["session_key"] == ""))
    invalid_date = result["date"].isna()
    excluded = int((invalid_key | invalid_date).sum())
    result = result.loc[~(invalid_key | invalid_date)].copy()
    duplicate_sessions = int(result.duplicated("session_key").sum())
    result = result.drop_duplicates("session_key", keep="first")
    for name in ["device", "country", "first_user_source"]:
        result[name] = result[name].fillna("Unknown").astype(str).str.strip()
        result.loc[result[name].isin(["", "nan", "None", "<Other>"]), name] = "Unknown"
    for name in STAGE_COLS:
        result[name] = _boolean(result[name])
    result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce")
    missing_revenue = int(result["revenue"].isna().sum())
    negative_revenue = int((result["revenue"] < 0).sum())
    result["revenue"] = result["revenue"].fillna(0).clip(lower=0)
    # Old demonstration data uses strictly nested funnel flags. GA4 exports in
    # observed_events mode are different: each flag means an event was observed,
    # regardless of whether earlier events were recorded in that session.
    recorded = result["purchased"].copy()
    if mode == "strict":
        previous = pd.Series(True, index=result.index)
        inconsistencies = pd.Series(False, index=result.index)
        for name in STAGE_COLS:
            original = result[name].copy()
            inconsistencies |= original & ~previous
            result[name] = original & previous
            previous = result[name]
        excluded_revenue = float(result.loc[recorded & ~result["purchased"], "revenue"].sum())
        result.loc[~result["purchased"], "revenue"] = 0.0
    else:
        inconsistencies = pd.Series(False, index=result.index)
        excluded_revenue = 0.0
    nonnested = (result["purchased"] & ~result["began_checkout"]) | (result["began_checkout"] & ~result["added_to_cart"]) | (result["added_to_cart"] & ~result["viewed_item"])
    qa = {
        "input_rows": input_count, "usable_sessions": len(result),
        "missing_key_or_date": excluded, "duplicate_session_rows": duplicate_sessions,
        "funnel_sequence_inconsistencies": int(inconsistencies.sum()),
        "unusable_or_missing_revenue": missing_revenue,
        "negative_revenue_rows": negative_revenue,
        "revenue_excluded_from_strict_funnel": round(excluded_revenue, 2),
        "measurement_mode": mode,
        "sessions_with_non_nested_event_flags": int(nonnested.sum()),
        "purchase_without_checkout_event_sessions": int((result["purchased"] & ~result["began_checkout"]).sum()),
        "checkout_without_cart_event_sessions": int((result["began_checkout"] & ~result["added_to_cart"]).sum()),
        "sessions_with_add_to_cart_event": int(result["added_to_cart"].sum()),
    }
    return result.sort_values("date").reset_index(drop=True), qa


def observed_events_mode(df: pd.DataFrame) -> bool:
    return "measurement_mode" in df.columns and df["measurement_mode"].eq("observed_events").all()


def event_reach_table(df: pd.DataFrame) -> pd.DataFrame:
    """Nonsequential GA4 event presence. All percentages use total session denominator."""
    stages = [("Sessions", None), ("Product view event", "viewed_item"),
              ("Add-to-cart event", "added_to_cart"),
              ("Begin-checkout event", "began_checkout"),
              ("Purchase event", "purchased")]
    total = len(df)
    return pd.DataFrame([
        {"event": title, "sessions": total if col is None else int(df[col].sum()),
         "pct_of_all_sessions": round(100 * (total if col is None else int(df[col].sum())) / total, 2) if total else float("nan")}
        for title, col in stages
    ])


def funnel_table(df: pd.DataFrame) -> pd.DataFrame:
    if observed_events_mode(df):
        raise ValueError("A sequential funnel cannot be computed from non-nested observed-event flags; use event_reach_table instead.")
    if df.empty:
        return pd.DataFrame(columns=["stage", "sessions", "step_conversion_pct", "dropoff", "dropoff_pct"])
    counts = [len(df)] + [int(df[c].sum()) for c in STAGE_COLS]
    result = []
    for i, (label, _) in enumerate(STAGE_NAMES):
        prior = counts[i - 1] if i else counts[0]
        count = counts[i]
        result.append({
            "stage": label,
            "sessions": count,
            "step_conversion_pct": round(count / prior * 100, 2) if prior else np.nan,
            "dropoff": prior - count if i else 0,
            "dropoff_pct": round((prior - count) / prior * 100, 2) if prior and i else 0,
        })
    return pd.DataFrame(result)


def daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "sessions", "orders", "revenue", "conversion_pct", "aov"])
    d = df.groupby("date", as_index=False).agg(
        sessions=("session_key", "size"),
        orders=("purchased", "sum"),
        revenue=("revenue", "sum"),
    ).sort_values("date")
    d["conversion_pct"] = np.where(d.sessions > 0, d.orders / d.sessions * 100, 0)
    d["aov"] = np.where(d.orders > 0, d.revenue / d.orders, 0)
    return d


def proportion_pvalue(x1: int, n1: int, x2: int, n2: int) -> float:
    """Two-sided pooled two-proportion z-test; NaN if approximation is unsafe."""
    if n1 <= 0 or n2 <= 0:
        return float("nan")
    pooled = (x1 + x2) / (n1 + n2)
    if min(n1 * pooled, n1 * (1 - pooled), n2 * pooled, n2 * (1 - pooled)) < 5:
        return float("nan")
    se = np.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return float("nan")
    return float(2 * norm.sf(abs((x1 / n1 - x2 / n2) / se)))


def _bh_adjust(pvals: pd.Series) -> pd.Series:
    """Benjamini-Hochberg FDR correction across all tested segments."""
    adjusted = pd.Series(float("nan"), index=pvals.index, dtype=float)
    valid = pvals.dropna().sort_values()
    m = len(valid)
    if not m:
        return adjusted
    q = (valid.to_numpy() * m / np.arange(1, m + 1))
    q = np.minimum.accumulate(q[::-1])[::-1]
    adjusted.loc[valid.index] = np.minimum(1, q)
    return adjusted


def segment_comparison(df: pd.DataFrame, column: str, min_sessions: int = 30) -> pd.DataFrame:
    if column not in ["device", "country", "first_user_source"]:
        raise ValueError("Invalid segmentation column")
    if df.empty:
        return pd.DataFrame()
    total_n, total_o = len(df), int(df["purchased"].sum())
    result = df.groupby(column).agg(
        sessions=("session_key", "size"), orders=("purchased", "sum"), revenue=("revenue", "sum")
    ).reset_index()
    result["conversion_pct"] = result["orders"] / result["sessions"] * 100
    result["difference_vs_rest_pp"] = [
        100 * (int(r.orders) / int(r.sessions) - (total_o - int(r.orders)) / (total_n - int(r.sessions)))
        if total_n > int(r.sessions) else np.nan
        for _, r in result.iterrows()
    ]
    result["p_value"] = [
        proportion_pvalue(int(r.orders), int(r.sessions), total_o - int(r.orders), total_n - int(r.sessions))
        if int(r.sessions) >= min_sessions and total_n - int(r.sessions) >= min_sessions else np.nan
        for _, r in result.iterrows()
    ]
    result["q_value_fdr"] = _bh_adjust(result["p_value"])
    result["flag_for_review"] = (result["q_value_fdr"] < 0.05) & (result["sessions"] >= min_sessions)
    return result.sort_values("sessions", ascending=False).reset_index(drop=True)


def statistical_alerts(daily: pd.DataFrame, lookback: int = 7) -> pd.DataFrame:
    """Compare each day with the preceding lookback *observed* days.

    Significance is screening evidence, not diagnosis. The app shows only declines.
    """
    work = daily.sort_values("date").copy().reset_index(drop=True)
    out = []
    for i in range(len(work)):
        today = work.iloc[i]
        if i < lookback:
            continue
        previous = work.iloc[i - lookback:i]
        p = proportion_pvalue(int(today.orders), int(today.sessions), int(previous.orders.sum()), int(previous.sessions.sum()))
        baseline = previous.orders.sum() / previous.sessions.sum() * 100 if previous.sessions.sum() else np.nan
        delta = float(today.conversion_pct - baseline)
        out.append({
            "date": today.date, "sessions": int(today.sessions),
            "conversion_pct": float(today.conversion_pct), "baseline_pct": float(baseline),
            "change_pp": delta, "p_value": p,
            "decline_alert": bool(pd.notna(p) and p < 0.01 and delta < 0 and today.sessions >= 50),
        })
    return pd.DataFrame(out, columns=["date", "sessions", "conversion_pct", "baseline_pct", "change_pp", "p_value", "decline_alert"])


def ml_anomalies(daily: pd.DataFrame) -> pd.DataFrame:
    """Retrospective unsupervised IsolationForest screening, not forecasting."""
    output = daily[["date", "sessions", "orders", "revenue", "conversion_pct"]].copy()
    output["ml_anomaly"] = False
    output["anomaly_score"] = np.nan
    if len(output) < 30:
        return output
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    x = output[["sessions", "conversion_pct", "revenue"]].fillna(0).to_numpy()
    x = StandardScaler().fit_transform(x)
    model = IsolationForest(n_estimators=150, contamination=0.10, random_state=42)
    output["ml_anomaly"] = model.fit_predict(x) == -1
    output["anomaly_score"] = -model.decision_function(x)
    return output


def recommendations(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    if observed_events_mode(df):
        cart_count = int(df["added_to_cart"].sum())
        checkout_count = int(df["began_checkout"].sum())
        purchase_count = int(df["purchased"].sum())
        suggestions = [{
            "priority": "Validate instrumentation",
            "finding": "Add-to-cart tracking may be incomplete",
            "evidence": f"{cart_count:,} sessions have an add-to-cart event versus {checkout_count:,} with a checkout-start event and {purchase_count:,} with a purchase event.",
            "next_step": "Audit event implementation and session attribution. Do not interpret these independent event counts as sequential conversion or abandonment.",
        }]
    else:
        funnel = funnel_table(df)
        drop = funnel.iloc[1:].sort_values("dropoff", ascending=False).iloc[0]
        suggestions = [{
            "priority": "Investigate",
            "finding": f"Largest absolute observed loss: before {drop['stage'].lower()}",
            "evidence": f"{int(drop['dropoff']):,} sessions did not advance to this stage ({drop['dropoff_pct']:.1f}% of the prior step).",
            "next_step": "Verify event instrumentation and check product UX, traffic intent, and device-specific paths. Treat this as a hypothesis, not a proven cause.",
        }]
    for col, display in [("device", "device"), ("country", "country"), ("first_user_source", "first-user source")]:
        segments = segment_comparison(df, col)
        if segments.empty:
            continue
        strong = segments[(segments.flag_for_review) & (segments.difference_vs_rest_pp < 0)]
        if len(strong):
            r = strong.sort_values("difference_vs_rest_pp").iloc[0]
            suggestions.append({
                "priority": "Test",
                "finding": f"Lower conversion for {display}: {r[col]}",
                "evidence": f"{int(r.sessions):,} sessions; {r.conversion_pct:.2f}% conversion, {r.difference_vs_rest_pp:.2f} pp vs the rest (FDR q={r.q_value_fdr:.3g}).",
                "next_step": "Investigate composition and tracking; design a controlled A/B experiment before claiming improvements.",
            })
    if not df["revenue"].sum():
        suggestions.append({
            "priority": "Validate",
            "finding": "Purchase revenue is zero or unavailable",
            "evidence": "Revenue cannot be estimated accurately from this selected data.",
            "next_step": "Audit GA4 ecommerce.purchase_revenue and event coverage before using the opportunity simulator.",
        })
    return suggestions


def revenue_scenario(df: pd.DataFrame, absolute_uplift_pp: float) -> dict:
    sessions, orders = len(df), int(df["purchased"].sum()) if len(df) else 0
    revenue = float(df["revenue"].sum()) if len(df) else 0.0
    aov = revenue / orders if orders else 0.0
    base = orders / sessions * 100 if sessions else 0.0
    target = min(100.0, base + max(0.0, float(absolute_uplift_pp)))
    extra = max(0, (target - base) / 100 * sessions)
    return {
        "baseline_conversion_pct": base, "assumed_conversion_pct": target,
        "aov": aov, "estimated_extra_orders": extra,
        "hypothetical_extra_revenue": extra * aov, "revenue_usable": aov > 0,
    }
