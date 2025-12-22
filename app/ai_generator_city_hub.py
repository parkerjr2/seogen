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

    user_prompt = f"""You are generating a City Hub page for a home-service business.

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

==================================================
ABSOLUTE RULES (NON-NEGOTIABLE)
==================================================
- Write like a real tradesperson explaining work to a homeowner.
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

### 1) INTRO — CITY FACTOR WITH CONSEQUENCE (2–3 sentences)
Purpose: Explain WHY this category matters in THIS city.

Rules:
- Mention {city} exactly ONCE.
- Include exactly ONE city-specific factor:
  (housing age, renovations, inspections, growth, weather exposure).
- Explain ONE real-world consequence of that factor that affects decisions or timing.
- No landmarks, ZIP codes, or nearby city lists.
- No sales language.

BAD (unacceptable):
"Homes vary in age, which can affect service needs."

GOOD STYLE (do NOT copy verbatim):
"When homes were built before modern standards were common, issues tend to surface during upgrades or inspections instead of routine maintenance, which changes how problems are prioritized."

### 2) SERVICES CONTEXT — REAL TRIGGERS (1–2 sentences)
Purpose: Describe what actually prompts calls WITHOUT naming services.

Rules:
- Do NOT name or list services.
- Describe real situations or moments of uncertainty.
- Avoid vague phrases like "many homeowners" or "people often".

GOOD STYLE:
"Calls usually come in after something stops working, a remodel uncovers an issue, or an inspection raises questions that weren't obvious beforehand."

### 3) SERVICE LINKS INSERTION POINT (MANDATORY)
On its OWN LINE, output EXACTLY the following token and nothing else:

{{{{CITY_SERVICE_LINKS}}}}

Rules:
- Do NOT wrap this token in a paragraph.
- Do NOT add text on the same line.
- This will be replaced later with natural inline service links.

### 4) WHY CHOOSE US — REAL PROCESS, NOT VALUES (ONE PARAGRAPH, 4–6 sentences)
Purpose: Explain HOW jobs are actually handled.

This paragraph MUST include ALL THREE:
1) A decision moment (when work is recommended vs deferred)
2) An explanation moment (how findings or options are explained)
3) An expectation-setting moment (timing, permits, inspections, follow-up)

Rules:
- ONE paragraph only.
- No bullets.
- No hype.
- No city name repetition.
- No credentials, reviews, awards, or rankings.
- Must describe real job flow, not abstract principles.

UNACCEPTABLE (DO NOT WRITE LIKE THIS):
"We focus on quality work, clear communication, and customer satisfaction."

ACCEPTABLE STYLE (do NOT copy verbatim):
"Most jobs start with figuring out whether an issue is isolated or part of something bigger. If it's something that can wait, we'll say that. If it's likely to cause trouble later, we explain why and what usually happens if it's ignored. When permits or inspections apply, that's discussed before work begins so expectations are clear."

### 5) CTA — LOW PRESSURE (1–2 sentences)
Purpose: Guide without selling.

Rules:
- Calm, neutral tone.
- No urgency or hype.
- No repetition of city name.

==================================================
OUTPUT JSON SCHEMA
==================================================
{{
  "blocks": [
    {{"type": "paragraph", "text": "2-3 sentence intro with city factor + consequence"}},
    {{"type": "heading", "level": 2, "text": "Services We Offer in {city}, {state}"}},
    {{"type": "paragraph", "text": "1-2 sentence real triggers - NO service names"}},
    {{"type": "paragraph", "text": "{{{{CITY_SERVICE_LINKS}}}}"}},
    {{"type": "heading", "level": 2, "text": "Why Choose Us"}},
    {{"type": "paragraph", "text": "ONE paragraph, 4-6 sentences, real process"}},
    {{"type": "heading", "level": 2, "text": "Frequently Asked Questions"}},
    {{"type": "faq", "question": "What {hub_label.lower()} {trade_name} services do you offer in {city}?", "answer": "Detailed 3-4 sentence answer"}},
    {{"type": "faq", "question": "...", "answer": "..."}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

==================================================
MANDATORY SELF-REWRITE ENFORCEMENT (CRITICAL)
==================================================
You MAY NOT return the first draft.

After generating the page, you MUST review your own output and answer:

- Does this sound like a real contractor speaking out loud?
- Does the intro explain a city factor AND its real consequence?
- Does "Why Choose Us" describe decisions, explanations, and expectations?
- Does any sentence exist only for SEO or to introduce links?
- Could this page be reused for another city unchanged?

If the answer to ANY question is YES (except the first):
→ You MUST rewrite the affected sections.
→ Repeat this review until ALL answers are correct.

DO NOT return output until it passes this enforcement check."""

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
            "text": f"When homes in {city} were built before modern standards were common, issues tend to surface during upgrades or inspections instead of routine maintenance, which changes how problems are prioritized."
        },
        {
            "type": "heading",
            "level": 2,
            "text": f"Services We Offer in {city}, {state}"
        },
        {
            "type": "paragraph",
            "text": "Calls usually come in after something stops working, a remodel uncovers an issue, or an inspection raises questions that weren't obvious beforehand."
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
            "text": "Most jobs start with figuring out whether an issue is isolated or part of something bigger. If it's something that can wait, we'll say that. If it's likely to cause trouble later, we explain why and what usually happens if it's ignored. When permits or inspections apply, that's discussed before work begins so expectations are clear."
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
