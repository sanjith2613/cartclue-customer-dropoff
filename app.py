"""CartClue: customer funnel, anomaly and decision-support application.

Run: streamlit run app.py
All demo figures are synthetic. GA4 sample data requires your own CSV export.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from cartclue.analytics import (
    daily_metrics, funnel_table, event_reach_table, observed_events_mode,
    ml_anomalies, prepare_data, recommendations, revenue_scenario,
    segment_comparison, statistical_alerts,
)
from cartclue.demo import make_demo

st.set_page_config(page_title='CartClue — Customer Drop-Off Detective', page_icon='🛒', layout='wide')
DATA_PATH = Path(__file__).parent / 'data' / 'demo_sessions.csv'
PUBLIC_GA4_PATH = Path(__file__).parent / 'data' / 'public_ga4_sessions.csv'


@st.cache_data(show_spinner=False)
def read_demo():
    return pd.read_csv(DATA_PATH) if DATA_PATH.exists() else make_demo()


st.title('🛒 CartClue')
st.caption('Customer Drop-Off Detective · Funnel analytics · Statistical review · Anomaly screening')

with st.sidebar:
    st.header('1. Choose your data')
    bundled = ['SIMULATED example']
    if PUBLIC_GA4_PATH.exists():
        bundled.insert(0, 'GA4-derived public sample')
    selected = st.radio('Included dataset', bundled, horizontal=False,
                        help='Use the public sample only after verifying it was produced from Google public GA4 exports.')
    uploads = st.file_uploader('Or upload session-level GA4 CSV file(s)', type=['csv'], accept_multiple_files=True,
                               help='Export SQL 02 from BigQuery. Multiple slices are combined and deduplicated.')
    if uploads:
        try:
            raw = pd.concat([pd.read_csv(file) for file in uploads], ignore_index=True)
            source = 'Uploaded GA4-format export (verify source provenance)'
            source_mode = 'upload'
        except Exception as exc:
            st.error(f'Unable to read CSV(s): {exc}')
            st.stop()
    elif selected == 'GA4-derived public sample':
        raw = pd.read_csv(PUBLIC_GA4_PATH)
        source = 'PUBLIC SAMPLE from user-provided GA4-format data, with session identifiers replaced; verify source and sampling'
        source_mode = 'public_ga4_sample'
    else:
        raw = read_demo()
        source = 'SIMULATED DEMO DATA — not actual GA4 measurements'
        source_mode = 'simulated'
    try:
        df, qa = prepare_data(raw)
    except ValueError as exc:
        st.error(str(exc))
        st.info('Expected columns: date, session_key, device, country, first_user_source, viewed_item, '
                'added_to_cart, began_checkout, purchased, revenue.')
        st.stop()
    if df.empty:
        st.warning('No valid rows in this data. Check dates and session IDs.')
        st.stop()

    st.header('2. Explore segments')
    dates = st.date_input('Session date range', value=(df.date.min().date(), df.date.max().date()),
                          min_value=df.date.min().date(), max_value=df.date.max().date())
    devices = st.multiselect('Device', sorted(df.device.unique()), default=sorted(df.device.unique()))
    countries = st.multiselect('Country', sorted(df.country.unique()), default=sorted(df.country.unique()))
    sources = st.multiselect('First-user source', sorted(df.first_user_source.unique()),
                             default=sorted(df.first_user_source.unique()),
                             help='GA4 traffic_source.source represents first-user acquisition, not session attribution.')
    st.caption('Data provenance: ' + source)

if len(dates) == 2:
    start, end = pd.Timestamp(dates[0]), pd.Timestamp(dates[1])
    df = df[(df.date >= start) & (df.date <= end)]
df = df[df.device.isin(devices) & df.country.isin(countries) & df.first_user_source.isin(sources)].copy()
if df.empty:
    st.info('No sessions match these filters. Widen the selection in the sidebar.')
    st.stop()

if source_mode == 'simulated':
    st.warning('SIMULATED DEMO: All numbers are synthetic, including the deliberately introduced mobile checkout deterioration.')
elif source_mode == 'public_ga4_sample':
    st.info('GA4-DERIVED SAMPLE MODE: Session IDs are replaced and records may be a random subset. Verify provenance; totals represent the sampled dataset, not all original store traffic.')
else:
    st.info('GA4-FORMAT UPLOAD: If using Google’s public dataset, it is historical (2020-11-01 to 2021-01-31) and intentionally obfuscated. Verify source provenance.')

sessions = len(df)
orders = int(df.purchased.sum())
revenue = float(df.revenue.sum())
conversion = 100 * orders / sessions
avg_order = revenue / orders if orders else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric('Sessions', f'{sessions:,}')
k2.metric('Purchasing sessions', f'{orders:,}')
k3.metric('Session conversion', f'{conversion:.2f}%')
k4.metric('Recorded revenue', f'${revenue:,.0f}')
st.caption('Conversion = sessions with at least one purchase event / analyzed sessions. '
           'Recorded purchase-event revenue is not profit or a validated accounting total.')
if observed_events_mode(df):
    st.warning('EVENT COVERAGE MODE: Counts for views, cart, checkout, and purchase are INDEPENDENT event-presence counts, '
               'not a sequential funnel. Missing/inconsistent add-to-cart instrumentation makes a conventional drop-off funnel unreliable.')
elif source_mode != 'simulated' and orders == 0 and sessions > 1000:
    st.error('This file uses the OLD strict-funnel extraction and shows zero purchases. '
             'Use the Day 2 corrected SQL (02_export_sessions.sql) and re-export to preserve purchases and revenue.')

tab_overview, tab_journey, tab_segments, tab_alerts, tab_decisions, tab_quality = st.tabs([
    '📊 Overview', '🧭 Journey', '👥 Segments', '🚨 Anomalies', '🧪 Decision lab', '✅ Data quality'
])

with tab_overview:
    st.subheader('Business performance over time')
    daily = daily_metrics(df)
    st.plotly_chart(px.line(daily, x='date', y='conversion_pct', markers=True,
                            labels={'date': 'Date', 'conversion_pct': 'Session conversion (%)'},
                            title='Daily session purchase conversion'), use_container_width=True)
    st.plotly_chart(px.bar(daily, x='date', y='sessions', labels={'date': 'Date', 'sessions': 'Sessions'},
                           title='Sessions per day'), use_container_width=True)
    st.caption('Use consistent date windows and a sufficient sample size before interpreting short-run changes.')

with tab_journey:
    if observed_events_mode(df):
        st.subheader('Which events are actually recorded?')
        st.warning('This is an **event-coverage report**, NOT a sequential purchase funnel. '
                   'Each bar shows sessions containing that event. A session may have a purchase '
                   'without a recorded add-to-cart event, so subtracting adjacent rows would be misleading.')
        reach = event_reach_table(df)
        fig = px.bar(reach, x='sessions', y='event', orientation='h',
                     text='pct_of_all_sessions',
                     labels={'sessions': 'Sessions containing event', 'event': 'Recorded event',
                             'pct_of_all_sessions': '% of all sessions'},
                     title='Independent recorded event presence')
        fig.update_traces(texttemplate='%{text:.2f}% of sessions', textposition='outside', cliponaxis=False)
        fig.update_layout(height=400, yaxis={'categoryorder': 'array', 'categoryarray': list(reversed(reach.event.tolist()))})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(reach.rename(columns={'event':'Recorded event', 'sessions':'Sessions with event',
                                           'pct_of_all_sessions':'% of all sessions'}),
                     hide_index=True, use_container_width=True)
        if int(df.added_to_cart.sum()) < int(df.began_checkout.sum()):
            st.error(f'Event coverage warning: only {int(df.added_to_cart.sum()):,} session(s) have '
                     f'an add-to-cart event, but {int(df.began_checkout.sum()):,} have checkout events. '
                     'Do not calculate cart abandonment from this source.')
        st.caption('Observation is defined per pseudonymous composite session ID. Sessions can contain '
                   'different events without recording earlier stages. Instrumentation and GA4 obfuscation '
                   'can produce internally inconsistent customer journeys.')
    else:
        st.subheader('Where do sessions stop advancing?')
        fun = funnel_table(df)
        fig = go.Figure(go.Funnel(y=fun.stage, x=fun.sessions,
                                  textinfo='value+percent initial'))
        fig.update_layout(height=430, margin=dict(l=10,r=10,t=20,b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(fun.rename(columns={'stage':'Stage','sessions':'Sessions',
                                          'step_conversion_pct':'Step conversion %','dropoff':'Loss vs prior stage',
                                          'dropoff_pct':'Loss % vs prior stage'}),
                     hide_index=True, use_container_width=True)
        st.caption('Strict sequential funnel at session level. A missing event does not prove a shopper abandoned that stage. '
                   'The SQL uses first-event timestamps, which can undercount sessions with repeated or out-of-order events.')

with tab_segments:
    st.subheader('Which groups deserve closer investigation?')
    selection = st.radio('Compare by', ['Device', 'Country', 'First-user source'], horizontal=True)
    key = {'Device': 'device','Country':'country','First-user source':'first_user_source'}[selection]
    segment = segment_comparison(df, key)
    fig = px.bar(segment, x=key, y='conversion_pct', hover_data=['sessions','orders'],
                 labels={key:selection,'conversion_pct':'Conversion (%)'}, title=f'Conversion by {selection.lower()}')
    st.plotly_chart(fig, use_container_width=True)
    shown = segment.copy().round({'conversion_pct':2,'difference_vs_rest_pp':2,'p_value':4,'q_value_fdr':4})
    st.dataframe(shown, use_container_width=True, hide_index=True)
    st.caption('Each group is tested against all other sessions using a two-proportion z-test when the normal '
               'approximation is adequate. Benjamini–Hochberg correction is applied within the selected segmentation. '
               'Significance is not causality and low-volume groups should not drive decisions.')

with tab_alerts:
    st.subheader('Spot unusual historical changes')
    daily = daily_metrics(df)
    a = statistical_alerts(daily)
    if a.empty:
        st.info('Select at least 8 distinct dates for a 7-day statistical baseline.')
    else:
        st.dataframe(a.sort_values('date', ascending=False), use_container_width=True, hide_index=True)
        st.caption('A decline alert is a descriptive screen: daily conversion is below the preceding seven '
                   'observed days and unadjusted two-sided p<0.01. Repeated daily testing can produce false alerts.')
    st.markdown('#### Machine learning: Isolation Forest')
    anomalies = ml_anomalies(daily)
    if len(daily) < 30:
        st.info('The retrospective Isolation Forest screen requires at least 30 observed days. '
                'Load more GA4 date slices for this feature.')
    else:
        ml_fig = px.scatter(anomalies, x='date', y='conversion_pct', color='ml_anomaly',
                            size='sessions', hover_data=['revenue', 'anomaly_score'],
                            title='Exploratory outliers based on sessions, conversion and revenue')
        st.plotly_chart(ml_fig, use_container_width=True)
        st.dataframe(anomalies[anomalies.ml_anomaly].sort_values('anomaly_score', ascending=False),
                     hide_index=True, use_container_width=True)
        st.caption('Unsupervised in-sample screening, not a trained future predictor or a validated root-cause model.')

with tab_decisions:
    st.subheader('Translate metrics into testable business questions')
    for idx, rec in enumerate(recommendations(df), 1):
        with st.expander(f'{idx}. {rec["finding"]}', expanded=(idx == 1)):
            st.write('**Observed evidence:** ' + rec['evidence'])
            st.write('**Recommended investigation:** ' + rec['next_step'])
    st.markdown('#### What-if revenue opportunity (simulation only)')
    uplift = st.slider('Assumed absolute conversion-rate improvement (percentage points)',
                       min_value=0.0, max_value=2.0, value=0.5, step=0.1)
    sim = revenue_scenario(df, uplift)
    s1, s2, s3 = st.columns(3)
    s1.metric('Assumed future conversion', f'{sim["assumed_conversion_pct"]:.2f}%')
    s2.metric('Hypothetical added orders', f'{sim["estimated_extra_orders"]:,.1f}')
    if sim['revenue_usable']:
        s3.metric('Hypothetical extra revenue', f'${sim["hypothetical_extra_revenue"]:,.0f}')
    else:
        s3.metric('Revenue estimate', 'Unavailable')
    st.caption('Simple scenario = sessions × assumed absolute conversion uplift × recorded revenue per purchasing session. '
               'Assumes stable traffic and AOV; it is not observed revenue, profit, a causal lift estimate, or a forecast.')

with tab_quality:
    st.subheader('Data lineage and validation')
    st.write('**Data source:** ' + source)
    st.write(f'**Filtered coverage:** {df.date.min().date()} through {df.date.max().date()}')
    st.write('**Input quality before dashboard filters:**')
    st.dataframe(pd.DataFrame([qa]).T.rename(columns={0:'Value'}), use_container_width=True)
    st.write('**Core grain:** one row per composite GA4 session identifier, not one row per person or visit event.')
    if observed_events_mode(df):
        st.write('**Measurement definition:** Event presence in a composite session, with NO stage-order requirement. '
                 'Cart, checkout and purchase events may not be nested. Compare each to total sessions, '
                 'not to the immediately preceding bar.')
        st.write('**Tracking note:** The public obfuscated GA4 sample contains sparse add-to-cart activity '
                 'for this interval; that is a source coverage limitation, not verified abandonment.')
    else:
        st.write('**Strict funnel assumption:** product view → add to cart → checkout → purchase in the same session.')
    st.write('**Data caveats:** session IDs can be missing, cross-date exports may truncate journeys, '
             'attribution is first-user, and obfuscated GA4 fields may not reconcile perfectly.')
    st.markdown('See `docs/METHODOLOGY.md` in the repository for definitions, quality and evaluation plans.')
    st.download_button('Download filtered analysis data', data=df.to_csv(index=False).encode('utf-8'),
                       file_name='cartclue_filtered_sessions.csv', mime='text/csv')

st.divider()
st.caption('Built as an educational portfolio project. Findings are descriptive; validate tracking and run experiments before making causal claims.')
