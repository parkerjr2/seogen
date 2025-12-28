-- Diagnostic queries to check auto-import setup

-- 1. Check if callback columns exist in api_keys table
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'api_keys' 
  AND column_name IN ('wordpress_rest_url', 'callback_secret', 'last_callback_at', 'last_callback_error')
ORDER BY column_name;

-- 2. Check if your license key has callback credentials stored
SELECT 
  key,
  wordpress_rest_url,
  callback_secret IS NOT NULL as has_secret,
  LENGTH(callback_secret) as secret_length,
  last_callback_at,
  last_callback_error
FROM api_keys
WHERE key LIKE 'N1aemyUq%'  -- Your license key prefix
ORDER BY created_at DESC
LIMIT 5;

-- 3. Check recent bulk job items to see if they were generated
SELECT 
  id,
  job_id,
  status,
  canonical_key,
  created_at,
  updated_at,
  result_json IS NOT NULL as has_result
FROM bulk_job_items
WHERE job_id IN (
  SELECT id FROM bulk_jobs 
  WHERE api_key_id IN (
    SELECT id FROM api_keys WHERE key LIKE 'N1aemyUq%'
  )
  ORDER BY created_at DESC
  LIMIT 1
)
ORDER BY idx
LIMIT 10;

-- 4. Check if there are any callback errors
SELECT 
  ak.key,
  ak.last_callback_error,
  ak.last_callback_at,
  ak.wordpress_rest_url
FROM api_keys ak
WHERE ak.key LIKE 'N1aemyUq%'
  AND ak.last_callback_error IS NOT NULL;
