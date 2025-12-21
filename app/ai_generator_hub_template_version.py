"""
Service Hub Page Generation with AI-Generated Unique Content

Combines deterministic variant selection (for section ordering) with AI-generated
unique content to create hub pages that are both structurally varied and 
substantively unique.

- 3 deterministic variants control section order
- AI generates unique content for each hub
- Hub-specific prompts ensure residential/commercial/emergency differentiation
"""

import hashlib
from typing import List, Dict, Any
from app.models import GeneratePageResponse, PageData
from app.vertical_profiles import get_vertical_profile, get_trade_name


def generate_service_hub_content(generator, data: PageData) -> GeneratePageResponse:
    """
    Generate service hub page content with AI-generated unique content.
    
    Args:
        generator: The AIContentGenerator instance
        data: Page generation parameters with hub information
        
    Returns:
        Complete validated hub page content with unique AI-generated text
    """
    vertical = data.vertical or "other"
    hub_key = data.hub_key or "residential"
    hub_slug = data.hub_slug or "services"
    
    # Deterministic variant selection based on slug
    variant = _get_variant_from_slug(hub_slug)
    
    # Debug log
    print(f"[HUB] slug={hub_slug} variant={variant} hub_key={hub_key}")
    
    vertical_profile = get_vertical_profile(vertical)
    trade_name = vertical_profile["trade_name"]
    hub_label = data.hub_label or "Services"
    
    # Build title and meta
    title = f"{hub_label} {trade_name.title()} Services"
    if data.business_name:
        title += f" | {data.business_name}"
    
    h1_text = f"{hub_label} {trade_name.title()} Services"
    slug = hub_slug
    
    meta_description = f"Professional {hub_label.lower()} {trade_name} services. "
    if data.service_area_label:
        meta_description += f"Serving {data.service_area_label}. "
    meta_description += f"{data.cta_text}."
    
    # Generate AI content with hub-specific focus
    ai_content = _call_openai_hub_generation(
        generator=generator,
        data=data,
        vertical_profile=vertical_profile,
        hub_key=hub_key,
        hub_label=hub_label,
        trade_name=trade_name
    )
    
    # Assemble blocks using selected variant for ordering
    blocks = _assemble_blocks_for_variant(
        variant=variant,
        ai_content=ai_content,
        h1_text=h1_text,
        data=data
    )
    
    response = GeneratePageResponse(
        title=title,
        meta_description=meta_description[:160],
        slug=slug,
        blocks=blocks
    )
    
    return response


def _get_variant_from_slug(slug: str) -> int:
    """
    Deterministically select variant (0, 1, or 2) based on slug.
    Uses SHA256 hash to ensure consistent selection.
    """
    hash_bytes = hashlib.sha256(slug.encode('utf-8')).digest()
    hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
    return hash_int % 3


