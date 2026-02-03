"""
City Hub page generation for AI content generator.
This module generates city-localized hub pages (e.g., "Electrician in Tulsa, OK").
"""

from app.models import GeneratePageResponse, PageData
from app.vertical_profiles import get_vertical_profile, get_trade_name


def _validate_industry_content(blocks: list, trade_name: str, vertical: str) -> None:
    """
    Validate that AI-generated content doesn't contain wrong industry terms.
    Raises exception if wrong industry content is detected.
    """
    # Define wrong industry terms that should never appear
    # Map vertical names to their industry keys
    vertical_to_industry = {
        "electrician": "electrical",
        "plumber": "plumbing",
        "hvac": "hvac",
        "roofer": "roofing",
        "painter": "painting",
        "flooring": "flooring",
        "lighting": "lighting"
    }
    
    wrong_terms = {
        "lighting": ["lighting", "light fixture", "led retrofit", "illumination"],
        "electrical": ["electrical", "wiring", "circuit", "panel", "breaker"],
        "plumbing": ["plumbing", "pipe", "drain", "faucet", "water heater"],
        "hvac": ["hvac", "air conditioning", "heating", "furnace", "ductwork"],
        "roofing": ["roofing", "shingle", "membrane", "flashing"],
        "painting": ["painting", "paint", "coating"],
        "flooring": ["flooring", "carpet", "tile", "hardwood"]
    }
    
    # Get the industry key for this vertical
    current_industry = vertical_to_industry.get(vertical.lower(), vertical.lower())
    
    # Get terms to check based on vertical (exclude own industry)
    terms_to_check = []
    for industry, terms in wrong_terms.items():
        # Don't check for terms from the same industry
        if industry != current_industry:
            terms_to_check.extend(terms)
    
    # Check all paragraph blocks for wrong terms
    for block in blocks:
        if block.get("type") == "paragraph":
            text = block.get("text", "").lower()

            for term in terms_to_check:
                if term in text:
                    raise Exception(
                        f"AI generated wrong industry content: '{term}' found in {trade_name} page. "
                        f"Content must only discuss {trade_name}-related work."
                    )


