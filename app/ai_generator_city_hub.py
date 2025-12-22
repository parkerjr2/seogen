"""
City Hub page generation for AI content generator.
This module generates city-localized hub pages (e.g., "Electrician in Tulsa, OK").
"""

from app.models import GeneratePageResponse, PageData
from app.vertical_profiles import get_vertical_profile, get_trade_name


def generate_city_hub_content(generator, data: PageData) -> GeneratePageResponse:
    """
    Generate city hub page content (city-localized hub page).
    
    Args:
        generator: The AIContentGenerator instance
        data: Page generation parameters with hub + city information
        
    Returns:
        Complete validated city hub page content
    """
    vertical = data.vertical or "other"
    profile = get_vertical_profile(vertical)
    trade_name = profile["trade_name"]
    
    # Build title programmatically
    hub_label = data.hub_label or "Services"
    city = data.city or "Your City"
    state = data.state or "ST"
    
    # Title: "Residential Electrician in Tulsa, OK | Business Name"
    title = f"{hub_label} {trade_name.title()} in {city}, {state}"
    if data.business_name:
        title += f" | {data.business_name}"
    
    # Build H1 (without business name)
    h1_text = f"{hub_label} {trade_name.title()} in {city}, {state}"
    
    # Build slug programmatically (city-slug, not hub-slug)
    city_slug = data.city_slug or generator.slugify("", f"{city}-{state}")
    
    # Build meta description
    meta_description = f"Professional {hub_label.lower()} {trade_name} services in {city}, {state}. "
    if data.service_area_label:
        meta_description += f"Serving {data.service_area_label}. "
    meta_description += f"{data.cta_text}."
    
    # Generate content blocks via LLM
    content_json = _call_openai_city_hub_generation(generator, data, profile)
    
    blocks = content_json.get("blocks", [])
    
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
        blocks=all_blocks
    )
    
    return response


