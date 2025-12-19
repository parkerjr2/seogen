-- Fix usage_logs to reference correct api_key IDs
-- This updates any usage_logs that still reference old license IDs

-- The migration kept the same IDs when creating api_keys from licenses,
-- so the api_key_id values should match the old license_id values.
-- This script ensures all usage_logs point to valid api_keys.

-- Step 1: Check current state
SELECT 
  'Before Fix' as status,
  COUNT(*) as total_logs,
  COUNT(DISTINCT api_key_id) as unique_api_keys
FROM usage_logs;

-- Step 2: Verify that api_key IDs match old license IDs
-- (They should, since we used the same ID in the migration)
SELECT 
  'API Keys' as table_name,
  id,
  key,
  created_at
FROM api_keys
ORDER BY created_at;

-- Step 3: Check for any orphaned usage_logs (shouldn't be any if migration worked)
SELECT 
  'Orphaned Logs' as status,
  COUNT(*) as count
FROM usage_logs ul
WHERE NOT EXISTS (
  SELECT 1 FROM api_keys ak WHERE ak.id = ul.api_key_id
);

-- Step 4: If there are orphaned logs, this would fix them
-- (Only run if you see orphaned logs from Step 3)
-- UPDATE usage_logs
-- SET api_key_id = (
--   SELECT ak.id 
--   FROM api_keys ak 
--   WHERE ak.key = 'test_license_123' 
--   LIMIT 1
-- )
-- WHERE api_key_id NOT IN (SELECT id FROM api_keys);

-- Step 5: Verify the fix
SELECT 
  'After Check' as status,
  COUNT(*) as total_logs,
  COUNT(DISTINCT api_key_id) as unique_api_keys,
  COUNT(DISTINCT CASE WHEN action IN ('ai_page_generation_success', 'bulk_item_generation_success') THEN api_key_id END) as api_keys_with_pages
FROM usage_logs;

-- Step 6: Show recent usage logs to verify they're being created correctly
SELECT 
  created_at,
  api_key_id,
  action,
  details->>'service' as service,
  details->>'city' as city
FROM usage_logs
WHERE action IN ('ai_page_generation_success', 'bulk_item_generation_success')
ORDER BY created_at DESC
LIMIT 10;
