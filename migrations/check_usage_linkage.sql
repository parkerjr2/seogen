-- Check if usage_logs are linked to the correct api_key_id

-- 1. What api_key_id are the usage logs using?
SELECT 
  'Usage Logs API Key IDs' as check_type,
  api_key_id,
  COUNT(*) as page_count
FROM usage_logs
WHERE action IN ('ai_page_generation_success', 'bulk_item_generation_success')
GROUP BY api_key_id
ORDER BY page_count DESC
LIMIT 5;

-- 2. Check if the usage logs api_key_id matches our API key
SELECT 
  'Matching Check' as check_type,
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM usage_logs 
      WHERE api_key_id = '823e0480-feb6-4cf0-92ef-d24ae718fb56'
      AND action IN ('ai_page_generation_success', 'bulk_item_generation_success')
    ) THEN 'YES - Usage logs match API key'
    ELSE 'NO - Usage logs use different api_key_id'
  END as result;

-- 3. If they don't match, we need to update usage_logs to use the correct api_key_id
-- First, let's see what api_key_id the usage logs are currently using
SELECT 
  'Current Usage Logs' as check_type,
  ul.api_key_id as current_api_key_id,
  COUNT(*) as page_count,
  a.key as api_key_value
FROM usage_logs ul
LEFT JOIN api_keys a ON a.id = ul.api_key_id
WHERE ul.action IN ('ai_page_generation_success', 'bulk_item_generation_success')
GROUP BY ul.api_key_id, a.key
ORDER BY page_count DESC;
