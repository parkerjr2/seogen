-- Add M Electric production license to new schema (users, subscriptions, api_keys)
-- License: N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc

-- Step 1: Create user for M Electric (if not exists)
INSERT INTO users (id, email, name, password_hash)
VALUES (
  'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid,
  'admin@melectricllc.com',
  'M Electric',
  'LEGACY_NO_PASSWORD_SET'
)
ON CONFLICT (id) DO NOTHING;

-- Step 2: Create subscription with 1000 page limit
INSERT INTO subscriptions (
  id,
  user_id,
  plan_name,
  page_limit,
  monthly_generation_limit,
  status,
  current_period_start,
  created_at,
  updated_at
)
VALUES (
  'b2c3d4e5-f6a7-8901-bcde-f12345678901'::uuid,
  'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid,
  'professional',
  1000,  -- Total page limit
  1000,  -- Monthly generation limit
  'active',
  NOW(),
  NOW(),
  NOW()
)
ON CONFLICT (id) DO UPDATE
SET 
  page_limit = EXCLUDED.page_limit,
  monthly_generation_limit = EXCLUDED.monthly_generation_limit,
  status = EXCLUDED.status,
  updated_at = NOW();

-- Step 3: Create API key with the production license key
INSERT INTO api_keys (
  id,
  user_id,
  subscription_id,
  key,
  name,
  status,
  created_at
)
VALUES (
  'c3d4e5f6-a7b8-9012-cdef-123456789012'::uuid,
  'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid,
  'b2c3d4e5-f6a7-8901-bcde-f12345678901'::uuid,
  'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc',
  'M Electric Production',
  'active',
  NOW()
)
ON CONFLICT (key) DO UPDATE
SET
  subscription_id = EXCLUDED.subscription_id,
  status = EXCLUDED.status;

-- Step 4: Also add to legacy licenses table for backward compatibility
INSERT INTO licenses (license_key, status, credits_remaining)
VALUES (
    'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc',
    'active',
    1000
)
ON CONFLICT (license_key) DO UPDATE
SET 
    status = EXCLUDED.status,
    credits_remaining = EXCLUDED.credits_remaining;

-- Step 5: Verify the setup
SELECT 
  'User' as type,
  u.id::text as id,
  u.email,
  u.name
FROM users u
WHERE u.id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid

UNION ALL

SELECT 
  'Subscription' as type,
  s.id::text,
  s.plan_name,
  CONCAT(s.page_limit, ' pages, ', s.monthly_generation_limit, ' monthly') as name
FROM subscriptions s
WHERE s.id = 'b2c3d4e5-f6a7-8901-bcde-f12345678901'::uuid

UNION ALL

SELECT 
  'API Key' as type,
  a.id::text,
  a.name,
  a.key
FROM api_keys a
WHERE a.key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';

-- Step 6: Check current usage
SELECT 
  COUNT(*) as total_pages_generated,
  COUNT(CASE WHEN created_at >= (SELECT current_period_start FROM subscriptions WHERE id = 'b2c3d4e5-f6a7-8901-bcde-f12345678901'::uuid) THEN 1 END) as pages_this_period
FROM usage_logs
WHERE api_key_id = 'c3d4e5f6-a7b8-9012-cdef-123456789012'::uuid
  AND action IN ('ai_page_generation_success', 'bulk_item_generation_success');
