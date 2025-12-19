-- Migration Script: Migrate licenses to users, subscriptions, and api_keys
-- Run this in Supabase SQL Editor

-- Step 1: Create a default user for existing licenses
-- This user will own all legacy API keys
INSERT INTO users (id, email, name, password_hash)
VALUES (
  '00000000-0000-0000-0000-000000000001'::uuid,
  'legacy@hyperlocal.com',
  'Legacy User',
  'LEGACY_NO_PASSWORD_SET' -- User will need to set password via password reset
)
ON CONFLICT (id) DO NOTHING;

-- Step 2: Create ONE subscription for the legacy user
-- Use the highest limits from existing licenses
-- All existing API keys will share this subscription
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
SELECT 
  '00000000-0000-0000-0000-000000000002'::uuid as id,
  '00000000-0000-0000-0000-000000000001'::uuid as user_id,
  'legacy' as plan_name,
  MAX(COALESCE(page_limit, 500)) as page_limit,
  MAX(COALESCE(monthly_generation_limit, 500)) as monthly_generation_limit,
  'active' as status,
  MIN(COALESCE(current_period_start, NOW())) as current_period_start,
  MIN(COALESCE(created_at, NOW())) as created_at,
  NOW() as updated_at
FROM licenses
ON CONFLICT (id) DO NOTHING;

-- Step 3: Migrate all licenses to api_keys
-- All API keys will share the same subscription
-- Keep the same ID and license_key for backward compatibility
INSERT INTO api_keys (
  id,
  user_id,
  subscription_id,
  key,
  name,
  status,
  created_at
)
SELECT 
  l.id,
  '00000000-0000-0000-0000-000000000001'::uuid as user_id,
  '00000000-0000-0000-0000-000000000002'::uuid as subscription_id,
  l.license_key as key,
  COALESCE('Legacy: ' || l.license_key, 'Legacy API Key') as name,
  COALESCE(l.status, 'active') as status,
  COALESCE(l.created_at, NOW()) as created_at
FROM licenses l;

-- Step 4: Update usage_logs to reference api_keys
-- Rename the column if you want (optional, but recommended for clarity)
-- If you skip this, just make sure your code references the correct column name

-- Option A: Rename column (recommended)
ALTER TABLE usage_logs RENAME COLUMN license_id TO api_key_id;

-- Option B: Keep column name as license_id (no changes needed)
-- Just update your code to understand license_id now points to api_keys table

-- Step 5: Verify migration
-- Check that all licenses were migrated
SELECT 
  'Licenses' as table_name,
  COUNT(*) as count
FROM licenses
UNION ALL
SELECT 
  'Users' as table_name,
  COUNT(*) as count
FROM users
UNION ALL
SELECT 
  'Subscriptions' as table_name,
  COUNT(*) as count
FROM subscriptions
UNION ALL
SELECT 
  'API Keys' as table_name,
  COUNT(*) as count
FROM api_keys;

-- Step 6: Verify usage_logs still work
SELECT 
  COUNT(*) as total_usage_logs,
  COUNT(DISTINCT api_key_id) as unique_api_keys
FROM usage_logs;

-- Step 7: After verification, you can drop the old licenses table
-- IMPORTANT: Only run this after confirming everything works!
-- DROP TABLE licenses;