def _call_openai_hub_generation(
    generator,
    data: PageData,
    vertical_profile: Dict,
    hub_key: str,
    hub_label: str,
    trade_name: str
) -> Dict:
    """
    Call OpenAI to generate unique hub page content with hub-specific focus.
    """
    vocabulary = vertical_profile.get("vocabulary", [])
    
    # Hub-specific content guidance
    hub_guidance = _get_hub_specific_guidance(hub_key, hub_label, trade_name)
    
    # Build services list
    services_list = ""
    if data.services_for_hub:
        services_list = "\n".join([f"- {s.get('name', '')}" for s in data.services_for_hub[:20]])
    
    # Add randomization to prompt to ensure unique content
    import random
    import time
    random.seed(time.time())  # Use current time for randomness
    
    writing_styles = [
        "conversational and approachable",
        "authoritative and technical",
        "straightforward and practical",
        "detailed and educational"
    ]
    
    opening_approaches = [
        "Start by addressing common pain points",
        "Begin with the value proposition",
        "Open with what makes this service essential",
        "Lead with customer concerns and solutions"
    ]
    
    style = random.choice(writing_styles)
    approach = random.choice(opening_approaches)
    
    system_prompt = f"""You are an expert {trade_name} content writer creating a {hub_label.lower()} service hub page.

WRITING STYLE: Use a {style} tone throughout.
APPROACH: {approach}

CRITICAL RULES:
1. Do NOT mention any specific city, town, or neighborhood
2. Keep content general and applicable to the entire service area
3. Use trade-specific vocabulary: {', '.join(vocabulary[:10])}
4. Focus on {hub_guidance['audience']} needs and concerns
5. Emphasize {hub_guidance['key_focus']}
6. Be professional and informative, not salesy
7. Output ONLY valid JSON matching the schema below
8. IMPORTANT: Write unique, varied content - avoid generic phrases and templates

FORBIDDEN:
- Never mention specific cities or locations
- No marketing fluff like "top-notch", "premier", "best-in-class"
- No meta-language like "this page", "this article"
- No repetitive sentence structures
"""

    # Add unique elements to each generation
    unique_angles = [
        "Focus on real-world scenarios and practical examples",
        "Emphasize problem-solving and solutions",
        "Highlight expertise and experience",
        "Address common misconceptions and concerns"
    ]
    
    faq_approaches = [
        "Answer questions in a direct, helpful manner",
        "Provide detailed explanations with context",
        "Use examples to illustrate answers",
        "Address both the question and underlying concerns"
    ]
    
    angle = random.choice(unique_angles)
    faq_style = random.choice(faq_approaches)
    
    user_prompt = f"""Generate content blocks for a {hub_label.lower()} {trade_name} service hub page.

Hub Category: {hub_label}
Target Audience: {hub_guidance['audience']}
Key Focus: {hub_guidance['key_focus']}
Business Type: {trade_name}
Business Name: {data.business_name or 'Our Company'}
Phone: {data.phone or ''}
Service Area: {data.service_area_label or 'your area'}
CTA Text: {data.cta_text}

Services Offered:
{services_list}

Content Guidelines:
{hub_guidance['content_guidelines']}

CONTENT ANGLE: {angle}
FAQ STYLE: {faq_style}

IMPORTANT: Create unique, original content. Do NOT use generic templates or repetitive phrases. Each section should feel naturally written and specific to this service type and audience. Vary your sentence structure and vocabulary throughout.

Generate these sections with unique, natural content:

1. "Who This Is For" section:
   - Heading: "Who Benefits from {hub_label} {trade_name.title()} Services"
   - 2 paragraphs explaining who should use these services and who they're not for
   - Focus on {hub_guidance['audience']} specifically

2. "Common Projects" section:
   - Heading: "Common {hub_label} {trade_name.title()} Projects"
   - 1-2 paragraphs with specific examples relevant to {hub_guidance['audience']}

3. "Our Process" section:
   - Heading: "Our {hub_label} Service Process"
   - 1-2 paragraphs explaining how you work, emphasizing {hub_guidance['process_focus']}

4. "Compliance" section:
   - Heading: "Permits, Codes & Safety Standards"
   - 1 paragraph about compliance, emphasizing {hub_guidance['compliance_focus']}

5. "Service Areas" section:
   - Heading: "Primary Service Areas"
   - 1 contextual paragraph about serving the area
   - Then include this shortcode EXACTLY: [seogen_service_hub_city_links hub_key="{data.hub_key}" limit="6"]

6. "Pricing" section:
   - Heading: "Understanding Project Costs"
   - 1 paragraph about pricing factors, mentioning {hub_guidance['pricing_focus']}

7. "FAQs" section:
   - Heading: "Frequently Asked Questions"
   - 6 FAQs with detailed answers (3-4 sentences each)
   - Questions should be specific to {hub_guidance['audience']} concerns
   - Examples: {hub_guidance['faq_examples']}

8. CTA block with text: "{data.cta_text}"

Output JSON schema:
{{
  "who_this_is_for": {{
    "heading": "Who Benefits from {hub_label} {trade_name.title()} Services",
    "paragraphs": ["paragraph 1 text", "paragraph 2 text"]
  }},
  "common_projects": {{
    "heading": "Common {hub_label} {trade_name.title()} Projects",
    "paragraphs": ["paragraph text with examples"]
  }},
  "process": {{
    "heading": "Our {hub_label} Service Process",
    "paragraphs": ["paragraph text about process"]
  }},
  "compliance": {{
    "heading": "Permits, Codes & Safety Standards",
    "paragraphs": ["paragraph text about compliance"]
  }},
  "service_areas": {{
    "heading": "Primary Service Areas",
    "paragraphs": ["contextual paragraph", "We provide {hub_label.lower()} {trade_name} services throughout {data.service_area_label or 'the area'}. [seogen_service_hub_city_links hub_key=\\"{data.hub_key}\\" limit=\\"6\\"]"]
  }},
  "pricing": {{
    "heading": "Understanding Project Costs",
    "paragraphs": ["paragraph text about pricing"]
  }},
  "faqs": [
    {{"question": "Question text?", "answer": "Detailed 3-4 sentence answer"}},
    {{"question": "Question text?", "answer": "Detailed 3-4 sentence answer"}},
    ...6 total FAQs
  ]
}}

CRITICAL: 
- Write substantial paragraphs (3-4 sentences minimum)
- Use technical trade vocabulary naturally
- Make content specific to {hub_guidance['audience']}
- Include the shortcode token EXACTLY as shown in service_areas
- Do NOT mention specific cities or neighborhoods
- Make FAQs relevant to {hub_guidance['audience']} concerns"""

    try:
        result = generator._call_openai_json(system_prompt, user_prompt, max_tokens=3500, temperature=0.8)
        return result
    except Exception as e:
        print(f"[HUB] OpenAI generation failed: {e}, using fallback")
        return _generate_fallback_content(hub_key, hub_label, trade_name, data)


