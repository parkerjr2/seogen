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

    user_prompt = f"""Generate content blocks for a {hub_label.lower()} {trade_name} city hub page.

Hub Category: {hub_label}
City: {city}, {state}
Business Type: {trade_name}
Business Name: {data.business_name or 'Our Company'}
Phone: {data.phone or ''}
Service Area: {data.service_area_label or city}
CTA Text: {data.cta_text}

Generate these blocks in EXACT order:

1. INTRO PARAGRAPH (2-3 sentences):
   - Mention {city} ONCE in the first sentence
   - Include exactly ONE general city factor: older homes, renovations, mixed housing stock, growth, or storms
   - NO landmarks, NO "locally", NO "local property owners", NO "serving the local area"
   - Use trade vocabulary: {', '.join(vocabulary[:8])}
   - Example: "Residential electrical work in {city}, {state} covers everything from panel upgrades to outlet repairs. Many homes here were built decades ago, so safety checks and code updates are common requests."

2. SERVICES SECTION - HEADING (level 2):
   - Text: "Services We Offer in {city}, {state}"

3. SERVICES SECTION - INTRO PARAGRAPH (1-2 sentences):
   - Brief, general intro about service range
   - DO NOT list or name any specific services
   - Example: "Whether you need a quick repair or a larger project, we handle the full range of {hub_label.lower()} {trade_name} work."

4. SERVICES SECTION - BRIDGE SENTENCE (1 sentence):
   - Natural lead-in to service links
   - Examples: "If you're not sure where to start, the pages below explain common options and what to expect." OR "The guides below walk through typical projects, timelines, and when to call a pro."

5. PLACEHOLDER TOKEN (EXACT TEXT, standalone paragraph):
   - Output EXACTLY: {{{{CITY_SERVICE_LINKS}}}}
   - This must be its own paragraph block, not inside another paragraph
   - Do NOT add any other text on this line

6. WHY CHOOSE US - HEADING (level 2):
   - Text: "Why Choose Us"
   - NO city name in this heading

7. WHY CHOOSE US - PARAGRAPH (ONE paragraph, 4-6 sentences):
   - Must sound like a real contractor explaining how they work
   - Talk about: communication, showing up, diagnosing, explaining options, code/safety, cleanup, documentation
   - Trade-neutral (works for any vertical)
   - NO bullets, NO lists
   - NO fluff words: "top-rated", "trusted", "best", "locally"
   - Mention {city} ZERO or ONE time maximum (prefer zero)
   - Example: "When you call, we start by asking a few questions and checking the situation in person if needed. We'll explain what we found in plain language, walk through your options, and tell you what's worth doing now versus later. If permits or code requirements apply, we point that out up front—no surprises after work starts. We keep the job site clean, communicate about timing, and make sure you know what changed when we're done."

8. FAQ - HEADING (level 2):
   - Text: "Frequently Asked Questions"

9. FAQ BLOCKS (5-8 questions):
   - Detailed answers (3-4 sentences each)
   - Cover common questions about {hub_label.lower()} {trade_name} services in {city}, {state}

10. CTA BLOCK:
   - Use provided CTA text and phone

Output JSON schema:
{{
  "blocks": [
    {{"type": "paragraph", "text": "2-3 sentence intro with city factor"}},
    {{"type": "heading", "level": 2, "text": "Services We Offer in {city}, {state}"}},
    {{"type": "paragraph", "text": "1-2 sentence general intro - NO service names"}},
    {{"type": "paragraph", "text": "One bridge sentence leading to service links"}},
    {{"type": "paragraph", "text": "{{{{CITY_SERVICE_LINKS}}}}"}},
    {{"type": "heading", "level": 2, "text": "Why Choose Us"}},
    {{"type": "paragraph", "text": "ONE paragraph, 4-6 sentences, sounds like real contractor"}},
    {{"type": "heading", "level": 2, "text": "Frequently Asked Questions"}},
    {{"type": "faq", "question": "What {hub_label.lower()} {trade_name} services do you offer in {city}?", "answer": "Detailed 3-4 sentence answer"}},
    {{"type": "faq", "question": "...", "answer": "..."}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

CRITICAL RULES:
- DO NOT list or name individual services anywhere
- DO NOT enumerate services (e.g., "including X, Y, and Z")
- DO NOT create any HTML lists (<ul>, <ol>, bullets, numbered lists)
- DO NOT create headings like "Services Available", "Services Locally"
- The {{{{CITY_SERVICE_LINKS}}}} token will be replaced with actual service links
- Output EXACTLY the blocks specified above, nothing more
- Why Choose Us must be ONE paragraph (not bullets, not multiple paragraphs)
- Total city mentions: 2-3 times maximum across entire page
- Never use banned phrases (see system prompt)

QUALITY RULES:
- Write like a real contractor, not marketing copy
- Use technical trade vocabulary naturally
- Make FAQs detailed and informative (3-4 sentences per answer)
- Be professional and direct, not salesy"""

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
            "text": f"{hub_label} {trade_name} work in {city}, {state} covers everything from routine repairs to larger projects. Many properties here have a mix of older and newer construction, so code compliance and safety checks come up often."
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"Services We Offer in {city}, {state}"
        },
        {
            "type": "paragraph",
            "text": f"Whether you need a quick repair or a larger project, we handle the full range of {hub_label.lower()} {trade_name} work."
        },
        {
            "type": "paragraph",
            "text": "If you're not sure where to start, the pages below explain common options and what to expect."
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
            "text": "When you call, we start by asking a few questions and checking the situation in person if needed. We'll explain what we found in plain language, walk through your options, and tell you what's worth doing now versus later. If permits or code requirements apply, we point that out up front—no surprises after work starts. We keep the job site clean, communicate about timing, and make sure you know what changed when we're done."
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
