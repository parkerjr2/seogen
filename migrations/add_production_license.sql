-- Add production license key for M Electric
-- License: N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc

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

-- Verify the license was added
SELECT id, license_key, status, credits_remaining, created_at
FROM licenses
WHERE license_key = 'N1aemyUq7GQka2VWA5qX2WF78J7mNKVvw50t_GW3BOc';
