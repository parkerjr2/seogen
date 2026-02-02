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
        if block.get("type") in ["paragraph", "faq"]:
            text = block.get("text", "").lower()
            if block.get("type") == "faq":
                text += " " + block.get("answer", "").lower()
            
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
    # Note: CITY_HUB research uses "General" trade type for cross-trade insights
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
                    "General"  # Use "General" trade type for city-level research
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
    
    system_prompt = f"""You are an expert {trade_name} content writer creating a city hub page.

⚠️ CRITICAL TRADE FOCUS - IMMEDIATE REJECTION IF VIOLATED ⚠️
You are writing EXCLUSIVELY about {trade_name.upper()} work.
NEVER mention: {_get_banned_trades(trade_name)}

SPECIFIC BANNED TERMS (these will cause automatic rejection):
- "heating", "air conditioning", "HVAC", "furnace", "AC unit", "ductwork"
- "plumbing", "pipes", "drains", "water heater", "faucets"
- "roofing", "shingles", "gutters", "roof repair"
- Any mention of other trades or their work

ONLY discuss {trade_name}-specific components, issues, and systems.
Use ONLY vocabulary from this list: {', '.join(vocabulary[:10])}

BAD EXAMPLE (DO NOT DO THIS):
"Homes in this area commonly need electrical, plumbing, and HVAC updates."
❌ This mentions plumbing and HVAC - REJECTED

GOOD EXAMPLE:
"Homes in this area commonly need panel upgrades, outlet additions, and code compliance work."
✅ Only mentions electrical work - APPROVED

CRITICAL RULES:
1. Mention {city}, {state} naturally but sparingly (2-3 times total in intro)
2. Do NOT mention any other cities or towns
3. Use trade-specific vocabulary: {', '.join(vocabulary[:10])}
4. Write like a real contractor, not marketing copy
5. Output ONLY valid JSON matching the schema below
6. Do NOT output any HTML lists (<ul>, <ol>, bullets, or numbered lists)

BANNED PHRASES (never use these):
- "locally" / "local property owners" / "serving the local area" / "in your area"
- "trusted by" / "top-rated" / "best in" / "#1 choice"
- "we offer the following services" / "services include"
- "premier" / "top-notch" / "best-in-class"
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

==================================================
REQUIRED STRUCTURE (FOLLOW EXACTLY)
==================================================

TARGET WORD COUNT: 1,100-1,300 words total (across all sections)

### 1) CITY-SPECIFIC CONTEXT (200-250 words, 4 paragraphs)
Purpose: Establish THIS city's unique characteristics and how they affect {trade_name} work.

**Paragraph 1 - Housing Stock & Construction Era (3-4 sentences, ~60 words)**
- Use SPECIFIC data from local research (median year built, construction boom periods)
- Mention {city} by name
- Connect construction era to current {trade_name} challenges
- Example pattern: "In {city}, the majority of {property_type} were built during [era], which means [specific {trade_name} consequence]..."
- DO NOT write anything that could apply to any city

**Paragraph 2 - Climate & Environmental Factors (3-4 sentences, ~60 words)**
- Use SPECIFIC weather/climate data from local research
- Connect climate to {trade_name} stress factors
- Example pattern: "The area experiences [specific climate factor], which creates [specific {trade_name} issue]..."
- Must include measurable data (temperatures, storm frequency, etc.)

**Paragraph 3 - Common Issues That Result (3-4 sentences, ~60 words)**
- Connect housing age + climate to specific {trade_name} problems
- Describe what typically fails, wears out, or needs updating
- Reference {trade_name}-specific components
- Show cause-and-effect from local factors

**Paragraph 4 - Neighborhood Coverage (2-3 sentences, ~50 words)**
- Mention at least 2 specific landmarks or neighborhoods from local research
- Describe service coverage area naturally
- Example pattern: "From {property_type} near [landmark] to properties around [landmark]..."
- NO generic "serving the area" language

### 2) COMMON {trade_name.upper()} ISSUES IN {city.upper()} (150-200 words, 2 paragraphs)
Purpose: Describe city-specific problems based on local factors.

**Paragraph 1 - Primary Issues (5-6 sentences, ~100-120 words)**
- Describe the MOST common {trade_name} issues in {city}
- Use housing age data to explain WHY these issues occur
- Include specific examples of what fails or needs updating
- Reference {trade_name} components directly
- Connect to local factors (age, climate, construction era)

**Paragraph 2 - Secondary Issues (3-4 sentences, ~70-100 words)**
- Describe issues related to climate or specific construction methods from that era
- Explain how these issues typically present themselves
- Describe when they're usually discovered (inspections, renovations, failures)
- Must be specific to {trade_name} work

### 3) SERVICES CONTEXT — REAL TRIGGERS (1-2 sentences, ~30 words)
Purpose: Describe what actually prompts calls WITHOUT naming services.

Rules:
- Do NOT name or list services
- Describe real situations or moments of uncertainty
- Avoid vague phrases like "many {target_audience}s" or "people often"

⚠️ CRITICAL: Create UNIQUE variations for each city - DO NOT copy these examples:

STYLE GUIDANCE - Create your own unique variations:
Example variety (DO NOT copy these - make your own):
- City A: "after a breaker trips repeatedly, an outlet stops working, or a renovation reveals outdated wiring"
- City B: "when lights flicker during storms, appliances trip circuits, or home inspections flag safety concerns"
- City C: "following power surges, when adding new appliances, or after noticing burning smells"

Your sentence must be COMPLETELY DIFFERENT from all examples above and from other cities.

### 4) DECISION TENSION — WHY LOOK DEEPER (ONE sentence, ~20 words)
Purpose: Explain WHY someone would need to explore service pages.

Rules:
- ONE sentence only
- No service names
- Must feel spoken, not written

GOOD PATTERNS (rotate, do NOT reuse verbatim):
- "The tricky part is figuring out whether what you're seeing is a one-off issue or part of something bigger."
- "What looks like a small problem can sometimes point to a larger update, which is why the details matter."
- "Once you know what's happening, the next step is understanding which type of work actually applies."

### 5) SERVICE LINKS INSERTION POINT (MANDATORY)
On its OWN LINE, output EXACTLY the following token and nothing else:

{{{{CITY_SERVICE_LINKS}}}}

Rules:
- Do NOT wrap this token in a paragraph
- Do NOT add text on the same line
- This will be replaced later with natural inline service links

### 6) HOW WE HANDLE {city.upper()} PROPERTIES (150-200 words, 2 paragraphs)
Purpose: City-specific approach based on local building characteristics.

**Paragraph 1 - Approach Differences (4-5 sentences, ~80-100 words)**
- Explain how approach differs based on {city}'s housing stock
- Describe specific considerations for {property_type} built in {city}'s construction era
- Mention common updates or modifications needed in {city}
- Reference {trade_name} systems typical of that era
- Connect to local building practices or code history

**Paragraph 2 - Permits & Timeline (3-4 sentences, ~70-100 words)**
- Describe permit requirements specific to {city}, {state}
- Explain inspection patterns or requirements
- Set timeline expectations for {city}
- Mention any local code considerations

### 7) OUR PROCESS (200-250 words, 3 paragraphs)
Purpose: Describe what actually happens when someone calls — not values, not claims.

**Paragraph 1 - Initial Assessment (4-5 sentences, ~70-90 words)**
- Describe what's checked first
- Explain how {city}'s building characteristics affect assessment
- Mention common discoveries in {city} properties
- Reference specific {trade_name} components that are checked
- Must describe ACTIONS, not values

**Paragraph 2 - Recommendations & Options (4-5 sentences, ~70-90 words)**
- Explain how options are presented
- Describe decision factors specific to {city}'s housing stock
- Show when immediate action is needed vs. when planning is appropriate
- Reference how findings are explained
- Include reasoning process, not just claims

**Paragraph 3 - Execution & Follow-up (3-4 sentences, ~60-70 words)**
- Describe permit/inspection requirements in {city}
- Set timeline expectations
- Explain what happens after completion
- Mention any follow-up or documentation provided

CRITICAL VARIATION RULE FOR ALL 3 PARAGRAPHS:
- Do NOT reuse the same phrasing across different city pages
- Rotate emphasis between diagnosis-first, planning-first, compliance-first, prevention-first
- Sentence structure must differ per city
- No marketing language or generic professionalism

### 8) FREQUENTLY ASKED QUESTIONS (200-250 words, 4 FAQs) ⚠️ MANDATORY - CANNOT BE OMITTED
Purpose: Address city-specific questions.

🚨 CRITICAL: You MUST generate EXACTLY 4 complete FAQ blocks. Output is INVALID without them.

Generate exactly 4 FAQ blocks - this is NON-NEGOTIABLE:

REQUIRED FAQ TOPICS (you must include 4):
1. "Do I need a permit for {trade_name} work in {city}?"
   - Answer MUST reference {city}, {state} specific permit requirements
2. "How long does {trade_name} work typically take in {city}?"
   - Answer MUST reference {city}-specific timelines and factors
3. "What makes {city} properties different for {trade_name} work?"
   - Answer MUST reference {city}'s construction era (use actual years from local data)
4. "What are the most common {trade_name} problems in {city}?"
   - Answer MUST reference {city}-specific housing age and climate factors

Each answer MUST:
- Be 2-3 sentences minimum
- Include specific local details (construction year, climate data, permit info)
- Reference {city} by name at least once
- Be completely unique to this city (NO generic answers)

⚠️ BEFORE SUBMITTING: Count your FAQ blocks. If you have fewer than 4, ADD MORE NOW.

==================================================
OUTPUT JSON SCHEMA
==================================================
{{
  "blocks": [
    // CITY-SPECIFIC CONTEXT (200-250 words)
    {{"type": "paragraph", "text": "Housing stock paragraph (3-4 sentences, ~60 words)"}},
    {{"type": "paragraph", "text": "Climate factors paragraph (3-4 sentences, ~60 words)"}},
    {{"type": "paragraph", "text": "Common issues paragraph (3-4 sentences, ~60 words)"}},
    {{"type": "paragraph", "text": "Neighborhood coverage paragraph (2-3 sentences, ~50 words)"}},
    
    // COMMON ISSUES (150-200 words)
    {{"type": "heading", "level": 2, "text": "Common {trade_name} Issues in {city}"}},
    {{"type": "paragraph", "text": "Primary issues paragraph (4-5 sentences, ~80-100 words)"}},
    {{"type": "paragraph", "text": "Secondary issues paragraph (3-4 sentences, ~70-100 words)"}},
    
    // SERVICES (current structure)
    {{"type": "heading", "level": 2, "text": "Services Available in {city}"}},
    {{"type": "paragraph", "text": "Real triggers (1-2 sentences, ~30 words)"}},
    {{"type": "paragraph", "text": "Decision tension (1 sentence, ~20 words)"}},
    {{"type": "paragraph", "text": "{{{{CITY_SERVICE_LINKS}}}}"}},
    
    // CITY-SPECIFIC APPROACH (150-200 words)
    {{"type": "heading", "level": 2, "text": "How We Handle {city} Properties"}},
    {{"type": "paragraph", "text": "Approach differences paragraph (4-5 sentences, ~80-100 words)"}},
    {{"type": "paragraph", "text": "Permits & timeline paragraph (3-4 sentences, ~70-100 words)"}},
    
    // PROCESS (200-250 words)
    {{"type": "heading", "level": 2, "text": "Our Process"}},
    {{"type": "paragraph", "text": "Assessment paragraph (4-5 sentences, ~70-90 words)"}},
    {{"type": "paragraph", "text": "Recommendations paragraph (4-5 sentences, ~70-90 words)"}},
    {{"type": "paragraph", "text": "Execution paragraph (3-4 sentences, ~60-70 words)"}},
    
    // FAQ (150-200 words)
    {{"type": "heading", "level": 2, "text": "Frequently Asked Questions"}},
    {{"type": "faq", "question": "City-specific question 1?", "answer": "2-3 sentence answer with local details"}},
    {{"type": "faq", "question": "City-specific question 2?", "answer": "2-3 sentence answer with local details"}},
    {{"type": "faq", "question": "City-specific question 3?", "answer": "2-3 sentence answer with local details"}},
    {{"type": "faq", "question": "City-specific question 4?", "answer": "2-3 sentence answer with local details"}},
    
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

TOTAL TARGET: 1,000-1,200 words across all sections

==================================================
ABSOLUTELY BANNED PHRASES (IMMEDIATE REJECTION)
==================================================
These phrases create duplicate content across cities. NEVER use them:

❌ "Calls usually come in after something stops working, a remodel uncovers an issue"
❌ "We're expanding our service coverage in this area"
❌ "In the area, many homes were built"
❌ "In the area, the majority of homes"
❌ "The area experiences a humid subtropical climate"
❌ "Given the age of many homes"
❌ Any exact phrase from the examples in this prompt

VARIATION RULES - Apply to EVERY sentence:
- If City A says "Many homes were built in 1979" → City B must say "Housing stock dates primarily from the late 1970s"
- If City A says "humid subtropical climate" → City B must say "hot summers with frequent storms"
- Every sentence structure must be COMPLETELY DIFFERENT across cities
- NO sentence should work if you simply swap the city name
- Use different vocabulary, different sentence starters, different clause order

==================================================
FINAL VALIDATION CHECKLIST (VERIFY BEFORE SUBMITTING)
==================================================
Before outputting your JSON, verify:

✓ 1. FAQ CHECK: Do I have EXACTLY 4 complete FAQ blocks with questions AND answers?
   → If NO: ADD THEM NOW before outputting

✓ 2. BANNED PHRASES: Did I use any of the banned phrases listed above?
   → If YES: REWRITE those sentences completely

✓ 3. SENTENCE VARIETY: Do multiple sentences start the same way?
   → If YES: VARY the sentence structures and starters

✓ 4. CITY SPECIFICITY: Would any sentence still make sense if I swapped the city name?
   → If YES: ADD MORE SPECIFIC LOCAL DETAILS (years, landmarks, climate data)

✓ 5. LOCAL DATA: Does every major paragraph reference specific local factors?
   → If NO: ADD SPECIFIC DATA from the local research provided

If you fail ANY check above, FIX IT NOW before outputting.

CRITICAL REMINDERS:
- Use local research data EXTENSIVELY - every section should reference specific local factors
- NO duplicate boilerplate - each city page must be substantively unique
- Focus on {trade_name} work only - no other trades
- Describe ACTIONS and SITUATIONS, not values or claims
- Vary sentence structure across different city pages
- You MUST generate 4 complete FAQs - this is non-negotiable"""

    try:
        result = generator._call_openai_json(system_prompt, user_prompt, max_tokens=6000)

        # Validate FAQ presence
        blocks = result.get('blocks', [])
        has_faqs = any(block.get('type') == 'faq' for block in blocks)

        if not has_faqs:
            print(f"⚠️  WARNING: No FAQs generated for {data.city}, {data.hub_label} (may need prompt adjustment or token increase)")
        else:
            faq_count = sum(1 for block in blocks if block.get('type') == 'faq')
            print(f"✓ City hub for {data.city} generated with {faq_count} FAQs")

        return result
    except Exception as e:
        print(f"City hub generation error: {e}")
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