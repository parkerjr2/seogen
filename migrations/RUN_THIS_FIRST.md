# CRITICAL: Run This Migration First

## The auto-import feature requires database columns that don't exist yet.

### Step 1: Run the migration

1. Go to Supabase Dashboard → SQL Editor
2. Open a new query
3. Copy and paste the contents of `add_wordpress_callback_fields.sql`
4. Click "Run"

### Step 2: Verify the migration

Run this query to confirm columns were added:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'api_keys' 
  AND column_name IN ('wordpress_rest_url', 'callback_secret', 'last_callback_at', 'last_callback_error')
ORDER BY column_name;
```

You should see 4 rows returned.

### Step 3: Trigger credential sync from WordPress

1. Go to WordPress → SEOgen Settings page
2. The page load will automatically send credentials to backend
3. Click "Test Connection" to verify it worked

### Step 4: Check if credentials are stored

Run this in Supabase SQL Editor:

```sql
SELECT 
  key,
  wordpress_rest_url,
  callback_secret IS NOT NULL as has_secret,
  last_callback_at
FROM api_keys
WHERE key LIKE 'N1aemyUq%'
LIMIT 1;
```

You should see:
- `wordpress_rest_url`: Your WordPress REST API URL
- `has_secret`: `true`

### Step 5: Test with a new bulk job

1. Start a small bulk job (5-10 pages)
2. Close the browser tab
3. Wait 2-3 minutes
4. Return to WordPress → Service Pages
5. Pages should be there automatically

---

## Why This Happened

The code was deployed before the database migration was run. The worker code is trying to query columns that don't exist yet, so it logs "WordPress callback not configured" and skips the push.

## Current Behavior (Without Migration)

- Pages generate successfully ✓
- Pages are stored in database ✓
- Worker tries to push to WordPress ✗ (columns don't exist)
- Worker logs: "WordPress callback not configured"
- Pages only import when you visit the bulk generate page (polling)

## After Migration

- Pages generate successfully ✓
- Pages are stored in database ✓
- Worker pushes to WordPress ✓ (credentials available)
- Pages import automatically within ~30 seconds ✓
- You can close browser tab immediately ✓
