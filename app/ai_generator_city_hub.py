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

    # Determine target audience based on hub label
    is_commercial = hub_label and 'commercial' in hub_label.lower()
    target_audience = "business owner" if is_commercial else "homeowner"
    property_type = "commercial properties" if is_commercial else "homes"
    business_type = f"{hub_label.lower()} {trade_name}" if hub_label else trade_name
    
    user_prompt = f"""You are generating a City Hub page for a {business_type} service business.

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

### 1) INTRO — CITY FACTOR CAUSES REAL CONSEQUENCE (2–3 sentences)
Purpose: Show WHY this type of work shows up the way it does in THIS city.

Rules:
- Mention {city} exactly ONCE.
- Include exactly ONE city factor: building age, inspections, growth, renovations, or weather.
- Show ONE practical consequence that affects:
  * what gets discovered,
  * when work is done,
  * or why issues surface.
- Do NOT write anything that would still apply unchanged to another city.
- No landmarks, ZIP codes, or nearby city lists.
- No sales language.
- Reference {property_type}, not generic "properties"

UNACCEPTABLE:
"Properties vary in age, which can affect service needs."

ACCEPTABLE STYLE (do NOT copy verbatim):
"Because many {property_type} in {city} were built before modern standards were common, issues are often uncovered during inspections or remodels rather than routine maintenance, which changes how problems are prioritized."

### 2) SERVICES CONTEXT — REAL TRIGGERS (1–2 sentences)
Purpose: Describe what actually prompts calls WITHOUT naming services.

Rules:
- Do NOT name or list services.
- Describe real situations or moments of uncertainty.
- Avoid vague phrases like "many {target_audience}s" or "people often".
- Use {target_audience} context appropriately.

GOOD STYLE:
"Calls usually come in after something stops working, a remodel uncovers an issue, or an inspection raises questions that weren't obvious beforehand."

### 3) DECISION TENSION — WHY LOOK DEEPER (ONE sentence)
Purpose: Explain WHY someone would need to explore service pages.

Rules:
- ONE sentence only
- No service names
- Describe a real moment of uncertainty or decision
- Must feel spoken, not written

GOOD PATTERNS (rotate, do NOT reuse verbatim):
- "The tricky part is figuring out whether what you're seeing is a one-off issue or part of something bigger."
- "What looks like a small problem can sometimes point to a larger update, which is why the details matter."
- "Once you know what's happening, the next step is understanding which type of work actually applies."

BAD PATTERNS:
- "Below are our services"
- "Explore our services"
- "We offer a range of services"

### 4) SERVICE LINKS INSERTION POINT (MANDATORY)
On its OWN LINE, output EXACTLY the following token and nothing else:

{{{{CITY_SERVICE_LINKS}}}}

Rules:
- Do NOT wrap this token in a paragraph.
- Do NOT add text on the same line.
- This will be replaced later with natural inline service links.

### 5) WHY CHOOSE US — EXPERIENCED, NOT GENERIC (ONE PARAGRAPH, 4–6 sentences)
Purpose: Describe what actually happens when someone calls — not values, not claims.

This paragraph MUST include ALL FOUR:
1) A discovery moment (what is checked or figured out first)
2) A decision moment (when something is recommended vs deferred)
3) An explanation moment (how options or findings are explained)
4) An expectation moment (timing, permits, inspections, or follow-up)

CRITICAL VARIATION RULE:
- Do NOT reuse the same phrasing across pages
- Rotate emphasis between:
  * diagnosis-first ("When someone calls, the first step is figuring out...")
  * planning-first ("Before recommending anything, we look at...")
  * compliance-first ("If permits or inspections apply, that's discussed early...")
  * prevention-first ("Sometimes what looks urgent can wait, and what looks minor needs attention...")
- Sentence structure must differ per city

Rules:
- ONE paragraph only.
- 4–6 sentences.
- No bullets.
- No city name.
- No marketing language.
- No generic professionalism ("quality", "trusted", "customer-focused").
- Must describe ACTIONS, not values.
- If ANY of the 4 moments are missing, the output is INVALID.

UNACCEPTABLE:
"We focus on clear communication and doing the job right."

GOLD-STANDARD EXAMPLE (STYLE ONLY — DO NOT COPY):
"When someone calls, the first step is figuring out whether the issue is isolated or part of a larger update. Sometimes that means opening things up or testing further before recommending anything. If it's something that can wait, that's said plainly. If it's likely to create problems down the line, the reasons are explained along with options. When permits or inspections are involved, that's discussed early so expectations are clear before work begins."

Your output must match the realism and specificity of this example,
but must NOT reuse its wording or structure.

### 6) CTA — LOW PRESSURE (1–2 sentences)
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
    {{"type": "heading", "level": 2, "text": "Services We Offer Locally"}},
    {{"type": "paragraph", "text": "1-2 sentence real triggers - NO service names"}},
    {{"type": "paragraph", "text": "ONE sentence decision tension - WHY look deeper"}},
    {{"type": "paragraph", "text": "{{{{CITY_SERVICE_LINKS}}}}"}},
    {{"type": "heading", "level": 2, "text": "Why Choose Us"}},
    {{"type": "paragraph", "text": "ONE paragraph, 4-6 sentences, real process with natural variation patterns"}},
    {{"type": "heading", "level": 2, "text": "Frequently Asked Questions"}},
    {{"type": "faq", "question": "What {hub_label.lower()} {trade_name} services do you offer in {city}?", "answer": "Detailed 3-4 sentence answer"}},
    {{"type": "faq", "question": "...", "answer": "..."}},
    {{"type": "cta", "text": "{data.cta_text}", "phone": "{data.phone or ''}"}}
  ]
}}

==================================================
HARD SELF-REVIEW ENFORCEMENT (DO NOT SKIP)
==================================================
You may NOT return the first draft.

Before finalizing, review your output and ask:
- Does this sound like a real tradesperson describing real jobs?
- Does the service-links transition create a reason to click?
- Does "Why Choose Us" describe actions, not values?
- Could this paragraph be reused unchanged on another city page?

If the answer to ANY question is YES (except the first):
→ Rewrite the affected section.
→ Repeat until ALL answers are NO.

Do NOT return output until this enforcement passes.

CRITICAL CONTEXT:
City Hub pages exist to answer:
"Why does this type of work show up the way it does in this city,
and how does this company actually handle those situations?"

If the output sounds like advice, values, or professionalism, it has FAILED."""

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
            "text": f"Because many homes in {city} were built before modern standards were common, issues are often uncovered during inspections or remodels rather than routine maintenance, which changes how problems are prioritized."
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
            "text": "The tricky part is figuring out whether what you're seeing is a one-off issue or part of something bigger."
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