def generate_city_hub_content(generator, data: PageData) -> GeneratePageResponse:
    """
    Generate city hub page content (city-localized hub page).

    Args:
        generator: The AIContentGenerator instance
        data: Page generation parameters with hub + city information

    Returns:
        Complete validated city hub page content
    """
    import asyncio
    from app.local_data_fetcher import local_data_fetcher

    vertical = data.vertical or "other"
    profile = get_vertical_profile(vertical)
    trade_name = profile["trade_name"]

    # Fetch comprehensive local data (Census + landmarks + research)
    # Note: Uses trade-specific research (building ages/climate are same across trades)
    local_data = None
    try:
        # Check if we're in an existing event loop (e.g., called from async worker)
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context - need to run in a new thread to avoid nested loop issues
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    local_data_fetcher.get_all_local_data(
                        data.city,
                        data.state,
                        trade_name
                    )
                )
                local_data = future.result(timeout=30)
            print(f"[CityHub] Fetched local data (async context) for {data.city}, {data.state}")
        except RuntimeError:
            # No running event loop - safe to use asyncio.run() directly
            local_data = asyncio.run(
                local_data_fetcher.get_all_local_data(
                    data.city,
                    data.state,
                    trade_name  # Use actual trade to get rich research data
                )
            )
            print(f"[CityHub] Fetched local data (sync context) for {data.city}, {data.state}")

        # Debug: Log what we got
        if local_data and local_data.get("research"):
            research = local_data["research"]
            building_age = research.get("building_age_specificity", {})
            median_year = building_age.get("median_year")
            print(f"[CityHub] Research data for {data.city}: median_year={median_year}")
        else:
            print(f"[CityHub] WARNING: No research data found for {data.city}, {data.state}")

    except Exception as e:
        print(f"[CityHub] ERROR fetching local data for {data.city}, {data.state}: {e}")
        local_data = None

    # Build title programmatically
    hub_label = data.hub_label or "Services"
    city = data.city or "Your City"
    state = data.state or "ST"
    
    # Title: "Commercial Electrical Services in Tulsa | Business Name"
    # Hub label should be the full service hub title (e.g., "Commercial Electrical Services")
    title = f"{hub_label} in {city}"
    if data.business_name:
        title += f" | {data.business_name}"
    
    # Build H1 (without business name)
    h1_text = f"{hub_label} in {city}"
    
    # Build slug programmatically (city-slug, not hub-slug)
    city_slug = data.city_slug or generator.slugify("", f"{city}-{state}")
    
    # Build meta description following Google best practices (155-160 chars)
    # - Compelling and unique
    # - Includes location and service category
    # - Clear call-to-action
    # - No generic marketing fluff
    meta_description = f"Expert {hub_label.lower()} in {city}, {state}. "
    meta_description += f"Licensed professionals, quality workmanship, reliable service. "
    meta_description += f"{data.cta_text}!"
    
    # Ensure optimal length (155-160 characters)
    if len(meta_description) > 160:
        meta_description = meta_description[:157] + "..."
    elif len(meta_description) < 120:
        # Add service area if too short
        if data.service_area_label:
            meta_description = f"Expert {hub_label.lower()} in {city}, {state}. Serving {data.service_area_label}. {data.cta_text}!"
            if len(meta_description) > 160:
                meta_description = meta_description[:157] + "..."
    
    # Generate content blocks via LLM
    content_json = _call_openai_city_hub_generation(generator, data, profile, local_data)
    
    blocks = content_json.get("blocks", [])
    
    # Validate content doesn't contain wrong industry terms
    _validate_industry_content(blocks, trade_name, vertical)
    
    # Prepend H1 and intro paragraph for hero section (WordPress will format as hero)
    hero_blocks = [
        {
            "type": "heading",
            "level": 1,
            "text": h1_text
        }
    ]
    
    # If first block is a paragraph, it becomes the hero paragraph
    if blocks and blocks[0].get("type") == "paragraph":
        hero_blocks.append(blocks[0])
        blocks = blocks[1:]
    else:
        # Add default hero paragraph
        hero_blocks.append({
            "type": "paragraph",
            "text": f"Professional {hub_label.lower()} {trade_name} services in {city}, {state}. Expert solutions for your property."
        })
    
    # Combine hero blocks with content blocks
    all_blocks = hero_blocks + blocks
    
    # Assemble response
    response = GeneratePageResponse(
        title=title,
        meta_description=meta_description[:160],
        slug=city_slug,
        blocks=all_blocks,
        page_mode="city_hub"
    )
    
    return response


def _get_banned_trades(current_trade: str) -> str:
    """Get list of banned trade names excluding the current trade."""
    all_trades = ["electrical", "plumbing", "HVAC", "lighting", "roofing", "painting", "flooring", "concrete", "siding"]
    current_trade_lower = current_trade.lower()
    
    # Remove the current trade from banned list
    banned = [t for t in all_trades if t.lower() != current_trade_lower]
    
    return ", ".join(banned)


