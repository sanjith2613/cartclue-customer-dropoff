-- CartClue Day 2 FIX | GA4 observed-event coverage (not a strict sequential funnel).
-- Query Google public GA4 sample. Start with one week; adjust ONLY the dates below.
-- Google obfuscation may result in event types missing or not matching across sessions.
-- For Nov 1-7 2020, add_to_cart is extremely sparse even though purchases occur.
-- Preserve observed purchase events/revenue; NEVER require add_to_cart for purchases.
-- Output: one row per user_pseudo_id + ga_session_id and a measurement_mode column.
-- An observed event *presence* is NOT proof of a completed ordered funnel step.
-- traffic_source.source means FIRST-USER attribution, not session attribution.
WITH raw AS (
  SELECT
    event_date,
    event_timestamp,
    event_name,
    user_pseudo_id,
    (SELECT ep.value.int_value
     FROM UNNEST(event_params) AS ep
     WHERE ep.key = 'ga_session_id'
     LIMIT 1) AS ga_session_id,
    device.category AS device,
    geo.country AS country,
    traffic_source.source AS first_user_source,
    ecommerce.purchase_revenue AS purchase_revenue
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
    AND event_name IN ('session_start', 'page_view', 'view_item', 'add_to_cart',
                       'begin_checkout', 'purchase')
),
valid_events AS (
  SELECT * FROM raw
  WHERE user_pseudo_id IS NOT NULL AND ga_session_id IS NOT NULL
),
by_session AS (
  SELECT
    CONCAT(user_pseudo_id, '-', CAST(ga_session_id AS STRING)) AS session_key,
    FORMAT_DATE('%Y-%m-%d', PARSE_DATE('%Y%m%d', MIN(event_date))) AS date,
    ARRAY_AGG(COALESCE(device, 'Unknown') ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS device,
    ARRAY_AGG(COALESCE(country, 'Unknown') ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS country,
    ARRAY_AGG(COALESCE(first_user_source, 'Unknown') ORDER BY event_timestamp LIMIT 1)[OFFSET(0)] AS first_user_source,
    COUNTIF(event_name = 'view_item') > 0 AS viewed_item,
    COUNTIF(event_name = 'add_to_cart') > 0 AS added_to_cart,
    COUNTIF(event_name = 'begin_checkout') > 0 AS began_checkout,
    COUNTIF(event_name = 'purchase') > 0 AS purchased,
    SUM(IF(event_name = 'purchase', COALESCE(purchase_revenue, 0), 0)) AS revenue
  FROM valid_events
  GROUP BY user_pseudo_id, ga_session_id
)
SELECT
  date, session_key, device, country, first_user_source,
  viewed_item, added_to_cart, began_checkout, purchased,
  revenue,
  'observed_events' AS measurement_mode
FROM by_session
ORDER BY date, session_key;
