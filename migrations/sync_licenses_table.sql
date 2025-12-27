-- The WordPress plugin is showing 1,000 pages because the old licenses table
-- still has credits_remaining = 1000
-- This is a quick fix to update the legacy table to match actual usage

-- Update the legacy licenses table to reflect actual usage
UPDATE licenses
SET 
  credits_remaining = (
    SELECT 5000 - COUNT(*)
    FROM usage_logs ul
    JOIN api_keys a ON a.id = ul.api_key_id
    WHERE a.key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc'
    AND ul.action IN ('ai_page_generation_success', 'bulk_item_generation_success')
  )
WHERE license_key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';

-- Verify the update
SELECT 
  'Legacy licenses table' as source,
  license_key,
  status,
  credits_remaining,
  5000 - credits_remaining as pages_used
FROM licenses
WHERE license_key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';

-- Show what WordPress should display after this fix
SELECT 
  'Expected WordPress Display' as status,
  5000 - l.credits_remaining as total_pages_shown,
  5000 as page_limit,
  l.credits_remaining as pages_remaining
FROM licenses l
WHERE l.license_key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';
