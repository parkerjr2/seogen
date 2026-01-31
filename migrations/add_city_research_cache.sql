-- City Research Cache Table
-- Stores comprehensive city research data for content generation
-- Cache expires after 90 days to ensure data freshness

CREATE TABLE IF NOT EXISTS city_research_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_name TEXT NOT NULL,
    state TEXT NOT NULL CHECK (LENGTH(state) = 2),
    trade_type TEXT NOT NULL,
    research_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '90 days')
);

-- Unique index to prevent duplicate research for same city+state+trade
CREATE UNIQUE INDEX IF NOT EXISTS idx_city_research_unique
ON city_research_cache(city_name, state, trade_type);

-- Index for expiration cleanup queries
CREATE INDEX IF NOT EXISTS idx_city_research_expires
ON city_research_cache(expires_at);

-- Index for city lookups
CREATE INDEX IF NOT EXISTS idx_city_research_lookup
ON city_research_cache(city_name, state);

-- Index for trade type filtering
CREATE INDEX IF NOT EXISTS idx_city_research_trade
ON city_research_cache(trade_type);

-- Auto-update updated_at timestamp trigger
CREATE OR REPLACE FUNCTION update_city_research_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER city_research_updated_at_trigger
    BEFORE UPDATE ON city_research_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_city_research_updated_at();

-- Comments
COMMENT ON TABLE city_research_cache IS 'Cached comprehensive city research data for content generation';
COMMENT ON COLUMN city_research_cache.city_name IS 'City name (e.g., "Tulsa")';
COMMENT ON COLUMN city_research_cache.state IS 'Two-letter state code (e.g., "OK")';
COMMENT ON COLUMN city_research_cache.trade_type IS 'Trade/vertical type (e.g., "Garage Door", "Electrician")';
COMMENT ON COLUMN city_research_cache.research_data IS 'Full research JSON with building age, climate, permits, etc.';
COMMENT ON COLUMN city_research_cache.expires_at IS 'Cache expiration timestamp (90 days from creation)';