def _call_openai_city_hub_generation(generator, data: PageData, profile: dict, local_data: dict = None) -> dict:
    """Call OpenAI to generate city hub page content blocks."""

    trade_name = profile["trade_name"]
    vocabulary = profile.get("vocabulary", [])
    hub_label = data.hub_label or "Services"
    city = data.city or "Your City"
    state = data.state or "ST"

    # Note: We do NOT pass service names to the AI to avoid enumeration
    # The shortcode will handle service discovery and display
    
    system_prompt = f"""You are an expert {trade_name} content writer. Write EXCLUSIVELY about {trade_name.upper()} work.

⚠️ NEVER mention: {_get_banned_trades(trade_name)} or terms like "heating", "HVAC", "plumbing", "roofing", or other trades.
Use ONLY {trade_name} vocabulary: {', '.join(vocabulary[:10])}

RULES: Mention {city}, {state} naturally. Write like a contractor, not marketing. Output ONLY valid JSON. No HTML lists.

BANNED PHRASES (never use these):
- "locally" / "local property owners" / "serving the local area" / "in your area"
- "trusted by" / "top-rated" / "best in" / "#1 choice"
- "we offer the following services" / "services include"
- "premier" / "top-notch" / "best-in-class"
- "SEO" / "search engine optimization"
- No meta-language like "this page", "this article"
"""

    # Determine target audience based on hub label
    is_commercial = hub_label and 'commercial' in hub_label.lower()
    target_audience = "business owner" if is_commercial else "homeowner"
    property_type = "commercial properties" if is_commercial else "homes"
    business_type = f"{hub_label.lower()} {trade_name}" if hub_label else trade_name

    # Format local data if available
    local_facts = ""
    if local_data:
        from app.local_data_fetcher import local_data_fetcher
        if local_data.get("housing_facts") or local_data.get("landmarks") or local_data.get("research"):
            local_facts = "\n\n" + local_data_fetcher.format_for_prompt(local_data)

    # Check if we have building age data (median year or construction era)
    has_building_age_data = False
    building_year_info = None

    if local_data and local_data.get("research"):
        research = local_data["research"]
        building_age = research.get("building_age_specificity", {})
        median_year = building_age.get("median_year")

        if median_year is not None and median_year != "":
            # We have a specific median year
            has_building_age_data = True
            building_year_info = str(median_year)
            print(f"[CityHub] Using median_year: {median_year}")
        else:
            # No median year - check for major_construction_eras as fallback
            construction_eras = research.get("major_construction_eras", [])
            if construction_eras and len(construction_eras) > 0:
                first_era = construction_eras[0]
                era_period = first_era.get("period", "")
                if era_period:
                    has_building_age_data = True
                    building_year_info = era_period  # e.g., "1985-1990"
                    print(f"[CityHub] Using construction era: {era_period}")

            if not has_building_age_data:
                print(f"[CityHub] No building age data available for {city}")

    # Build conditional housing requirement based on data availability
    if has_building_age_data and building_year_info:
        housing_requirement = f'REQUIRED: "{city}\'s housing boom centered on {building_year_info}" - use this EXACT year/period ({building_year_info}), do not change or invent a different year'
        housing_instruction = f"Use year/period {building_year_info}, construction eras → {trade_name} impacts (60w)"
    else:
        housing_requirement = f"""⚠️ CRITICAL: NO BUILDING AGE DATA EXISTS FOR {city.upper()}.
You MUST NOT mention any specific years like "1979", "1980s", "built around 19XX", etc.
Instead, use phrases like "older homes", "aging infrastructure", "established neighborhoods".
ANY mention of a specific year will be REJECTED as hallucination."""
        housing_instruction = f"Focus on other local factors from research (climate, permits, unique characteristics) → {trade_name} impacts (60w). NO YEARS."

    # Build "USING VERIFIED LOCAL CONTEXT" section if research data exists
    using_context_section = ""
    if local_data and local_data.get("research"):
        using_context_section = f"""

==================================================
⚠️ USING VERIFIED LOCAL CONTEXT
==================================================
The local_context below contains REAL, VERIFIED data about {city}, {state}:
- Census housing facts (building ages, construction periods)
- Real landmarks verified by AI research
- City-specific construction patterns, climate factors, and service demand drivers

CRITICAL RULES:
1. YOU MUST use at least 1 specific fact from the research data in your overview
2. DO NOT invent local context - ONLY use what's provided
3. Focus on factors that create service demand across multiple trades

EXAMPLE:
✅ "Many of {city}'s commercial buildings date from the 1978-1982 construction boom, creating consistent renovation needs across {trade_name} services"
   (Uses specific construction era to explain multi-trade demand)
"""

    user_prompt = f"""You are generating a City Hub page for a {business_type} service business.{local_facts}{using_context_section}

PAGE TYPE:
City Hub (category + city context page)

This page is NOT:
- a service page
- a full service hub
- a marketing page

Its purpose:
To explain WHY this category of work commonly comes up in THIS city and to guide the reader naturally to the next step.

Hub Category: {hub_label}
City: {city}, {state}
Business Type: {trade_name}
Business Name: {data.business_name or 'Our Company'}
Phone: {data.phone or ''}
Service Area: {data.service_area_label or city}
CTA Text: {data.cta_text}
Trade Vocabulary: {', '.join(vocabulary[:8])}
Target Audience: {target_audience}
Property Type: {property_type}

==================================================
INDUSTRY CONTEXT (CRITICAL - READ CAREFULLY)
==================================================
You are writing for a {trade_name} business.
- ONLY discuss {trade_name}-related work and issues
- NEVER mention these other trades: {_get_banned_trades(trade_name)}
- Use ONLY vocabulary from this list: {', '.join(vocabulary[:8])}
- If you mention upgrades, repairs, or issues, they MUST be {trade_name}-specific
- Any mention of "electrical service", "plumbing work", "HVAC systems", or other non-{trade_name} work will cause IMMEDIATE REJECTION
- DO NOT default to electrical content - you are writing for {trade_name.upper()}

==================================================
ABSOLUTE RULES (NON-NEGOTIABLE)
==================================================
- Write like a real tradesperson explaining work to a {target_audience}.
- Sound practical and conversational, not polished marketing.
- Do NOT enumerate services in prose.
- Do NOT use bullet points or numbered lists.
- Do NOT repeat sentence structures across city pages.
- Do NOT write content that would still make sense if the city name were swapped.

BANNED WORDS / PHRASES (NEVER USE):
- "locally", "local", "local property owners", "in your area", "serving the area"
- "trusted", "top-rated", "best", "premier", "award-winning", "#1", "top choice"
- "we offer the following services", "services include", "our services"
- "SEO", "search engine optimization"
- "quality service", "quality work", "quality craftsmanship"

SPECIFIC DUPLICATE PHRASES TO AVOID (use completely different wording):
- "The tricky part is figuring out whether..."
- "Given the age of many homes in {city}..."
- "What seems like a minor issue could indicate..."
- "Understanding whether a minor issue is isolated..."
- "The first step in our process is..."
- "Many properties in {city} eventually need..."

BANNED OPENING PATTERNS (must vary across cities):
- "In the area, many homes were built/constructed around..."
- "In the area, most homes date from..."
- "In the area, the majority of homes..."
- "{city}'s housing boom centered on..." (if using this, heavily vary the rest of the sentence)

REQUIRED: Each city must open differently. Rotate between:
- Climate-first: "{city}'s [climate characteristic] creates unique challenges for {trade_name} systems..."
- Problem-first: "Homeowners in {city} frequently encounter [specific issue] because..."
- Neighborhood-first: "Properties in [neighborhood] and [neighborhood] face..."
- Question-first: "Why do {city} homes need {trade_name} attention more than average?"

==================================================
STRUCTURE (900-1,100 words MINIMUM):
==================================================

⚠️ CRITICAL LENGTH REQUIREMENT:
Your total output MUST be at least 900 words. Count paragraphs before submitting.
If under 900 words, expand sections 1, 2, or 6 until you reach minimum.
Pages under 900 words will be REJECTED and regenerated.

1) CITY CONTEXT (4-5 paragraphs, 280-350w)
   - Opening: {housing_instruction} + neighborhoods (80-100w)
   - Climate: Specific weather data → {trade_name} stress (80-100w)
   - Issues: What fails from age + climate (80-100w)
   - Coverage: 2-3 landmarks + neighborhoods from research (60-80w)
   - Optional 5th paragraph: Unique city characteristic (40-50w)

2) COMMON ISSUES (3 paragraphs, 220-280w)
   - Primary: Top {trade_name} problems in {city}, root causes (90-100w)
   - Secondary: Climate/weather-related issues (70-90w)
   - Seasonal: How seasons affect service calls in {city} (60-90w)

3) TRIGGERS (40-60w): What prompts homeowners to call. Be specific to {city}. NO service lists.

4) DECISION (30-40w): Why addressing issues matters. Natural tone, not salesy.

5) SERVICE LINKS: Output EXACTLY: {{{{CITY_SERVICE_LINKS}}}}

6) {city.upper()} PROPERTIES (2-3 paragraphs, 200-250w)
   - City-specific approach with EXAMPLE from {city} (100-120w)
   - Permits + local requirements specific to {city}, {state} (80-100w)
   - Optional: Neighborhood-specific considerations (40-50w)

7) REAL PROJECT EXAMPLE (1-2 paragraphs, 120-180w)
   Generate a realistic case study:
   - Location: Specific {city} neighborhood or landmark area
   - Problem: Concrete {trade_name} issue tied to local factors
   - Discovery: What assessment revealed
   - Solution: Specific {trade_name} work performed
   - Outcome: Measurable result for homeowner
   
   Format: "Last [season] in [neighborhood], we worked with a {target_audience} who noticed [problem].
   The [component] had [issue], likely from [local factor like building age/weather].
   We [solution]. Now they [outcome]."
   
   MUST reference real landmark/neighborhood from research.
   MUST tie to local building age, climate, or permit requirements.

BANNED: "locally", "serving the area", "trusted", "quality service", "the first step"
{housing_requirement}

STRUCTURE FLEXIBILITY:
- You may combine sections if they flow naturally
- Vary heading styles ("Common Issues" vs "What Fails in {city}")
- Add extra paragraphs to any section if needed for depth
- Goal: 5 different cities should NOT have identical structures

⚠️ CRITICAL JSON FORMAT: Your output MUST use a "blocks" array with objects containing "type" keys.
DO NOT use "sections". DO NOT use "heading"/"paragraph" as keys. Use "type": "paragraph" or "type": "heading".

JSON SCHEMA (15-18 blocks total):
{{
  "blocks": [
    {{"type": "paragraph", "text": "Opening: Housing + neighborhoods (80-100w)"}},
    {{"type": "paragraph", "text": "Climate specifics (80-100w)"}},
    {{"type": "paragraph", "text": "What fails (80-100w)"}},
    {{"type": "paragraph", "text": "Landmarks + coverage (60-80w)"}},
    {{"type": "paragraph", "text": "Optional: Unique city factor (40-50w)"}},
    {{"type": "heading", "level": 2, "text": "Common {trade_name} Issues in {city}"}},
    {{"type": "paragraph", "text": "Primary problems (90-100w)"}},
    {{"type": "paragraph", "text": "Secondary climate issues (70-90w)"}},
    {{"type": "paragraph", "text": "Seasonal patterns (60-90w)"}},
    {{"type": "heading", "level": 2, "text": "Services Available in {city}"}},
    {{"type": "paragraph", "text": "Triggers (40-60w)"}},
    {{"type": "paragraph", "text": "Decision (30-40w)"}},
    {{"type": "paragraph", "text": "{{{{CITY_SERVICE_LINKS}}}}"}},
    {{"type": "heading", "level": 2, "text": "How We Handle {city} Properties"}},
    {{"type": "paragraph", "text": "Approach with example (100-120w)"}},
    {{"type": "paragraph", "text": "Permits (80-100w)"}},
    {{"type": "heading", "level": 2, "text": "Recent {city} Project"}},
    {{"type": "paragraph", "text": "Case study (120-180w)"}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

CRITICAL: Total word count across all paragraphs must be 900-1,100 words.
Use local research extensively. Each city must be unique.
"""

    try:
        result = generator._call_openai_json(system_prompt, user_prompt, max_tokens=10000)
        print(f"✓ City hub for {data.city} generated successfully")
        
        # Validate word count
        blocks = result.get("blocks", [])
        total_text = ' '.join([b.get('text', '') for b in blocks if b.get('type') == 'paragraph'])
        word_count = len(total_text.split())
        
        if word_count < 850:
            print(f"⚠️ WARNING: Generated content for {data.city} is only {word_count} words (target: 900+)")
            print(f"   Consider regenerating or manually expanding content")
        else:
            print(f"✓ Word count for {data.city}: {word_count} words")
        
        return result

    except Exception as e:
        print(f"❌ FAILED: City hub generation error for {data.city}: {e}")
        # Return fallback content
        return _generate_fallback_city_hub_content(data, profile)


