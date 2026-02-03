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
        try:
            asyncio.get_running_loop()
            local_data = None  # Skip if already in event loop
        except RuntimeError:
            local_data = asyncio.run(
                local_data_fetcher.get_all_local_data(
                    data.city,
                    data.state,
                    trade_name  # Use actual trade to get rich research data
                )
            )
    except Exception as e:
        print(f"Warning: Could not fetch local data for {data.city}, {data.state}: {e}")
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

    # Check if we have building age data (median year)
    has_building_age_data = False
    if local_data and local_data.get("research"):
        building_age = local_data["research"].get("building_age_specificity", {})
        median_year = building_age.get("median_year")
        has_building_age_data = median_year is not None and median_year != ""

    # Build conditional housing requirement based on data availability
    if has_building_age_data:
        housing_requirement = f'REQUIRED: "{city}\'s housing boom centered on {median_year}" - use this EXACT year ({median_year}), do not change or invent a different year'
        housing_instruction = f"Use median year {median_year}, construction eras → {trade_name} impacts (60w)"
    else:
        housing_requirement = "OPTIONAL: If building age data is available in research, mention it. If not available (median_year is null), focus on other local factors instead. DO NOT invent or guess years."
        housing_instruction = f"Focus on other local factors from research (climate, permits, unique characteristics) → {trade_name} impacts (60w)"

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
- "locally", "local", "local property owners"
- "serving the area", "in your area"
- "trusted", "top-rated", "best", "premier", "award-winning"
- "we offer the following services", "services include"
- "SEO", "search engine optimization"

==================================================
STRUCTURE (1,100-1,300 words):
==================================================

1) CITY CONTEXT (4 paragraphs, 200-250w)
   - Housing: {housing_instruction}
   - Climate: Specific weather data → {trade_name} stress (60w)
   - Issues: What fails from age + climate (60w)
   - Coverage: 2+ landmarks from research (50w)

2) COMMON ISSUES (2 paragraphs, 150-200w)
   - Primary: {trade_name} problems, WHY (100w)
   - Secondary: Climate issues, when found (80w)

3) TRIGGERS (30w): What prompts calls. NO service names. Unique per city.

4) DECISION (20w): Why explore services. Spoken tone.

5) SERVICE LINKS: Output EXACTLY: {{{{CITY_SERVICE_LINKS}}}}

6) {city.upper()} PROPERTIES (2 paragraphs, 150-200w)
   - Approach for {city}'s stock (90w)
   - {city}, {state} permits (80w)

7) PROCESS (3 paragraphs, 200-250w)
   - Assessment (80w)
   - Recommendations (80w)
   - Execution (70w)

BANNED: "locally", "serving the area", "trusted", "quality service"
BANNED OPENINGS: "In the area, many homes"
{housing_requirement}

JSON SCHEMA:
{{
  "blocks": [
    {{"type": "paragraph", "text": "Housing"}},
    {{"type": "paragraph", "text": "Climate"}},
    {{"type": "paragraph", "text": "Issues"}},
    {{"type": "paragraph", "text": "Coverage"}},
    {{"type": "heading", "level": 2, "text": "Common {trade_name} Issues in {city}"}},
    {{"type": "paragraph", "text": "Primary"}},
    {{"type": "paragraph", "text": "Secondary"}},
    {{"type": "heading", "level": 2, "text": "Services Available in {city}"}},
    {{"type": "paragraph", "text": "Triggers"}},
    {{"type": "paragraph", "text": "Decision"}},
    {{"type": "paragraph", "text": "{{{{CITY_SERVICE_LINKS}}}}"}},
    {{"type": "heading", "level": 2, "text": "How We Handle {city} Properties"}},
    {{"type": "paragraph", "text": "Approach"}},
    {{"type": "paragraph", "text": "Permits"}},
    {{"type": "heading", "level": 2, "text": "Our Process"}},
    {{"type": "paragraph", "text": "Assessment"}},
    {{"type": "paragraph", "text": "Recommendations"}},
    {{"type": "paragraph", "text": "Execution"}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

Use local research extensively. Each city must be unique.
"""

    try:
        result = generator._call_openai_json(system_prompt, user_prompt, max_tokens=6000)
        print(f"✓ City hub for {data.city} generated successfully")
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
            "text": f"Because many homes in {city} were built before modern standards were common, issues are often uncovered during inspections or remodels rather than routine maintenance, which changes how problems are prioritized."
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"Services Available in {city}"
        },
        {
            "type": "paragraph",
            "text": f"Work requests typically follow equipment failures, renovation discoveries, or inspection findings that need professional assessment in {city}."
        },
        {
            "type": "paragraph",
            "text": f"Determining whether an issue requires immediate attention or can be addressed during planned updates depends on the specific situation and {city}'s local building requirements."
        },
        {
            "type": "paragraph",
            "text": "{{CITY_SERVICE_LINKS}}"
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Why Choose Us"
        },
        {
            "type": "paragraph",
            "text": "Most jobs start by figuring out whether the issue is isolated or part of something bigger. If it's something that can wait, that's said clearly. If it's likely to cause trouble later, the reason is explained along with options. When permits or inspections are involved, that's discussed up front so there are no surprises. The goal is to leave the work done correctly and make sure the customer understands what changed."
        },
    ]
    
    if data.phone and data.cta_text:
        blocks.append({
            "type": "cta",
            "text": data.cta_text,
            "phone": data.phone
        })
    
    return {"blocks": blocks}