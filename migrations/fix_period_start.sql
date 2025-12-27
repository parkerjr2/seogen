-- Check and fix the current_period_start date
-- If it's set to NOW(), all historical pages won't count toward this period

-- 1. Check current period_start and when pages were actually generated
SELECT 
  'Period Analysis' as status,
  s.current_period_start,
  MIN(ul.created_at) as first_page_generated,
  MAX(ul.created_at) as last_page_generated,
  COUNT(*) as total_pages,
  COUNT(*) FILTER (WHERE ul.created_at >= s.current_period_start) as pages_in_current_period,
  COUNT(*) FILTER (WHERE ul.created_at < s.current_period_start) as pages_before_period
FROM subscriptions s
JOIN api_keys a ON a.subscription_id = s.id
LEFT JOIN usage_logs ul ON ul.api_key_id = a.id 
  AND ul.action IN ('ai_page_generation_success', 'bulk_item_generation_success')
WHERE a.key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
GROUP BY s.current_period_start;

-- 2. Fix: Set period_start to when the first page was generated
-- This will make all historical pages count toward the current period
UPDATE subscriptions
SET 
  current_period_start = (
    SELECT MIN(ul.created_at)
    FROM usage_logs ul
    JOIN api_keys a ON a.subscription_id = subscriptions.id
    WHERE ul.api_key_id = a.id
    AND ul.action IN ('ai_page_generation_success', 'bulk_item_generation_success')
  ),
  updated_at = NOW()
WHERE id = (
  SELECT subscription_id 
  FROM api_keys 
  WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
);

-- 3. Verify the fix
SELECT 
  'After Fix' as status,
  s.current_period_start,
  COUNT(*) as total_pages,
  COUNT(*) FILTER (WHERE ul.created_at >= s.current_period_start) as pages_this_period,
  s.monthly_generation_limit - COUNT(*) FILTER (WHERE ul.created_at >= s.current_period_start) as monthly_remaining
FROM subscriptions s
JOIN api_keys a ON a.subscription_id = s.id
LEFT JOIN usage_logs ul ON ul.api_key_id = a.id 
  AND ul.action IN ('ai_page_generation_success', 'bulk_item_generation_success')
WHERE a.key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
GROUP BY s.current_period_start, s.monthly_generation_limit;
