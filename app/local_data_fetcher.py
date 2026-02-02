"""
Local Data Fetcher - Retrieves real facts about cities for AI content generation.
Uses US Census API for housing age data and GPT-4o-mini for plausible landmarks.
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import hashlib
import json
from app.config import settings
from app.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class LocalDataFetcher:
    """Fetches verified local data about cities to enhance AI-generated content."""
    
    def __init__(self):
        self.timeout = 10.0
        self.current_year = datetime.now().year
        self._cache: Dict[str, Any] = {}  # In-memory cache for landmarks
        self.openai_api_key = settings.openai_api_key
        self.supabase_client = SupabaseClient()  # For city research caching
        
    async def fetch_city_data(self, city: str, state: str) -> Dict[str, Any]:
        """
        Fetch housing age data and landmarks for a city.
        Returns dict with housing facts and landmarks.
        """
        city_data = {
            "city": city,
            "state": state,
            "housing_facts": [],
            "landmarks": [],
        }
        
        # Fetch both Census and AI-generated landmarks in parallel
        results = await asyncio.gather(
            self._fetch_census_housing_age(city, state),
            self._fetch_ai_landmarks(city, state),
            return_exceptions=True
        )
        
        # Process Census data
        housing_data = results[0] if not isinstance(results[0], Exception) else []
        if housing_data:
            city_data["housing_facts"] = housing_data
        
        # Process AI-generated landmarks
        landmarks = results[1] if not isinstance(results[1], Exception) else []
        if landmarks:
            city_data["landmarks"] = landmarks
        
        return city_data
    
    async def _fetch_census_housing_age(self, city: str, state: str) -> List[str]:
        """Fetch housing age data from US Census API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use Census ACS 5-Year Data for housing characteristics
                # This is more reliable than trying to get city-specific data
                # We'll use state-level data as a proxy
                
                state_fips = self._get_state_fips(state)
                if not state_fips:
                    return []
                
                # Census API endpoint for housing units by year built
                # Using ACS 5-Year estimates (most recent and stable)
                api_url = "https://api.census.gov/data/2022/acs/acs5"
                
                # B25034: Year Structure Built
                # We'll get median year and calculate average age
                params = {
                    "get": "B25035_001E",  # Median year structure built
                    "for": f"state:{state_fips}",
                }
                
                response = await client.get(api_url, params=params)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                
                if len(data) < 2:  # Need header + data row
                    return []
                
                # Parse median year built
                try:
                    median_year = float(data[1][0])
                    if median_year > 1800 and median_year < self.current_year:
                        avg_age = self.current_year - int(median_year)
                        return [
                            f"Many homes in the area were built around {int(median_year)}, making them approximately {avg_age} years old"
                        ]
                except (ValueError, IndexError):
                    pass
                
                return []
                
        except Exception as e:
            logger.warning(f"Census API fetch failed for {city}, {state}: {e}")
            return []
    
    def _get_state_fips(self, state: str) -> Optional[str]:
        """Convert state abbreviation or name to FIPS code."""
        state_fips_map = {
            "AL": "01", "Alabama": "01",
            "AK": "02", "Alaska": "02",
            "AZ": "04", "Arizona": "04",
            "AR": "05", "Arkansas": "05",
            "CA": "06", "California": "06",
            "CO": "08", "Colorado": "08",
            "CT": "09", "Connecticut": "09",
            "DE": "10", "Delaware": "10",
            "FL": "12", "Florida": "12",
            "GA": "13", "Georgia": "13",
            "HI": "15", "Hawaii": "15",
            "ID": "16", "Idaho": "16",
            "IL": "17", "Illinois": "17",
            "IN": "18", "Indiana": "18",
            "IA": "19", "Iowa": "19",
            "KS": "20", "Kansas": "20",
            "KY": "21", "Kentucky": "21",
            "LA": "22", "Louisiana": "22",
            "ME": "23", "Maine": "23",
            "MD": "24", "Maryland": "24",
            "MA": "25", "Massachusetts": "25",
            "MI": "26", "Michigan": "26",
            "MN": "27", "Minnesota": "27",
            "MS": "28", "Mississippi": "28",
            "MO": "29", "Missouri": "29",
            "MT": "30", "Montana": "30",
            "NE": "31", "Nebraska": "31",
            "NV": "32", "Nevada": "32",
            "NH": "33", "New Hampshire": "33",
            "NJ": "34", "New Jersey": "34",
            "NM": "35", "New Mexico": "35",
            "NY": "36", "New York": "36",
            "NC": "37", "North Carolina": "37",
            "ND": "38", "North Dakota": "38",
            "OH": "39", "Ohio": "39",
            "OK": "40", "Oklahoma": "40",
            "OR": "41", "Oregon": "41",
            "PA": "42", "Pennsylvania": "42",
            "RI": "44", "Rhode Island": "44",
            "SC": "45", "South Carolina": "45",
            "SD": "46", "South Dakota": "46",
            "TN": "47", "Tennessee": "47",
            "TX": "48", "Texas": "48",
            "UT": "49", "Utah": "49",
            "VT": "50", "Vermont": "50",
            "VA": "51", "Virginia": "51",
            "WA": "53", "Washington": "53",
            "WV": "54", "West Virginia": "54",
            "WI": "55", "Wisconsin": "55",
            "WY": "56", "Wyoming": "56",
        }
        return state_fips_map.get(state.upper())
    
    async def _fetch_ai_landmarks(self, city: str, state: str) -> List[str]:
        """Use GPT-4o-mini to suggest plausible landmarks for a city."""
        # Check cache first
        cache_key = f"{city.lower()}_{state.lower()}"
        if cache_key in self._cache:
            logger.info(f"Using cached landmarks for {city}, {state}")
            return self._cache[cache_key]
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Ask GPT-4o-mini for plausible landmarks
                prompt = f"""List 2-3 real, well-known landmarks, institutions, or areas in {city}, {state}. 
Examples: universities, colleges, hospitals, major parks, downtown areas, historic districts.
Only include landmarks that actually exist and are well-known.
Return ONLY a JSON array of landmark names, nothing else.
Example format: ["University of Tulsa", "Woodward Park", "Tulsa Arts District"]"""

                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that provides accurate information about US cities. Only suggest landmarks that actually exist."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 100
                }
                
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.warning(f"OpenAI API returned {response.status_code} for {city}, {state}")
                    return []
                
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                
                # Parse JSON response
                try:
                    landmarks = json.loads(content)
                    if isinstance(landmarks, list):
                        # Filter and clean
                        landmarks = [str(l).strip() for l in landmarks if l and len(str(l)) < 60][:3]
                        
                        # Cache the results
                        self._cache[cache_key] = landmarks
                        
                        logger.info(f"AI suggested {len(landmarks)} landmarks for {city}, {state}: {landmarks}")
                        return landmarks
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI response as JSON: {content}")
                    return []
                
                return []
                
        except Exception as e:
            logger.warning(f"AI landmark fetch failed for {city}, {state}: {e}")
            return []

    async def fetch_city_research_data(
        self,
        city_name: str,
        state: str,
        trade_type: str
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive city research data using OpenAI GPT-4o with web search.
        Uses Supabase caching with quality-based TTL:
        - High-quality (score >= 8): 90 days
        - Generic/low-quality (score < 6): 7 days
        - Medium quality: 30 days

        PART 5: Validation and quality-based caching

        Args:
            city_name: City name (e.g., "Tulsa")
            state: Two-letter state code (e.g., "OK")
            trade_type: Trade type (e.g., "Garage Door", "Electrician")

        Returns:
            Dict with research data or empty dict on failure
        """
        # Check cache first
        cached_data = self.supabase_client.get_city_research_cache(
            city_name,
            state,
            trade_type
        )

        if cached_data:
            logger.info(f"Using cached research for {city_name}, {state} ({trade_type})")
            return cached_data

        # Cache miss - perform research
        logger.info(f"Performing new research for {city_name}, {state} ({trade_type})")

        research_data = await self._perform_city_research(city_name, state, trade_type)

        # PART 5: Validate research quality before caching
        if research_data and research_data.get("researched_at"):
            try:
                # Run validation
                validation_result = self.validate_research_uniqueness(
                    research_data,
                    city_name,
                    state
                )

                # Extract quality metrics
                is_generic = validation_result.get("is_generic", False)
                differentiation_score = research_data.get("differentiation_score", 0)
                specificity_score = validation_result.get("specificity_score", 0)

                # Determine if manual review needed
                needs_manual_review = (
                    is_generic or
                    differentiation_score < 6 or
                    specificity_score < 5 or
                    research_data.get("fallback", False)
                )

                # Add validation results to research data (for debugging/logging)
                research_data["validation"] = validation_result

                # Cache with quality-based TTL
                self.supabase_client.set_city_research_cache(
                    city_name,
                    state,
                    trade_type,
                    research_data,
                    is_generic=is_generic,
                    differentiation_score=differentiation_score,
                    needs_manual_review=needs_manual_review,
                    validated_at=validation_result.get("validated_at")
                )

                # Log quality warning if needed
                if needs_manual_review:
                    logger.warning(
                        f"Research for {city_name}, {state} ({trade_type}) needs manual review. "
                        f"Generic: {is_generic}, Diff score: {differentiation_score}, "
                        f"Specificity: {specificity_score}"
                    )

            except Exception as e:
                logger.warning(f"Failed to validate/cache research data: {e}")

        return research_data

    async def _perform_city_research(
        self,
        city_name: str,
        state: str,
        trade_type: str
    ) -> Dict[str, Any]:
        """
        Perform actual city research using OpenAI GPT-4o with web search.

        This uses OpenAI's GPT-4o model (NOT mini) with function calling/web search
        to gather comprehensive, accurate city data.

        CRITICAL: This prompt is designed to find UNIQUE, CITY-SPECIFIC data.
        Generic regional data (applicable to any city in the state) is rejected.
        """
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured - cannot perform research")
            return self._get_fallback_research(city_name, state, trade_type)

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:  # Longer timeout for thorough research

                # Construct aggressive research prompt focused on differentiation
                # Handle "General" trade type for city hub pages
                if trade_type == "General":
                    system_prompt = f"""You are researching {city_name}, {state} to find data that makes it DIFFERENT from other cities in the region.

CRITICAL: Generic regional data (applicable to any city in {state}) is USELESS.
Find specific local factors that create service demand patterns across MULTIPLE service industries (roofing, HVAC, electrical, plumbing, garage doors, etc.).

Focus on construction patterns, climate factors, and economic trends that affect MULTIPLE trades, not just one specific service type.

Your research must uncover what makes {city_name} DISTINCT - not what it shares with nearby cities."""
                else:
                    system_prompt = f"""You are researching {city_name}, {state} to find data that makes it DIFFERENT from other cities in the region.

CRITICAL: Generic regional data (applicable to any city in {state}) is USELESS.
Find specific local factors that create unique service patterns for {trade_type} businesses.

Your research must uncover what makes {city_name} DISTINCT - not what it shares with nearby cities."""

                # Adjust search strategy based on trade type
                if trade_type == "General":
                    search_focus = "service businesses across multiple trades"
                    user_prompt = f"""Research {city_name}, {state} for general service business insights across multiple trades (roofing, HVAC, electrical, plumbing, etc.).

SEARCH STRATEGY - Execute these specific searches:
1. "{city_name} {state} building permits commercial construction" - Find permit trends, inspection requirements
2. "{city_name} {state} commercial construction history" - Identify specific building booms unique to this city
3. "{city_name} {state} climate weather patterns" - Find weather anomalies, microclimates, specific storm patterns
4. "{city_name} {state} building codes regulations" - Local codes, requirements
5. "{city_name} {state} economic development history" - Industry shifts that affect building stock
6. "{city_name} {state} demographics housing" - Population changes creating service demand
7. "{city_name} neighborhood service demand patterns" - Specific districts/areas with unique needs
8. "{city_name} {state} vs [nearby city] differences" - Direct comparison to highlight uniqueness"""
                else:
                    user_prompt = f"""Research {city_name}, {state} for {trade_type} service businesses.

SEARCH STRATEGY - Execute these specific searches:
1. "{city_name} {state} building permits {trade_type}" - Find permit trends, inspection requirements
2. "{city_name} {state} commercial construction history" - Identify specific building booms unique to this city
3. "{city_name} {state} climate weather patterns" - Find weather anomalies, microclimates, specific storm patterns
4. "{city_name} {state} {trade_type} industry regulations" - Local codes, requirements
5. "{city_name} {state} economic development history" - Industry shifts that affect building stock
6. "{city_name} {state} demographics housing" - Population changes creating service demand
7. "{city_name} neighborhood {trade_type} service demand" - Specific districts/areas with unique needs
8. "{city_name} {state} vs [nearby city] differences" - Direct comparison to highlight uniqueness

DIFFERENTIATION REQUIREMENTS:
- Building age data must be CITY-SPECIFIC (not state/regional averages)
- Construction eras must include SPECIFIC YEARS and LOCAL CONTEXT (e.g., "1978-1982 oil boom" not "1970s")
- Climate factors must be UNIQUE TO THIS CITY (e.g., "tornado alley microclimates" not just "storms")
- Service triggers must reflect LOCAL PATTERNS (e.g., "historic district renovation surge 2015-2020" not "renovations")
- Include NEIGHBORHOOD-LEVEL details where relevant
- Cite data sources with specificity_note explaining why this data is city-specific

REJECT GENERIC DATA:
❌ BAD: "heat, storms, hail" - applicable to entire region
✅ GOOD: "extreme heat waves (110°F+ 20 days/year vs state avg 8 days), urban heat island effect in downtown core, flash flooding in Arts District due to 1920s drainage infrastructure"

❌ BAD: "inspections, renovations, tenant_turnover" - universal triggers
✅ GOOD: "Historic Greenwood District requiring period-authentic repairs since 2018 designation, Blue Dome entertainment district rapid turnover (avg 18mo lease), flood plain inspections post-2019 Arkansas River flooding"

❌ BAD: "1970s, 1990s, 2010s" - generic regional pattern
✅ GOOD: "1978-1982 (oil boom commercial expansion, 40% of downtown office stock), 2004-2008 (suburban retail explosion along BA Expressway), 2015-2020 (urban core reinvestment, warehouse conversions in Kendall-Whittier)"

Return ONLY valid JSON in this exact format:
{{
  "building_age_specificity": {{
    "median_year": "1978" or null,
    "city_specific_note": "Explain why this is specific to {city_name} vs other {state} cities",
    "neighborhoods": {{"Downtown": "1978", "Suburbs": "1995"}} or {{}}
  }},
  "major_construction_eras": [
    {{
      "period": "1978-1982",
      "description": "Oil boom commercial expansion - 40% of downtown office stock",
      "specificity_note": "Unique to Tulsa's energy industry peak"
    }}
  ],
  "climate_factors": {{
    "primary": ["extreme heat waves 110°F+ (20 days/year vs state avg 8)", "urban heat island +5°F downtown", "flash flooding Arts District"],
    "service_impacts": "City-specific explanation of how these UNIQUE factors affect {trade_type}",
    "specificity_note": "Explain what makes {city_name} climate unique vs nearby cities"
  }},
  "service_triggers": [
    {{
      "trigger": "Historic Greenwood District period-authentic repair requirements",
      "context": "2018 historic designation, affects 200+ commercial buildings",
      "specificity_note": "Unique to Tulsa's historic preservation efforts"
    }}
  ],
  "permit_requirements": {{
    "description": "City-specific permit process details",
    "unique_aspects": "What makes {city_name} different from other {state} cities",
    "specificity_note": "Explain local variations from state code"
  }},
  "unique_factors": [
    {{
      "factor": "Specific local characteristic with data",
      "specificity_note": "Why this is unique to {city_name}"
    }}
  ],
  "differentiation_score": 8,
  "self_validation": {{
    "is_city_specific": true,
    "has_generic_data": false,
    "confidence_level": "high",
    "notes": "Brief self-assessment of research quality"
  }},
  "researched_at": "{datetime.utcnow().isoformat()}",
  "city_name": "{city_name}",
  "state": "{state}",
  "trade_type": "{trade_type}"
}}

SELF-VALIDATE before returning:
1. Does data apply ONLY to {city_name} or to entire {state}? (Reject if regional)
2. Are construction eras specific YEARS with LOCAL CONTEXT? (Reject if generic decades)
3. Are climate factors UNIQUE to this city? (Reject if applicable to whole state)
4. Do service triggers reference SPECIFIC local events/patterns? (Reject if universal)
5. Differentiation score: Rate 1-10 how unique this data is (8+ = good, <6 = too generic)

Base your research on your knowledge of {city_name}, {state} geography, climate, and building patterns."""

                # Call OpenAI GPT-4o (not mini) for detailed city research
                # Note: Uses model's training data, not real-time web search
                payload = {
                    "model": "gpt-4o",  # Use GPT-4o, NOT gpt-4o-mini
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.15,  # Very low temperature for factual research
                    "max_tokens": 2000,  # More tokens for detailed responses
                    "response_format": {"type": "json_object"}  # Enforce JSON response
                }

                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code != 200:
                    logger.error(f"OpenAI API returned {response.status_code} for city research: {response.text}")
                    return self._get_fallback_research(city_name, state, trade_type)

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                # Parse JSON response
                try:
                    research_data = json.loads(content)

                    # Validate required fields (updated structure)
                    required_fields = [
                        "building_age_specificity", "major_construction_eras", "climate_factors",
                        "service_triggers", "permit_requirements", "unique_factors",
                        "differentiation_score", "self_validation",
                        "researched_at", "city_name", "state", "trade_type"
                    ]

                    if all(field in research_data for field in required_fields):
                        # Check differentiation score
                        diff_score = research_data.get("differentiation_score", 0)
                        self_val = research_data.get("self_validation", {})

                        logger.info(f"Successfully researched {city_name}, {state} for {trade_type}")
                        logger.info(f"Differentiation score: {diff_score}/10")
                        logger.info(f"Self-validation: {self_val}")

                        # Flag low-quality research but still return it
                        if diff_score < 6:
                            logger.warning(f"Low differentiation score ({diff_score}) - data may be too generic")
                            research_data["quality_warning"] = "low_differentiation_score"

                        if not self_val.get("is_city_specific", False):
                            logger.warning(f"Self-validation flagged data as not city-specific")
                            research_data["quality_warning"] = "not_city_specific"

                        return research_data
                    else:
                        missing = [f for f in required_fields if f not in research_data]
                        logger.warning(f"Research response missing required fields: {missing}")
                        return self._get_fallback_research(city_name, state, trade_type)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse research JSON: {e}")
                    logger.error(f"Response content: {content}")
                    return self._get_fallback_research(city_name, state, trade_type)

        except Exception as e:
            logger.error(f"City research failed for {city_name}, {state}: {e}")
            return self._get_fallback_research(city_name, state, trade_type)

    def _get_fallback_research(
        self,
        city_name: str,
        state: str,
        trade_type: str
    ) -> Dict[str, Any]:
        """
        Return minimal fallback research data when API call fails.
        This ensures generation doesn't break if research fails.
        Marked as low-quality for shorter cache TTL.
        """
        return {
            "building_age_specificity": {
                "median_year": None,
                "city_specific_note": None,
                "neighborhoods": {}
            },
            "major_construction_eras": [],
            "climate_factors": {
                "primary": [],
                "service_impacts": None,
                "specificity_note": None
            },
            "service_triggers": [],
            "permit_requirements": {
                "description": None,
                "unique_aspects": None,
                "specificity_note": None
            },
            "unique_factors": [],
            "differentiation_score": 0,  # Lowest score = fallback
            "self_validation": {
                "is_city_specific": False,
                "has_generic_data": True,
                "confidence_level": "none",
                "notes": "Fallback data - API call failed"
            },
            "researched_at": datetime.utcnow().isoformat(),
            "city_name": city_name,
            "state": state,
            "trade_type": trade_type,
            "fallback": True,  # Flag to indicate this is fallback data
            "quality_warning": "api_failure"
        }

    def validate_research_uniqueness(
        self,
        research_data: Dict[str, Any],
        city_name: str,
        state: str
    ) -> Dict[str, Any]:
        """
        Validate that research data is genuinely city-specific (not generic regional data).

        Flags research as is_generic if it contains too many generic patterns.
        Returns validation results dict.

        PART 2 of the city research quality improvement.
        """
        validation_result = {
            "is_generic": False,
            "generic_flags": [],
            "specificity_score": 10,  # Start at 10, deduct points for issues
            "validated_at": datetime.utcnow().isoformat()
        }

        # GENERIC DATA PATTERNS TO DETECT
        generic_climate_patterns = [
            ["heat", "storms", "hail"],
            ["hot", "humid", "rain"],
            ["cold", "snow", "ice"],
            ["wind", "rain", "storms"]
        ]

        generic_trigger_patterns = [
            ["inspections", "renovations", "tenant_turnover"],
            ["maintenance", "repairs", "upgrades"],
            ["compliance", "safety", "efficiency"]
        ]

        generic_era_patterns = [
            ["1970s", "1990s", "2010s"],
            ["1980s", "2000s"],
            ["post-war", "modern"]
        ]

        # Check climate factors for generic patterns
        climate_primary = research_data.get("climate_factors", {}).get("primary", [])
        if climate_primary:
            # Normalize to just keywords
            climate_keywords = []
            for item in climate_primary:
                # Extract keywords (lowercase, first word)
                keywords = item.lower().split()
                if keywords:
                    climate_keywords.append(keywords[0])

            # Check against generic patterns
            for pattern in generic_climate_patterns:
                if set(climate_keywords) == set(pattern):
                    validation_result["generic_flags"].append("climate_factors_generic_pattern")
                    validation_result["specificity_score"] -= 3
                    break

            # Check if climate data lacks city-specific details (length test)
            if all(len(item) < 20 for item in climate_primary):
                validation_result["generic_flags"].append("climate_factors_too_short")
                validation_result["specificity_score"] -= 2

        # Check service triggers for generic patterns
        service_triggers = research_data.get("service_triggers", [])
        if service_triggers and isinstance(service_triggers, list):
            # Handle both old format (list of strings) and new format (list of dicts)
            trigger_keywords = []
            for trigger in service_triggers:
                if isinstance(trigger, dict):
                    trigger_text = trigger.get("trigger", "")
                else:
                    trigger_text = str(trigger)

                keywords = trigger_text.lower().split()
                if keywords:
                    trigger_keywords.append(keywords[0])

            # Check against generic patterns
            for pattern in generic_trigger_patterns:
                if set(trigger_keywords) == set(pattern):
                    validation_result["generic_flags"].append("service_triggers_generic_pattern")
                    validation_result["specificity_score"] -= 3
                    break

        # Check construction eras for generic patterns
        construction_eras = research_data.get("major_construction_eras", [])
        if construction_eras:
            # Extract just the decade/era labels
            era_labels = []
            for era in construction_eras:
                if isinstance(era, dict):
                    period = era.get("period", "")
                else:
                    period = str(era)

                # Simple pattern match for "1970s", "1990s", etc.
                if period in ["1970s", "1980s", "1990s", "2000s", "2010s"]:
                    era_labels.append(period)

            # Check against generic patterns
            for pattern in generic_era_patterns:
                if set(era_labels) == set(pattern):
                    validation_result["generic_flags"].append("construction_eras_generic_decades")
                    validation_result["specificity_score"] -= 3
                    break

            # Check if eras lack specificity notes
            if construction_eras:
                for era in construction_eras:
                    if isinstance(era, dict) and not era.get("specificity_note"):
                        validation_result["generic_flags"].append("construction_era_missing_specificity_note")
                        validation_result["specificity_score"] -= 1
                        break

        # Check for missing specificity notes across all fields
        if not research_data.get("climate_factors", {}).get("specificity_note"):
            validation_result["generic_flags"].append("climate_missing_specificity_note")
            validation_result["specificity_score"] -= 1

        building_age = research_data.get("building_age_specificity", {})
        if building_age and not building_age.get("city_specific_note"):
            validation_result["generic_flags"].append("building_age_missing_specificity_note")
            validation_result["specificity_score"] -= 1

        # Check differentiation score
        diff_score = research_data.get("differentiation_score", 0)
        if diff_score < 6:
            validation_result["generic_flags"].append("low_differentiation_score")
            validation_result["specificity_score"] -= 2

        # Check self-validation
        self_val = research_data.get("self_validation", {})
        if not self_val.get("is_city_specific", False):
            validation_result["generic_flags"].append("self_validation_not_city_specific")
            validation_result["specificity_score"] -= 2

        if self_val.get("has_generic_data", False):
            validation_result["generic_flags"].append("self_validation_has_generic_data")
            validation_result["specificity_score"] -= 2

        # Final determination
        if validation_result["specificity_score"] < 5:
            validation_result["is_generic"] = True

        # Log validation results
        if validation_result["is_generic"]:
            logger.warning(
                f"Research for {city_name}, {state} flagged as GENERIC. "
                f"Flags: {validation_result['generic_flags']}, "
                f"Score: {validation_result['specificity_score']}/10"
            )
        else:
            logger.info(
                f"Research for {city_name}, {state} validated as CITY-SPECIFIC. "
                f"Score: {validation_result['specificity_score']}/10"
            )

        return validation_result

    def compare_city_research(
        self,
        city1_research: Dict[str, Any],
        city2_research: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two city research datasets to detect suspiciously similar data.

        If cities return >80% identical data in climate/triggers/eras, flag as too similar.
        This helps detect when GPT-4o is returning generic regional data.

        PART 3 of the city research quality improvement.

        Returns:
            Dict with similarity_score (0-100), is_too_similar (bool), and details
        """
        comparison_result = {
            "similarity_score": 0.0,
            "is_too_similar": False,
            "identical_fields": [],
            "compared_at": datetime.utcnow().isoformat()
        }

        similarity_points = []

        # Compare climate factors
        climate1 = set(city1_research.get("climate_factors", {}).get("primary", []))
        climate2 = set(city2_research.get("climate_factors", {}).get("primary", []))

        if climate1 and climate2:
            intersection = climate1 & climate2
            union = climate1 | climate2
            if union:
                climate_similarity = len(intersection) / len(union) * 100
                similarity_points.append(climate_similarity)
                if climate_similarity > 80:
                    comparison_result["identical_fields"].append("climate_factors")

        # Compare service triggers (extract text from dicts if needed)
        def extract_trigger_texts(triggers):
            texts = []
            for t in triggers:
                if isinstance(t, dict):
                    texts.append(t.get("trigger", ""))
                else:
                    texts.append(str(t))
            return set(texts)

        triggers1 = extract_trigger_texts(city1_research.get("service_triggers", []))
        triggers2 = extract_trigger_texts(city2_research.get("service_triggers", []))

        if triggers1 and triggers2:
            intersection = triggers1 & triggers2
            union = triggers1 | triggers2
            if union:
                trigger_similarity = len(intersection) / len(union) * 100
                similarity_points.append(trigger_similarity)
                if trigger_similarity > 80:
                    comparison_result["identical_fields"].append("service_triggers")

        # Compare construction eras (extract periods)
        def extract_era_periods(eras):
            periods = []
            for e in eras:
                if isinstance(e, dict):
                    periods.append(e.get("period", ""))
                else:
                    periods.append(str(e))
            return set(periods)

        eras1 = extract_era_periods(city1_research.get("major_construction_eras", []))
        eras2 = extract_era_periods(city2_research.get("major_construction_eras", []))

        if eras1 and eras2:
            intersection = eras1 & eras2
            union = eras1 | eras2
            if union:
                era_similarity = len(intersection) / len(union) * 100
                similarity_points.append(era_similarity)
                if era_similarity > 80:
                    comparison_result["identical_fields"].append("construction_eras")

        # Calculate average similarity
        if similarity_points:
            comparison_result["similarity_score"] = sum(similarity_points) / len(similarity_points)
        else:
            comparison_result["similarity_score"] = 0.0

        # Flag as too similar if >80% overlap
        if comparison_result["similarity_score"] > 80:
            comparison_result["is_too_similar"] = True

        # Log results
        city1_name = city1_research.get("city_name", "City1")
        city2_name = city2_research.get("city_name", "City2")

        if comparison_result["is_too_similar"]:
            logger.warning(
                f"Cities {city1_name} and {city2_name} have suspiciously similar research data "
                f"({comparison_result['similarity_score']:.1f}% similar). "
                f"Identical fields: {comparison_result['identical_fields']}"
            )
        else:
            logger.info(
                f"Cities {city1_name} and {city2_name} have sufficiently unique data "
                f"({comparison_result['similarity_score']:.1f}% similar)"
            )

        return comparison_result

    async def get_all_local_data(
        self,
        city_name: str,
        state: str,
        trade_type: str = None
    ) -> Dict[str, Any]:
        """
        Get all available local data for a city: Census data, landmarks, and research.

        Args:
            city_name: City name (e.g., "Tulsa")
            state: Two-letter state code (e.g., "OK")
            trade_type: Optional trade type for research data (e.g., "Garage Door")

        Returns:
            Combined dict with all local data
        """
        # Fetch all data sources in parallel
        tasks = [
            self._fetch_census_housing_age(city_name, state),
            self._fetch_ai_landmarks(city_name, state)
        ]

        # Add research task if trade type provided
        if trade_type:
            tasks.append(self.fetch_city_research_data(city_name, state, trade_type))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        combined_data = {
            "city": city_name,
            "state": state,
            "housing_facts": results[0] if not isinstance(results[0], Exception) else [],
            "landmarks": results[1] if not isinstance(results[1], Exception) else [],
        }

        # Add research data if available
        if trade_type and len(results) > 2:
            research = results[2] if not isinstance(results[2], Exception) else {}
            combined_data["research"] = research

        return combined_data

    def format_for_prompt(self, city_data: Dict[str, Any]) -> str:
        """
        Format city data for inclusion in AI prompt.
        Includes research data alongside housing facts and landmarks.

        Updated to handle new research structure with specificity notes.
        """
        if not city_data:
            return ""

        lines = []

        # Add housing facts (Census data)
        if city_data.get("housing_facts"):
            for fact in city_data["housing_facts"]:
                lines.append(f"VERIFIED LOCAL FACT: {fact}")

        # Add landmarks
        if city_data.get("landmarks"):
            landmarks_str = ", ".join(city_data["landmarks"][:3])  # Max 3 landmarks
            lines.append(f"VERIFIED LANDMARKS: {landmarks_str}")

        # Add research data
        if city_data.get("research"):
            research = city_data["research"]

            # Building age from research (new structure)
            building_age = research.get("building_age_specificity", {})
            if isinstance(building_age, dict):
                median_year = building_age.get("median_year")
                city_note = building_age.get("city_specific_note")
                if median_year:
                    line = f"COMMERCIAL BUILDING AGE: Median year built {median_year}"
                    if city_note:
                        line += f" ({city_note})"
                    lines.append(line)
            else:
                # Backwards compatibility with old structure
                if research.get("building_age_median"):
                    lines.append(f"COMMERCIAL BUILDING AGE: Median year built {research['building_age_median']}")

            # Construction eras (new structure with details)
            construction_eras = research.get("major_construction_eras", [])
            if construction_eras:
                for era in construction_eras[:3]:  # Max 3 eras
                    if isinstance(era, dict):
                        period = era.get("period", "")
                        description = era.get("description", "")
                        if period and description:
                            lines.append(f"CONSTRUCTION ERA: {period} - {description}")
                    else:
                        # Backwards compatibility
                        lines.append(f"CONSTRUCTION ERA: {era}")

            # Climate factors (enhanced structure)
            climate = research.get("climate_factors", {})
            if climate.get("primary"):
                primary = climate["primary"]
                if isinstance(primary, list):
                    # New structure has detailed descriptions in list items
                    for factor in primary[:3]:  # Max 3 factors
                        lines.append(f"CLIMATE FACTOR: {factor}")
                else:
                    # Fallback
                    lines.append(f"CLIMATE FACTORS: {primary}")

            if climate.get("service_impacts"):
                lines.append(f"SERVICE IMPACTS: {climate['service_impacts']}")

            # Service triggers (new structure with context)
            service_triggers = research.get("service_triggers", [])
            if service_triggers:
                for trigger in service_triggers[:3]:  # Max 3 triggers
                    if isinstance(trigger, dict):
                        trigger_text = trigger.get("trigger", "")
                        context = trigger.get("context", "")
                        if trigger_text:
                            line = f"SERVICE TRIGGER: {trigger_text}"
                            if context:
                                line += f" - {context}"
                            lines.append(line)
                    else:
                        # Backwards compatibility
                        lines.append(f"SERVICE TRIGGER: {trigger}")

            # Permit requirements (new structure)
            permit_req = research.get("permit_requirements")
            if permit_req:
                if isinstance(permit_req, dict):
                    description = permit_req.get("description")
                    unique_aspects = permit_req.get("unique_aspects")
                    if description:
                        lines.append(f"PERMIT INFO: {description}")
                    if unique_aspects:
                        lines.append(f"PERMIT UNIQUE ASPECTS: {unique_aspects}")
                else:
                    # Backwards compatibility
                    lines.append(f"PERMIT INFO: {permit_req}")

            # Unique factors (new structure with specificity notes)
            unique_factors = research.get("unique_factors", [])
            if unique_factors:
                for factor in unique_factors[:2]:  # Max 2 unique factors
                    if isinstance(factor, dict):
                        factor_text = factor.get("factor", "")
                        if factor_text:
                            lines.append(f"LOCAL FACTOR: {factor_text}")
                    else:
                        # Backwards compatibility
                        lines.append(f"LOCAL FACTOR: {factor}")

        if not lines:
            return ""

        return "\n".join(lines)


# Global instance
local_data_fetcher = LocalDataFetcher()
