-- Diagnostic query to check M Electric license setup and usage
-- Run this to see what the system is actually seeing

-- 1. Check if API key exists
SELECT 
  'API Key Found' as status,
  id,
  key,
  name,
  status,
  subscription_id
FROM api_keys
WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';

-- 2. Check subscription details
SELECT 
  'Subscription Details' as status,
  s.id,
  s.plan_name,
  s.page_limit,
  s.monthly_generation_limit,
  s.current_period_start,
  s.status
FROM subscriptions s
JOIN api_keys a ON a.subscription_id = s.id
WHERE a.key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';

-- 3. Count total usage
SELECT 
  'Total Usage Count' as status,
  COUNT(*) as total_pages_generated,
  COUNT(CASE WHEN action = 'ai_page_generation_success' THEN 1 END) as individual_pages,
  COUNT(CASE WHEN action = 'bulk_item_generation_success' THEN 1 END) as bulk_pages
FROM usage_logs
WHERE api_key_id = (
  SELECT id FROM api_keys WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
)
AND action IN ('ai_page_generation_success', 'bulk_item_generation_success');

-- 4. Count usage this period
SELECT 
  'This Period Usage' as status,
  COUNT(*) as pages_this_period,
  MIN(created_at) as first_page,
  MAX(created_at) as last_page
FROM usage_logs
WHERE api_key_id = (
  SELECT id FROM api_keys WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
)
AND action IN ('ai_page_generation_success', 'bulk_item_generation_success')
AND created_at >= (
  SELECT current_period_start 
  FROM subscriptions 
  WHERE id = (
    SELECT subscription_id 
    FROM api_keys 
    WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
  )
);

-- 5. Show recent usage logs
SELECT 
  'Recent Usage Logs' as status,
  created_at,
  action,
  details->>'service' as service,
  details->>'city' as city,
  details->>'canonical_key' as canonical_key
FROM usage_logs
WHERE api_key_id = (
  SELECT id FROM api_keys WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
)
ORDER BY created_at DESC
LIMIT 10;

-- 6. Calculate what WordPress should see
SELECT 
  'Expected WordPress Display' as status,
  s.page_limit as total_limit,
  COALESCE(usage.total_pages, 0) as pages_used,
  s.page_limit - COALESCE(usage.total_pages, 0) as pages_remaining,
  s.monthly_generation_limit as monthly_limit,
  COALESCE(usage.period_pages, 0) as monthly_used,
  s.monthly_generation_limit - COALESCE(usage.period_pages, 0) as monthly_remaining
FROM subscriptions s
JOIN api_keys a ON a.subscription_id = s.id
LEFT JOIN (
  SELECT 
    api_key_id,
    COUNT(*) FILTER (WHERE action IN ('ai_page_generation_success', 'bulk_item_generation_success')) as total_pages,
    COUNT(*) FILTER (WHERE action IN ('ai_page_generation_success', 'bulk_item_generation_success') 
      AND created_at >= (SELECT current_period_start FROM subscriptions WHERE id = (SELECT subscription_id FROM api_keys WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'))
    ) as period_pages
  FROM usage_logs
  WHERE api_key_id = (SELECT id FROM api_keys WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc')
  GROUP BY api_key_id
) usage ON usage.api_key_id = a.id
WHERE a.key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';
