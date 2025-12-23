-- Migration: Add missing columns to bulk_job_items table
-- These columns are needed for wizard to create pages exactly like individual generation

-- Add page_mode column (service_hub, city_hub, or service_city)
ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS page_mode text DEFAULT 'service_city';

-- Add hub-related columns for service_hub pages
ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS hub_key text DEFAULT '';

ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS hub_label text DEFAULT '';

ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS hub_slug text DEFAULT '';

-- Add city_slug for city_hub pages
ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS city_slug text DEFAULT '';

-- Add vertical (business type: electrician, plumber, etc.)
ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS vertical text DEFAULT '';

-- Add business_name (preferred over company_name)
ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS business_name text DEFAULT '';

-- Add CTA text
ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS cta_text text DEFAULT 'Request a Free Estimate';

-- Add service area label
ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS service_area_label text DEFAULT '';

-- Add email column (was missing from original schema)
ALTER TABLE bulk_job_items 
ADD COLUMN IF NOT EXISTS email text DEFAULT '';

-- Create index on page_mode for efficient filtering
CREATE INDEX IF NOT EXISTS bulk_job_items_page_mode_idx ON bulk_job_items (page_mode);

-- Create index on hub_key for efficient hub page lookups
CREATE INDEX IF NOT EXISTS bulk_job_items_hub_key_idx ON bulk_job_items (hub_key);

-- Update existing NOT NULL columns to allow empty strings for hub pages
-- (service, city, state can be empty for hub pages)
ALTER TABLE bulk_job_items 
ALTER COLUMN service DROP NOT NULL;

ALTER TABLE bulk_job_items 
ALTER COLUMN city DROP NOT NULL;

ALTER TABLE bulk_job_items 
ALTER COLUMN state DROP NOT NULL;

ALTER TABLE bulk_job_items 
ALTER COLUMN company_name DROP NOT NULL;

ALTER TABLE bulk_job_items 
ALTER COLUMN phone DROP NOT NULL;

ALTER TABLE bulk_job_items 
ALTER COLUMN address DROP NOT NULL;
