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
    
    # Build services list
    services_list = ""
    if data.services_for_hub:
        services_list = "\n".join([f"- {s.get('name', '')}" for s in data.services_for_hub[:20]])
    
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

Services Offered in {city}:
{services_list}

Generate these blocks in order:
1. Opening paragraph (3-4 sentences) - Explain what {hub_label.lower()} {trade_name} services are in {city}, {state} and why they matter. Use trade-specific vocabulary: {', '.join(vocabulary[:8])}
2. Second paragraph (2-3 sentences) - Describe common scenarios or problems in {city} that these services solve
3. "Services We Offer in {city}" heading (level 2)
4. Paragraph (3-4 sentences) - Introduce the services list and explain the comprehensive nature of offerings in {city}
5. Paragraph with shortcode: "We provide {hub_label.lower()} {trade_name} services throughout {city}, {state}. [seogen_city_hub_links hub_key=\\"{data.hub_key}\\" city_slug=\\"{data.city_slug}\\"]"
6. "Why Choose Us in {city}" heading (level 2)
7. Paragraph (3-4 sentences) - Explain benefits of choosing local {trade_name} services in {city}
8. "Frequently Asked Questions" heading (level 2)
9. 5-8 FAQs with detailed answers (3-4 sentences each) - Cover common questions about {hub_label.lower()} {trade_name} services in {city}, {state}
10. CTA block

Output JSON schema:
{{
  "blocks": [
    {{"type": "paragraph", "text": "3-4 sentence opening paragraph mentioning {city}, {state}"}},
    {{"type": "paragraph", "text": "2-3 sentence paragraph about common scenarios in {city}"}},
    {{"type": "heading", "level": 2, "text": "Services We Offer in {city}"}},
    {{"type": "paragraph", "text": "3-4 sentence paragraph introducing services in {city}"}},
    {{"type": "paragraph", "text": "We provide {hub_label.lower()} {trade_name} services throughout {city}, {state}. [seogen_city_hub_links hub_key=\\"{data.hub_key}\\" city_slug=\\"{data.city_slug}\\"]"}},
    {{"type": "heading", "level": 2, "text": "Why Choose Us in {city}"}},
    {{"type": "paragraph", "text": "3-4 sentence paragraph about local benefits"}},
    {{"type": "heading", "level": 2, "text": "Frequently Asked Questions"}},
    {{"type": "faq", "question": "What {hub_label.lower()} {trade_name} services do you offer in {city}?", "answer": "Detailed 3-4 sentence answer"}},
    {{"type": "faq", "question": "...", "answer": "..."}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

CRITICAL: 
- Write substantial paragraphs (3-4 sentences minimum)
- Use technical trade vocabulary naturally
- Make FAQs detailed and informative (3-4 sentences per answer)
- Include the shortcode token EXACTLY as shown
- Mention {city}, {state} naturally but do NOT mention other cities
- DO NOT add any extra headings or sections beyond what is specified above
- DO NOT create "Services Available Locally" or "Services Available in {city}" headings
- DO NOT create service lists - the shortcode will handle that automatically
- ONLY output the 10 blocks specified above, nothing more"""

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
            "text": f"Services We Offer in {city}"
        },
        {
            "type": "paragraph",
            "text": f"Our comprehensive {hub_label.lower()} {trade_name} services in {city} cover everything from basic maintenance to complex installations. We work with property owners, managers, and contractors throughout {city}, {state}."
        },
        {
            "type": "paragraph",
            "text": f"We provide {hub_label.lower()} {trade_name} services throughout {city}, {state}. [seogen_city_hub_links hub_key=\"{data.hub_key}\" city_slug=\"{data.city_slug}\"]"
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"Why Choose Us in {city}"
        },
        {
            "type": "paragraph",
            "text": f"As a local {trade_name} service provider in {city}, we understand the specific needs and challenges of properties in the area. Our team is familiar with local building codes and can respond quickly to service requests throughout {city}, {state}."
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Frequently Asked Questions"
        },
        {
            "type": "faq",
            "question": f"What {hub_label.lower()} {trade_name} services do you offer in {city}?",
            "answer": f"We offer a complete range of {hub_label.lower()} {trade_name} services in {city}, {state} including routine maintenance, repairs, installations, and emergency services. Our team has experience with both simple and complex projects."
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
