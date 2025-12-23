# Wizard Bulk Generation Fix - Deployment Guide

## Overview
This fix makes the wizard's bulk generation work **exactly** like individual page generation by storing and passing all necessary metadata through the bulk job system.

## Problem Summary
The bulk job system was missing critical metadata fields (page_mode, hub_key, hub_label, etc.) that the wizard needs to create pages correctly. The worker was generating content but the wizard couldn't properly import it because it lacked the context to apply quality improvements, set correct metadata, and establish page relationships.

## Solution Summary
1. **Database**: Added 11 new columns to `bulk_job_items` table
2. **Backend Models**: Updated `BulkJobResultItem` to include all metadata fields
3. **Backend API**: Modified `/bulk-jobs` POST and `/bulk-jobs/{id}/results` GET to store/return metadata
4. **Worker**: Updated to pass all metadata to `PageData` for proper AI generation
5. **Plugin**: No changes needed - v0.4.0 already expects these fields

---

## Deployment Steps

### Step 1: Run Database Migration

Execute the SQL migration in your Supabase SQL editor:

**File**: `/Users/joeparker/AppDev/SEOgen/seogen/migrations/add_bulk_job_items_columns.sql`

This adds the following columns to `bulk_job_items`:
- `page_mode` - Page type (service_city, service_hub, city_hub)
- `hub_key` - Hub identifier (residential, commercial, etc.)
- `hub_label` - Display label for hub
- `hub_slug` - URL slug for hub
- `city_slug` - URL slug for city
- `vertical` - Business vertical (electrician, plumber, etc.)
- `business_name` - Preferred business name field
- `cta_text` - Call-to-action text
- `service_area_label` - Service area display label
- `email` - Email address (was missing)

Also relaxes NOT NULL constraints on service/city/state fields (needed for hub pages).

**Verification**: After running, check that columns exist:
```sql
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'bulk_job_items' 
ORDER BY ordinal_position;
```

### Step 2: Deploy Backend to Railway

The following files have been updated:

**Modified Files**:
1. `app/models.py` - Added fields to `BulkJobResultItem`
2. `app/main.py` - Updated bulk job creation and results endpoints
3. `app/supabase_client.py` - Updated queries to fetch new fields
4. `worker.py` - Updated to pass all metadata to `PageData`

**Deploy Command**:
```bash
# Commit changes
cd /Users/joeparker/AppDev/SEOgen/seogen
git add .
git commit -m "Fix: Add metadata fields to bulk jobs for wizard generation"
git push origin main

# Railway will auto-deploy
# Monitor deployment at: https://railway.app
```

**Verification**: After deployment, test the API:
```bash
# Test that new fields are returned
curl -X GET "https://seogen-production.up.railway.app/bulk-jobs/{job_id}/results?license_key={key}" | jq '.items[0]'

# Should see: page_mode, hub_key, hub_label, city_slug, vertical, etc.
```

### Step 3: Test Wizard Generation

**No plugin changes needed** - the WordPress plugin v0.4.0 already expects these fields.

**Test Procedure**:

1. **Service Hub Pages** (should generate first):
   - Go to WP Admin → Hyper Local → Setup Wizard
   - Complete steps 1-4 (Settings, Business, Services, Cities)
   - Click "Generate All Pages"
   - Verify service hub pages are created with:
     - Correct hub metadata (`_seogen_hub_key`, `_seogen_hub_slug`)
     - Quality improvements applied
     - Proper SEO focus keywords

2. **Service City Pages** (should generate second):
   - Verify service+city pages are created with:
     - Correct service and city metadata
     - Parent hub relationships (if applicable)
     - Proper slugs and SEO

3. **City Hub Pages** (should generate third):
   - Verify city hub pages are created with:
     - Correct city metadata
     - Hub key and city slug
     - Links to service pages in that city

**Expected Results**:
- Pages generated in correct order: Service Hubs → Service Pages → City Hubs
- All pages have complete metadata
- Quality improvements applied (same as individual generation)
- Correct parent-child relationships
- Proper SEO optimization

---

## Technical Details

### Database Schema Changes

