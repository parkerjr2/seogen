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
    
    # Build H1 (without business name)
    h1_text = f"{hub_label} {trade_name.title()} Services"
    
    # Build slug programmatically
    slug = data.hub_slug or generator.slugify(hub_label, trade_name)
    
    # Build meta description
    meta_description = f"Professional {hub_label.lower()} {trade_name} services. "
    if data.service_area_label:
        meta_description += f"Serving {data.service_area_label}. "
    meta_description += f"{data.cta_text}."
    
    # Generate content blocks via LLM
    content_json = _call_openai_hub_generation(generator, data, profile)
    
    blocks = content_json.get("blocks", [])
    
    # Prepend H1 and intro paragraph for hero section (WordPress will format as hero)
    # The build_gutenberg_content_from_blocks method expects H1 + paragraph at start for hero
    hero_blocks = [
        {
            "type": "heading",
            "level": 1,
            "text": h1_text
        }
    ]
    
    # If first block is a paragraph, it becomes the hero paragraph
    # Otherwise add a default hero paragraph
    if blocks and blocks[0].get("type") == "paragraph":
        hero_blocks.append(blocks[0])
        blocks = blocks[1:]  # Remove it from main blocks since it's now in hero
    else:
        # Add default hero paragraph
        hero_blocks.append({
            "type": "paragraph",
            "text": f"Professional {hub_label.lower()} {trade_name} services for your property."
        })
    
    # Combine hero blocks with content blocks
    all_blocks = hero_blocks + blocks
    
    # Assemble response
    response = GeneratePageResponse(
        title=title,
        meta_description=meta_description[:160],
        slug=slug,
        blocks=all_blocks
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
1. Opening paragraph (3-4 sentences) - Explain what {hub_label.lower()} {trade_name} services are and why they matter. Use trade-specific vocabulary: {', '.join(vocabulary[:8])}
2. Second paragraph (2-3 sentences) - Describe common scenarios or problems these services solve
3. "Services We Offer" heading (level 2)
4. Paragraph (3-4 sentences) - Introduce the services list and explain the comprehensive nature of offerings
5. "Primary Service Areas" heading (level 2)
6. Paragraph with shortcode: "We provide {hub_label.lower()} {trade_name} services throughout {data.service_area_label or 'the area'}. [seogen_service_hub_links hub_key=\\"{data.hub_key}\\"]"
7. "Frequently Asked Questions" heading (level 2)
8. 6-8 FAQs with detailed answers (3-4 sentences each) - Cover common questions about {hub_label.lower()} {trade_name} services
9. CTA block

Output JSON schema:
{{
  "blocks": [
    {{"type": "paragraph", "text": "3-4 sentence opening paragraph with trade vocabulary"}},
    {{"type": "paragraph", "text": "2-3 sentence paragraph about common scenarios"}},
    {{"type": "heading", "level": 2, "text": "Services We Offer"}},
    {{"type": "paragraph", "text": "3-4 sentence paragraph introducing services"}},
    {{"type": "heading", "level": 2, "text": "Primary Service Areas"}},
    {{"type": "paragraph", "text": "We provide {hub_label.lower()} {trade_name} services throughout {data.service_area_label or 'the area'}. [seogen_service_hub_links hub_key=\\"{data.hub_key}\\"]"}},
    {{"type": "heading", "level": 2, "text": "Frequently Asked Questions"}},
    {{"type": "faq", "question": "What types of {hub_label.lower()} {trade_name} services do you offer?", "answer": "Detailed 3-4 sentence answer with specifics"}},
    {{"type": "faq", "question": "...", "answer": "..."}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

CRITICAL: 
- Write substantial paragraphs (3-4 sentences minimum)
- Use technical trade vocabulary naturally
- Make FAQs detailed and informative (3-4 sentences per answer)
- Include the shortcode token EXACTLY as shown
- Do NOT mention specific cities or neighborhoods"""

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
    vocabulary = profile.get("vocabulary", [])
    
    blocks = [
        {
            "type": "paragraph",
            "text": f"Our {hub_label.lower()} {trade_name} services provide comprehensive solutions for property owners and managers. Whether you need routine maintenance, emergency repairs, or new installations, our experienced team delivers reliable results using industry-standard practices and quality materials."
        },
        {
            "type": "paragraph",
            "text": f"We understand that {hub_label.lower()} properties have unique requirements. Our services are designed to address common challenges while ensuring safety, compliance, and long-term performance."
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Services We Offer"
        },
        {
            "type": "paragraph",
            "text": f"Our comprehensive {hub_label.lower()} {trade_name} services cover everything from basic maintenance to complex installations. We work with property owners, managers, and contractors to deliver solutions that meet specific needs and budgets."
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Primary Service Areas"
        },
        {
            "type": "paragraph",
            "text": f"We provide {hub_label.lower()} {trade_name} services throughout {data.service_area_label or 'the area'}. [seogen_service_hub_links hub_key=\"{data.hub_key}\"]"
        },
        {
            "type": "heading",
            "level": 2,
            "text": "Frequently Asked Questions"
        },
        {
            "type": "faq",
            "question": f"What types of {hub_label.lower()} {trade_name} services do you provide?",
            "answer": f"We offer a complete range of {hub_label.lower()} {trade_name} services including routine maintenance, repairs, installations, and emergency services. Our team has experience with both simple and complex projects, ensuring quality results regardless of scope."
        },
        {
            "type": "faq",
            "question": f"How quickly can you respond to {hub_label.lower()} service requests?",
            "answer": f"Response times vary based on the nature of the request. For routine {hub_label.lower()} services, we typically schedule within a few days. Emergency situations receive priority response, often within hours depending on availability and location."
        },
        {
            "type": "faq",
            "question": "Do you provide estimates before starting work?",
            "answer": f"Yes, we provide detailed estimates for all {hub_label.lower()} {trade_name} projects. Our estimates include scope of work, materials, labor, and timeline. We believe in transparent pricing with no hidden fees or surprise charges."
        },
        {
            "type": "faq",
            "question": "Are your technicians licensed and insured?",
            "answer": f"All our {trade_name} technicians are properly licensed, insured, and experienced in {hub_label.lower()} applications. We maintain current certifications and follow industry best practices to ensure quality and safety on every project."
        },
    ]
    
    if data.phone and data.cta_text:
        blocks.append({
            "type": "cta",
            "text": data.cta_text,
            "phone": data.phone
        })
    
    return {"blocks": blocks}
