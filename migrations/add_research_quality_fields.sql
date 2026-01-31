-- Add Quality Tracking Fields to City Research Cache
-- PART 4 of city research quality improvement
-- Tracks data quality, generic detection, and manual review needs

-- Add quality tracking columns
ALTER TABLE city_research_cache
ADD COLUMN IF NOT EXISTS is_generic BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS differentiation_score INTEGER CHECK (differentiation_score >= 0 AND differentiation_score <= 10),
ADD COLUMN IF NOT EXISTS needs_manual_review BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP WITH TIME ZONE;

-- Index for finding generic data that needs review
CREATE INDEX IF NOT EXISTS idx_city_research_quality
ON city_research_cache(is_generic, needs_manual_review)
WHERE is_generic = true OR needs_manual_review = true;

-- Index for differentiation score filtering
CREATE INDEX IF NOT EXISTS idx_city_research_score
ON city_research_cache(differentiation_score);

-- Comments
COMMENT ON COLUMN city_research_cache.is_generic IS 'True if research data is flagged as generic/regional (not city-specific)';
COMMENT ON COLUMN city_research_cache.differentiation_score IS 'Score 1-10 rating how unique this city data is (8+ = good, <6 = too generic)';
COMMENT ON COLUMN city_research_cache.needs_manual_review IS 'True if research failed validation and needs human review';
COMMENT ON COLUMN city_research_cache.validated_at IS 'Timestamp of last validation check';