```sql
-- New columns added to bulk_job_items
page_mode text DEFAULT 'service_city'
hub_key text DEFAULT ''
hub_label text DEFAULT ''
hub_slug text DEFAULT ''
city_slug text DEFAULT ''
vertical text DEFAULT ''
business_name text DEFAULT ''
cta_text text DEFAULT 'Request a Free Estimate'
service_area_label text DEFAULT ''
email text DEFAULT ''

-- Indexes added
CREATE INDEX bulk_job_items_page_mode_idx ON bulk_job_items (page_mode);
CREATE INDEX bulk_job_items_hub_key_idx ON bulk_job_items (hub_key);

-- Constraints relaxed (allow empty strings for hub pages)
ALTER COLUMN service DROP NOT NULL
ALTER COLUMN city DROP NOT NULL
ALTER COLUMN state DROP NOT NULL
```

### API Changes

**POST /bulk-jobs** - Now stores:
```json
{
  "job_id": "uuid",
  "idx": 0,
  "service": "Electrical Panel Upgrade",
  "city": "Tulsa",
  "state": "OK",
  "page_mode": "service_city",
  "hub_key": "residential",
  "hub_label": "Residential",
  "hub_slug": "residential-services",
  "city_slug": "tulsa-ok",
  "vertical": "electrician",
  "business_name": "ABC Electric",
  "cta_text": "Request a Free Estimate",
  "service_area_label": "Tulsa Metro"
}
```

**GET /bulk-jobs/{id}/results** - Now returns:
```json
{
  "items": [{
    "item_id": "uuid",
    "idx": 0,
    "canonical_key": "electrical-panel-upgrade|tulsa|ok",
    "status": "completed",
    "result_json": { /* generated content */ },
    "service": "Electrical Panel Upgrade",
    "city": "Tulsa",
    "state": "OK",
    "page_mode": "service_city",
    "hub_key": "residential",
    "hub_label": "Residential",
    "hub_slug": "residential-services",
    "city_slug": "tulsa-ok",
    "vertical": "electrician",
    "business_name": "ABC Electric",
    "cta_text": "Request a Free Estimate",
    "service_area_label": "Tulsa Metro"
  }]
}
```

### Worker Changes

The worker now passes complete `PageData` to the AI generator:

```python
data = PageData(
    page_mode=page_mode,              # Routes to correct generator
    service=service,
    city=city,
    state=state,
    hub_key=hub_key,                  # For service_hub pages
    hub_label=hub_label,
    hub_slug=hub_slug,
    city_slug=city_slug,              # For city_hub pages
    vertical=vertical,                # Business type
    business_name=business_name,      # Preferred over company_name
    cta_text=cta_text,
    service_area_label=service_area_label,
    # ... other fields
)
```

This ensures the AI generator receives the same data for bulk jobs as it does for individual generation.

---

## Rollback Plan

If issues occur, rollback is straightforward:

1. **Revert Backend Code**:
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Database**: No need to remove columns (they have defaults and won't break anything)

3. **Plugin**: No changes made, so nothing to rollback

---

## Testing Checklist

- [ ] Database migration executed successfully
- [ ] Backend deployed to Railway
- [ ] API returns new fields in `/bulk-jobs/{id}/results`
- [ ] Worker logs show page_mode and hub_key values
- [ ] Service hub pages generate correctly
- [ ] Service city pages generate correctly
- [ ] City hub pages generate correctly
- [ ] Pages have correct metadata
- [ ] Quality improvements applied
- [ ] Parent-child relationships correct
- [ ] SEO optimization working

---

## Support

If you encounter issues:

1. **Check Railway Logs**: Look for worker errors or missing fields
2. **Check Database**: Verify columns exist and have data
3. **Check API Response**: Ensure new fields are returned
4. **Check Plugin Logs**: Look for import errors in WP debug.log

---

## Summary

This fix ensures that wizard bulk generation produces **identical results** to individual page generation by:

1. Storing all metadata in the database
2. Passing all metadata through the API
3. Providing all metadata to the AI generator
4. Allowing the wizard to apply the same quality improvements

The wizard will now create pages in the correct order (Service Hubs → Service Pages → City Hubs) with all the same features as individual generation.
