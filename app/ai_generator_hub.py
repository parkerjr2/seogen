"""
Service Hub page generation for AI content generator.
This module extends the AI generator with service hub capabilities.
"""

from app.models import GeneratePageResponse, PageData, HeadingBlock, ParagraphBlock, FAQBlock, CTABlock
from app.vertical_profiles import get_vertical_profile, get_trade_name


def generate_service_hub_content(generator, data: PageData) -> GeneratePageResponse:
    """
    Generate service hub page content (no city-specific content).
    
    Args:
        generator: The AIContentGenerator instance
        data: Page generation parameters with hub information
        
    Returns:
        Complete validated hub page content
    """
    vertical = data.vertical or "other"
    profile = get_vertical_profile(vertical)
    trade_name = profile["trade_name"]
    
    # Build title programmatically
    hub_label = data.hub_label or "Services"
    title = f"{hub_label} {trade_name.title()} Services"
    if data.business_name:
        title += f" | {data.business_name}"
    
    # Build slug programmatically
    slug = data.hub_slug or generator.slugify(hub_label, trade_name)
    
    # Build meta description
    meta_description = f"Professional {hub_label.lower()} {trade_name} services. "
    if data.service_area_label:
        meta_description += f"Serving {data.service_area_label}. "
    meta_description += f"{data.cta_text}."
    
    # Generate content blocks via LLM
    content_json = _call_openai_hub_generation(generator, data, profile)
    
    # Assemble response
    response = GeneratePageResponse(
        title=title,
        meta_description=meta_description[:160],
        slug=slug,
        blocks=content_json.get("blocks", [])
    )
    
    return response


def _call_openai_hub_generation(generator, data: PageData, profile: dict) -> dict:
    """Call OpenAI to generate hub page content blocks."""
    
    trade_name = profile["trade_name"]
    vocabulary = profile["vocabulary"]
    hub_label = data.hub_label or "Services"
    
    # Build services list
    services_list = ""
    if data.services_for_hub:
        services_list = "\n".join([f"- {s.get('name', '')}" for s in data.services_for_hub[:20]])
    
    system_prompt = f"""You are an expert {trade_name} content writer creating a service hub page.

CRITICAL RULES:
1. Do NOT mention any specific city, town, or neighborhood
2. Keep content general and applicable to the entire service area
3. Use trade-specific vocabulary: {', '.join(vocabulary[:10])}
4. Be professional and informative, not salesy
5. Output ONLY valid JSON matching the schema below

FORBIDDEN:
- Never mention specific cities or locations
- No marketing fluff like "top-notch", "premier", "best-in-class"
- No meta-language like "this page", "this article"
"""

    user_prompt = f"""Generate content blocks for a {hub_label.lower()} {trade_name} service hub page.

Hub Category: {hub_label}
Business Type: {trade_name}
Business Name: {data.business_name or 'Our Company'}
Phone: {data.phone or ''}
Service Area: {data.service_area_label or 'your area'}
CTA Text: {data.cta_text}

Services Offered:
{services_list}

Generate these blocks in order:
1. Intro paragraph (2-3 sentences about {hub_label.lower()} {trade_name} services in general)
2. "Services We Offer" heading (level 2)
3. Paragraph introducing the services list
4. "Primary Service Areas" heading (level 2)
5. Short paragraph with this EXACT shortcode token: [seogen_service_hub_links hub_key="{data.hub_key}"]
6. 5-8 FAQs relevant to {hub_label.lower()} {trade_name} services
7. CTA block with phone and CTA text

Output JSON schema:
{{
  "blocks": [
    {{"type": "paragraph", "text": "..."}},
    {{"type": "heading", "level": 2, "text": "Services We Offer"}},
    {{"type": "paragraph", "text": "..."}},
    {{"type": "heading", "level": 2, "text": "Primary Service Areas"}},
    {{"type": "paragraph", "text": "We serve communities throughout {data.service_area_label or 'the area'}. [seogen_service_hub_links hub_key=\\"{data.hub_key}\\"]"}},
    {{"type": "faq", "question": "...", "answer": "..."}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

IMPORTANT: Include the shortcode token EXACTLY as shown in the Primary Service Areas paragraph."""

    try:
        result = generator._call_openai_json(system_prompt, user_prompt, max_tokens=3000)
        return result
    except Exception as e:
        print(f"Hub generation error: {e}")
        # Return fallback content
        return _generate_fallback_hub_content(data, profile)


def _generate_fallback_hub_content(data: PageData, profile: dict) -> dict:
    """Generate fallback hub content if AI generation fails."""
    
    trade_name = profile["trade_name"]
    hub_label = data.hub_label or "Services"
    
    blocks = [
        {
            "type": "paragraph",
            "text": f"Welcome to our {hub_label.lower()} {trade_name} services. We provide professional solutions for all your {trade_name} needs."
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Services We Offer"
        },
        {
            "type": "paragraph",
            "text": f"Our team specializes in comprehensive {hub_label.lower()} {trade_name} services designed to meet your specific requirements."
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Primary Service Areas"
        },
        {
            "type": "paragraph",
            "text": f"We serve communities throughout {data.service_area_label or 'the area'}. [seogen_service_hub_links hub_key=\"{data.hub_key}\"]"
        },
        {
            "type": "faq",
            "question": f"What {hub_label.lower()} {trade_name} services do you offer?",
            "answer": f"We offer a full range of {hub_label.lower()} {trade_name} services to meet your needs."
        },
        {
            "type": "faq",
            "question": "How can I get started?",
            "answer": f"Contact us today to discuss your {trade_name} needs and get a free estimate."
        },
    ]
    
    if data.phone and data.cta_text:
        blocks.append({
            "type": "cta",
            "text": data.cta_text,
            "phone": data.phone
        })
    
    return {"blocks": blocks}
