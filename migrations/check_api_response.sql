-- Check what the backend API should be returning for /validate-license

-- 1. Verify API key exists and is linked to subscription
SELECT 
  'API Key Lookup' as check_type,
  a.id as api_key_id,
  a.key as license_key,
  a.subscription_id,
  a.status as api_key_status,
  s.page_limit,
  s.monthly_generation_limit,
  s.status as subscription_status
FROM api_keys a
LEFT JOIN subscriptions s ON s.id = a.subscription_id
WHERE a.key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';

-- 2. Check if there are multiple API keys for this license
SELECT 
  'All Matching Keys' as check_type,
  COUNT(*) as count,
  STRING_AGG(id::text, ', ') as api_key_ids
FROM api_keys
WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';

-- 3. Check legacy licenses table
SELECT 
  'Legacy Licenses Table' as check_type,
  id,
  license_key,
  status,
  credits_remaining
FROM licenses
WHERE license_key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';

-- 4. Count actual usage
SELECT 
  'Usage Count' as check_type,
  COUNT(*) as total_pages_in_usage_logs
FROM usage_logs
WHERE api_key_id IN (
  SELECT id FROM api_keys WHERE key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
)
AND action IN ('ai_page_generation_success', 'bulk_item_generation_success');
