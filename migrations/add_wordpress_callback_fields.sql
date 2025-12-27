-- Add WordPress callback fields to api_keys table for backend-push auto-import
-- These fields enable secure backend-to-WordPress callbacks

-- Add wordpress_rest_url to store the full REST API base URL
-- Example: https://example.com/wp-json/seogen/v1/
ALTER TABLE api_keys 
ADD COLUMN IF NOT EXISTS wordpress_rest_url TEXT;

-- Add callback_secret for HMAC signature verification
-- This is the shared secret used to sign requests
ALTER TABLE api_keys 
ADD COLUMN IF NOT EXISTS callback_secret TEXT;

-- Add last_callback_at to track when we last successfully pushed to WordPress
ALTER TABLE api_keys 
ADD COLUMN IF NOT EXISTS last_callback_at TIMESTAMPTZ;

-- Add last_callback_error to store the most recent error (for debugging)
ALTER TABLE api_keys 
ADD COLUMN IF NOT EXISTS last_callback_error TEXT;

-- Create index for faster lookups by wordpress_rest_url
CREATE INDEX IF NOT EXISTS api_keys_wordpress_rest_url_idx ON api_keys(wordpress_rest_url);

-- Verify the changes
SELECT 
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'api_keys'
  AND column_name IN ('wordpress_rest_url', 'callback_secret', 'last_callback_at', 'last_callback_error')
ORDER BY column_name;
