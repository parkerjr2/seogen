-- Sites table for tracking WordPress installations
-- Stores site registration data and webhook secrets for license management

CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_url TEXT NOT NULL UNIQUE,
    license_key TEXT NOT NULL,
    secret_key TEXT NOT NULL,
    plugin_version TEXT,
    wordpress_version TEXT,
    status TEXT DEFAULT 'active',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_webhook_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast license key lookups
CREATE INDEX IF NOT EXISTS idx_sites_license_key ON sites(license_key);

-- Index for fast site URL lookups
CREATE INDEX IF NOT EXISTS idx_sites_site_url ON sites(site_url);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_sites_status ON sites(status);

-- Comments
COMMENT ON TABLE sites IS 'WordPress site registrations for license management';
COMMENT ON COLUMN sites.site_url IS 'Full URL of the WordPress site';
COMMENT ON COLUMN sites.license_key IS 'License key used by this site';
COMMENT ON COLUMN sites.secret_key IS 'Webhook secret for secure communication';
COMMENT ON COLUMN sites.plugin_version IS 'SEOgen plugin version installed';
COMMENT ON COLUMN sites.wordpress_version IS 'WordPress version running on site';
COMMENT ON COLUMN sites.status IS 'Site status: active, inactive, suspended';
COMMENT ON COLUMN sites.registered_at IS 'When the site first registered';
COMMENT ON COLUMN sites.last_webhook_at IS 'Last time we sent a webhook to this site';
