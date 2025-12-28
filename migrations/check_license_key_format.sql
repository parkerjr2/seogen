-- Check the exact license key format stored in backend
SELECT 
  key as license_key,
  LENGTH(key) as key_length,
  key = UPPER(key) as is_uppercase,
  key = LOWER(key) as is_lowercase,
  wordpress_rest_url,
  callback_secret IS NOT NULL as has_secret
FROM api_keys
WHERE key LIKE 'N1aemyUq%'
LIMIT 1;

-- Check recent bulk jobs to see what license key is being used
SELECT 
  bj.id as job_id,
  bj.license_key,
  LENGTH(bj.license_key) as key_length,
  bj.created_at,
  bj.status
FROM bulk_jobs bj
WHERE bj.license_key LIKE 'N1aemyUq%'
ORDER BY bj.created_at DESC
LIMIT 5;