def _get_hub_specific_guidance(hub_key: str, hub_label: str, trade_name: str) -> Dict:
    """Get hub-specific content guidance for AI generation."""
    
    if hub_key == "residential":
        return {
            "audience": "homeowners and residential property owners",
            "key_focus": "family safety, property value, and minimal disruption to daily life",
            "process_focus": "respectful service, working around family schedules, and protecting your home",
            "compliance_focus": "residential safety codes and protecting home value",
            "pricing_focus": "home size factors and financing options for homeowners",
            "content_guidelines": "Focus on homeowner concerns like safety, property value, family disruption, and home protection",
            "faq_examples": "Do I need to be home? Will you protect my floors? How does this affect resale value?"
        }
    elif hub_key == "commercial":
        return {
            "audience": "business owners, facility managers, and commercial property operators",
            "key_focus": "minimizing business downtime, compliance documentation, and after-hours service",
            "process_focus": "flexible scheduling, detailed documentation, and coordination with business operations",
            "compliance_focus": "commercial codes, OSHA requirements, and insurance documentation",
            "pricing_focus": "facility complexity, maintenance contracts, and business budgeting",
            "content_guidelines": "Focus on business concerns like downtime costs, permits, insurance, and operational disruption",
            "faq_examples": "Can you work after hours? Who handles permits? Do you provide compliance documentation?"
        }
    elif hub_key == "emergency":
        return {
            "audience": "property owners facing urgent issues requiring immediate attention",
            "key_focus": "rapid response, 24/7 availability, and immediate safety",
            "process_focus": "fast response times, safety triage, and immediate stabilization",
            "compliance_focus": "emergency safety protocols and code-compliant permanent repairs",
            "pricing_focus": "premium rates for immediate response and after-hours availability",
            "content_guidelines": "Focus on urgency, safety hazards, response times, and emergency vs routine service",
            "faq_examples": "How quickly can you respond? What qualifies as emergency? Do you work holidays?"
        }
    else:
        return {
            "audience": "property owners",
            "key_focus": "quality service and professional results",
            "process_focus": "clear communication and professional execution",
            "compliance_focus": "building codes and safety standards",
            "pricing_focus": "transparent pricing and project scope",
            "content_guidelines": "Focus on general service quality and professionalism",
            "faq_examples": "What services do you offer? How quickly can you respond? Do you provide estimates?"
        }


def _generate_fallback_content(hub_key: str, hub_label: str, trade_name: str, data: PageData) -> Dict:
    """Generate fallback content if AI generation fails."""
    return {
        "who_this_is_for": {
            "heading": f"Who Benefits from {hub_label} {trade_name.title()} Services",
            "paragraphs": [
                f"These services are designed for property owners who need reliable {trade_name} work.",
                f"We work with clients who value quality workmanship and professional service."
            ]
        },
        "common_projects": {
            "heading": f"Common {hub_label} {trade_name.title()} Projects",
            "paragraphs": [
                f"We handle a wide range of {hub_label.lower()} {trade_name} projects including installations, repairs, maintenance, and upgrades."
            ]
        },
        "process": {
            "heading": f"Our {hub_label} Service Process",
            "paragraphs": [
                f"We begin every project with a thorough assessment and provide clear communication throughout the process."
            ]
        },
        "compliance": {
            "heading": "Permits, Codes & Safety Standards",
            "paragraphs": [
                f"All work complies with applicable building codes and safety standards. We handle necessary permits and inspections."
            ]
        },
        "service_areas": {
            "heading": "Primary Service Areas",
            "paragraphs": [
                f"We provide {hub_label.lower()} {trade_name} services throughout {data.service_area_label or 'the area'}.",
                f"Explore our services in your area. [seogen_service_hub_city_links hub_key=\"{data.hub_key}\" limit=\"6\"]"
            ]
        },
        "pricing": {
            "heading": "Understanding Project Costs",
            "paragraphs": [
                f"Project costs vary based on scope, materials, and complexity. We provide detailed estimates before starting work."
            ]
        },
        "faqs": [
            {
                "question": f"What types of {hub_label.lower()} {trade_name} services do you provide?",
                "answer": f"We offer comprehensive {hub_label.lower()} {trade_name} services including installations, repairs, maintenance, and emergency services."
            },
            {
                "question": "How quickly can you respond to service requests?",
                "answer": "Response times vary based on the nature of the request and current schedule. We'll provide an estimated timeframe when you contact us."
            },
            {
                "question": "Do you provide estimates before starting work?",
                "answer": f"Yes, we provide detailed estimates for all projects including scope of work, materials, labor, and timeline."
            },
            {
                "question": "Are your technicians licensed and insured?",
                "answer": f"Yes, our technicians hold appropriate licenses and we maintain comprehensive insurance coverage."
            },
            {
                "question": "What areas do you serve?",
                "answer": f"We provide services throughout our coverage area. Contact us to confirm availability for your location."
            },
            {
                "question": "What warranty comes with your work?",
                "answer": f"We warranty our workmanship. Specific terms depend on the type of work and materials used."
            }
        ]
    }