def _generate_fallback_city_hub_content(data: PageData, profile: dict) -> dict:
    """Generate fallback city hub content if AI generation fails."""

    trade_name = profile["trade_name"]
    hub_label = data.hub_label or "Services"
    city = data.city or "Your City"
    state = data.state or "ST"

    blocks = [
        {
            "type": "paragraph",
            "text": f"{city}, {state} has a mix of older and newer construction, which creates varying {trade_name} demands across different neighborhoods. Many properties built before modern standards require updates to meet current codes and handle today's usage patterns."
        },
        {
            "type": "paragraph",
            "text": f"The local climate in {city} affects {trade_name} systems through seasonal temperature fluctuations and weather events common to the region. These environmental factors contribute to wear patterns that differ from other areas."
        },
        {
            "type": "paragraph",
            "text": f"Common issues in {city} homes often stem from the combination of building age and local conditions. Components that worked adequately when first installed may now need attention due to increased demands or accumulated wear."
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"Common {trade_name} Issues in {city}"
        },
        {
            "type": "paragraph",
            "text": f"Primary concerns typically involve components showing age-related wear or insufficient capacity for current needs. These issues often become apparent during renovations, inspections, or when adding new equipment."
        },
        {
            "type": "paragraph",
            "text": f"Weather-related problems in {city} include damage from storms, temperature extremes, and moisture issues specific to the local climate. These tend to surface seasonally or after significant weather events."
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"Services Available in {city}"
        },
        {
            "type": "paragraph",
            "text": f"Calls typically come in after equipment failures, during renovation projects, or when routine maintenance reveals potential issues. {city} homeowners often contact us when facing immediate problems or planning larger updates."
        },
        {
            "type": "paragraph",
            "text": f"Addressing {trade_name} issues promptly helps prevent larger problems and ensures systems meet current safety standards and usage requirements."
        },
        {
            "type": "paragraph",
            "text": "{{CITY_SERVICE_LINKS}}"
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"How We Handle {city} Properties"
        },
        {
            "type": "paragraph",
            "text": f"Our approach in {city} accounts for the area's building characteristics and local requirements. We start by assessing the current system condition and identifying any issues that need immediate attention versus those that can be planned for later."
        },
        {
            "type": "paragraph",
            "text": f"Work in {city}, {state} requires permits and inspections for most significant {trade_name} projects. We coordinate these requirements and ensure all work meets local codes."
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"Recent {city} Project"
        },
        {
            "type": "paragraph",
            "text": f"Recently in {city}, we worked with a homeowner whose older system was struggling to meet modern demands. The existing setup had been adequate when installed but needed upgrades to handle current usage. After assessment, we implemented appropriate solutions that resolved the immediate concerns while meeting local code requirements. The homeowner now has a reliable system appropriate for their needs."
        },
    ]
    
    if data.phone and data.cta_text:
        blocks.append({
            "type": "cta",
            "text": data.cta_text,
            "phone": data.phone
        })
    
    return {"blocks": blocks}