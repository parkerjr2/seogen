-- Increase M Electric subscription limits to accommodate actual usage
-- Current usage: 2,752 pages
-- Current limit: 1,000 pages
-- New limit: 5,000 pages (room for growth)

UPDATE subscriptions
SET 
  page_limit = 5000,              -- Increase from 1,000 to 5,000
  monthly_generation_limit = 5000, -- Increase monthly limit too
  updated_at = NOW()
WHERE id = (
  SELECT subscription_id 
  FROM api_keys 
  WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
);

-- Verify the update
SELECT 
  s.id,
  s.plan_name,
  s.page_limit,
  s.monthly_generation_limit,
  s.status,
  (
    SELECT COUNT(*) 
    FROM usage_logs ul 
    WHERE ul.api_key_id = a.id 
    AND ul.action IN ('ai_page_generation_success', 'bulk_item_generation_success')
  ) as actual_pages_used,
  s.page_limit - (
    SELECT COUNT(*) 
    FROM usage_logs ul 
    WHERE ul.api_key_id = a.id 
    AND ul.action IN ('ai_page_generation_success', 'bulk_item_generation_success')
  ) as pages_remaining
FROM subscriptions s
JOIN api_keys a ON a.subscription_id = s.id
WHERE a.key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';
