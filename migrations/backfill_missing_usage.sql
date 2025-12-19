-- Backfill usage logs for items that were imported but marked as failed
-- This fixes the "home remodeling" page that was generated but not counted

-- Insert usage log for the home remodeling page
INSERT INTO usage_logs (api_key_id, action, details, created_at)
VALUES (
  '823e0480-feb6-4cf0-92ef-d24ae718fb56', -- Your real API key ID
  'bulk_item_generation_success',
  jsonb_build_object(
    'job_id', 'f0db908f-c1bc-4b6e-9cd4-50d448f1b65a',
    'item_id', '8a57ad1c-8bb9-4935-9be0-31c1bb24673a',
    'service', 'home remodeling',
    'city', 'tulsa',
    'state', 'ok',
    'backfilled', true,
    'reason', 'Item had valid result_json but was marked failed due to retry error'
  ),
  '2025-12-19 03:24:23.662481+00'::timestamptz -- Use the bulk job created_at time
);

-- Verify the insert
SELECT 
  created_at,
  api_key_id,
  action,
  details->>'service' as service,
  details->>'city' as city,
  details->>'backfilled' as backfilled
FROM usage_logs
WHERE api_key_id = '823e0480-feb6-4cf0-92ef-d24ae718fb56'
ORDER BY created_at DESC;