def _call_openai_city_hub_generation(generator, data: PageData, profile: dict) -> dict:
    """Call OpenAI to generate city hub page content blocks."""
    
    trade_name = profile["trade_name"]
    vocabulary = profile.get("vocabulary", [])
    hub_label = data.hub_label or "Services"
    city = data.city or "Your City"
    state = data.state or "ST"
    
    # Note: We do NOT pass service names to the AI to avoid enumeration
    # The shortcode will handle service discovery and display
    
    system_prompt = f"""You are an expert {trade_name} content writer creating a city hub page.

CRITICAL RULES:
1. Mention {city}, {state} naturally throughout the content
2. Do NOT mention any other cities or towns
3. Use trade-specific vocabulary: {', '.join(vocabulary[:10])}
4. Be professional and informative, not salesy
5. Output ONLY valid JSON matching the schema below

FORBIDDEN:
- Never mention cities other than {city}
- No marketing fluff like "top-notch", "premier", "best-in-class"
- No meta-language like "this page", "this article"
"""

    user_prompt = f"""Generate content blocks for a {hub_label.lower()} {trade_name} city hub page.

Hub Category: {hub_label}
City: {city}, {state}
Business Type: {trade_name}
Business Name: {data.business_name or 'Our Company'}
Phone: {data.phone or ''}
Service Area: {data.service_area_label or city}
CTA Text: {data.cta_text}

Generate these blocks in order:
1. Opening paragraph (3-4 sentences) - Explain what {hub_label.lower()} {trade_name} services are in {city}, {state} and why they matter. Use trade-specific vocabulary: {', '.join(vocabulary[:8])}
2. Second paragraph (2-3 sentences) - Describe common scenarios or problems in {city} that these services solve
3. "Services We Offer in {city}, {state}" heading (level 2)
4. ONE short paragraph (2-3 sentences) - Brief intro about the range of services available, NO enumeration of specific service names
5. Bridge sentence paragraph: A single natural sentence introducing the service links below (e.g., "Explore our most requested services in the area below." or similar)
6. "Why Choose Us" heading (level 2) - NO city name in this heading
7. REQUIRED: Either 3-4 bullet points OR 2 concise paragraphs explaining benefits. Content must be:
   - Trade-neutral (works for any home service)
   - Natural, conversational tone - write like a professional tradesperson, not marketing copy
   - Complete sentences or substantial phrases (8-15 words each)
   - NO generic marketing fluff ("we are the best", "top-rated", "#1 choice")
   - NO service enumeration
   - May reference local factors (response times, familiarity with local codes, property types, weather patterns)
   Example bullet points:
   * "We're familiar with the building codes and common issues in {city} properties"
   * "Straightforward pricing and clear explanations before we start any work"
   * "Licensed, insured, and focused on doing the job right the first time"
   * "We respond quickly and show up when we say we will"
8. "Frequently Asked Questions" heading (level 2)
9. 5-8 FAQs with detailed answers (3-4 sentences each) - Cover common questions about {hub_label.lower()} {trade_name} services in {city}, {state}
10. CTA block

Output JSON schema:
{{
  "blocks": [
    {{"type": "paragraph", "text": "3-4 sentence opening paragraph mentioning {city}, {state}"}},
    {{"type": "paragraph", "text": "2-3 sentence paragraph about common scenarios in {city}"}},
    {{"type": "heading", "level": 2, "text": "Services We Offer in {city}, {state}"}},
    {{"type": "paragraph", "text": "2-3 sentence brief intro about service range - NO specific service names"}},
    {{"type": "paragraph", "text": "One natural bridge sentence like 'Explore our most requested services in the area below.' or similar"}},
    {{"type": "heading", "level": 2, "text": "Why Choose Us"}},
    {{"type": "list", "items": ["We're familiar with the building codes and common issues in {city} properties", "Straightforward pricing and clear explanations before we start any work", "Licensed, insured, and focused on doing the job right the first time", "We respond quickly and show up when we say we will"]}} OR {{"type": "paragraph", "text": "2 concise paragraphs"}},
    {{"type": "heading", "level": 2, "text": "Frequently Asked Questions"}},
    {{"type": "faq", "question": "What {hub_label.lower()} {trade_name} services do you offer in {city}?", "answer": "Detailed 3-4 sentence answer"}},
    {{"type": "faq", "question": "...", "answer": "..."}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

CRITICAL ANTI-DUPLICATION RULES:
- DO NOT list or name individual services in any paragraph
- DO NOT enumerate services (e.g., "including X, Y, and Z")
- DO NOT create bullet lists of services
- DO NOT create multiple service-related headings
- DO NOT create "Services Available" or "Services Locally" headings
- The service discovery will be handled automatically by the system
- ONLY output the 10 blocks specified above, nothing more
- Keep the bridge sentence natural and simple

QUALITY RULES:
- Write substantial paragraphs (2-4 sentences)
- Use technical trade vocabulary naturally
- Make FAQs detailed and informative (3-4 sentences per answer)
- Mention {city}, {state} naturally but do NOT mention other cities
- Be professional and informative, not salesy"""

    try:
        result = generator._call_openai_json(system_prompt, user_prompt, max_tokens=3000)
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
            "text": f"Our {hub_label.lower()} {trade_name} services in {city}, {state} provide comprehensive solutions for property owners and managers. Whether you need routine maintenance, emergency repairs, or new installations, our experienced team delivers reliable results."
        },
        {
            "type": "paragraph",
            "text": f"We understand the unique needs of properties in {city}. Our services are designed to address common challenges while ensuring safety, compliance, and long-term performance."
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"Services We Offer in {city}, {state}"
        },
        {
            "type": "paragraph",
            "text": f"Our {hub_label.lower()} {trade_name} services address a wide range of property needs. From routine work to specialized projects, we provide reliable solutions for residential and commercial clients."
        },
        {
            "type": "paragraph",
            "text": "Explore our most requested services in the area below."
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Why Choose Us"
        },
        {
            "type": "list",
            "items": [
                f"We're familiar with the building codes and common issues in {city} properties",
                "Straightforward pricing and clear explanations before we start any work",
                "Licensed, insured, and focused on doing the job right the first time",
                "We respond quickly and show up when we say we will"
            ]
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Frequently Asked Questions"
        },
        {
            "type": "faq",
            "question": f"What {hub_label.lower()} {trade_name} services do you offer in {city}?",
            "answer": f"We offer a complete range of {hub_label.lower()} {trade_name} services in {city}, {state}. Our team has experience with both routine maintenance and complex projects, ensuring quality results for every job."
        },
        {
            "type": "faq",
            "question": f"How quickly can you respond in {city}?",
            "answer": f"Response times in {city} vary based on the nature of the request. For routine services, we typically schedule within a few days. Emergency situations receive priority response, often within hours."
        },
        {
            "type": "faq",
            "question": "Do you provide estimates?",
            "answer": f"Yes, we provide detailed estimates for all projects in {city}. Our estimates include scope of work, materials, labor, and timeline with transparent pricing."
        },
    ]
    
    if data.phone and data.cta_text:
        blocks.append({
            "type": "cta",
            "text": data.cta_text,
            "phone": data.phone
        })
    
    return {"blocks": blocks}
