-- CartClue | Lesson 1: Explore GA4 event volume and instrumentation.
-- This example scans just seven daily tables to protect free quota.
SELECT
  event_date,
  event_name,
  COUNT(*) AS events,
  COUNT(DISTINCT user_pseudo_id) AS users_with_anonymous_ids
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20201107'
  AND event_name IN ('session_start','view_item','add_to_cart','begin_checkout','purchase')
GROUP BY 1, 2
ORDER BY event_date, events DESC;