def _assemble_blocks_for_variant(
    variant: int,
    ai_content: Dict,
    h1_text: str,
    data: PageData
) -> List[Dict]:
    """
    Assemble AI-generated content blocks in variant-specific order.
    
    Variant 0: Standard order (Who → Projects → Process → Compliance → Areas → Pricing → FAQs)
    Variant 1: Reordered (Projects → Who → Compliance → Process → Areas → FAQs → Pricing)
    Variant 2: Alternative (Process → Compliance → Who → Projects → Pricing → Areas → FAQs)
    """
    blocks = []
    
    # Hero section (H1)
    blocks.append({
        "type": "heading",
        "level": 1,
        "text": h1_text
    })
    
    # Convert AI content sections to block format
    sections = {
        "who": _section_to_blocks(ai_content.get("who_this_is_for", {})),
        "projects": _section_to_blocks(ai_content.get("common_projects", {})),
        "process": _section_to_blocks(ai_content.get("process", {})),
        "compliance": _section_to_blocks(ai_content.get("compliance", {})),
        "areas": _section_to_blocks(ai_content.get("service_areas", {})),
        "pricing": _section_to_blocks(ai_content.get("pricing", {})),
        "faqs": _faqs_to_blocks(ai_content.get("faqs", []))
    }
    
    # Assemble in variant-specific order
    if variant == 0:
        # Variant 0: Standard order
        blocks.extend(sections["who"])
        blocks.extend(sections["projects"])
        blocks.extend(sections["process"])
        blocks.extend(sections["compliance"])
        blocks.extend(sections["areas"])
        blocks.extend(sections["pricing"])
        blocks.extend(sections["faqs"])
        
    elif variant == 1:
        # Variant 1: Reordered
        blocks.extend(sections["projects"])
        blocks.extend(sections["who"])
        blocks.extend(sections["compliance"])
        blocks.extend(sections["process"])
        blocks.extend(sections["areas"])
        blocks.extend(sections["faqs"])
        blocks.extend(sections["pricing"])
        
    else:  # variant == 2
        # Variant 2: Alternative order
        blocks.extend(sections["process"])
        blocks.extend(sections["compliance"])
        blocks.extend(sections["who"])
        blocks.extend(sections["projects"])
        blocks.extend(sections["pricing"])
        blocks.extend(sections["areas"])
        blocks.extend(sections["faqs"])
    
    # Add CTA
    blocks.append({
        "type": "cta",
        "text": data.cta_text or "Contact Us Today",
        "phone": data.phone or ""
    })
    
    return blocks


def _section_to_blocks(section: Dict) -> List[Dict]:
    """Convert a section dict to block format."""
    blocks = []
    
    if not section:
        return blocks
    
    # Add heading
    heading = section.get("heading", "")
    if heading:
        blocks.append({
            "type": "heading",
            "level": 2,
            "text": heading
        })
    
    # Add paragraphs
    paragraphs = section.get("paragraphs", [])
    for para in paragraphs:
        if para:
            blocks.append({
                "type": "paragraph",
                "text": para
            })
    
    return blocks


def _faqs_to_blocks(faqs: List[Dict]) -> List[Dict]:
    """Convert FAQs list to block format."""
    blocks = []
    
    if not faqs:
        return blocks
    
    # Add FAQ heading
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": "Frequently Asked Questions"
    })
    
    # Add FAQ blocks
    for faq in faqs:
        if faq.get("question") and faq.get("answer"):
            blocks.append({
                "type": "faq",
                "question": faq["question"],
                "answer": faq["answer"]
            })
    
    return blocks
