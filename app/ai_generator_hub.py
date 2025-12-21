"""
Service Hub Page Generation with Randomized Structure (Like Service Pages)

Uses the same randomization approach as service+city pages to ensure truly unique content:
- Random section headings
- Random section positions
- Random FAQ count
- Less prescriptive prompts
- Natural content generation
"""

import hashlib
import random
from typing import List, Dict, Any
from app.models import GeneratePageResponse, PageData
from app.vertical_profiles import get_vertical_profile, get_trade_name


def generate_service_hub_content(generator, data: PageData) -> GeneratePageResponse:
    """
    Generate service hub page content with randomized structure for uniqueness.
    
    Uses same approach as service+city pages to ensure truly unique content.
    """
    vertical = data.vertical or "other"
    hub_key = data.hub_key or "residential"
    hub_slug = data.hub_slug or "services"
    
    # Debug log
    print(f"[HUB] slug={hub_slug} hub_key={hub_key}")
    
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
    
    # Generate AI content with randomized structure
    ai_content = _call_openai_hub_generation(
        generator=generator,
        data=data,
        vertical_profile=vertical_profile,
        hub_key=hub_key,
        hub_label=hub_label,
        trade_name=trade_name
    )
    
    # Convert AI content to blocks
    blocks = _convert_to_blocks(ai_content, h1_text, data)
    
    response = GeneratePageResponse(
        title=title,
        meta_description=meta_description[:160],
        slug=slug,
        blocks=blocks
    )
    
    return response


def _get_random_hub_headings(hub_label: str, trade_name: str, hub_key: str) -> Dict[str, str]:
    """Generate random heading variations for each section (like service pages)."""
    
    # Hub-specific heading variations
    if hub_key == "residential":
        audience_term = random.choice(["Homeowners", "Residential Property Owners", "Home Owners"])
        service_term = random.choice(["Services", "Solutions", "Work"])
    elif hub_key == "commercial":
        audience_term = random.choice(["Business Owners", "Commercial Property Managers", "Facility Managers"])
        service_term = random.choice(["Services", "Solutions", "Work"])
    elif hub_key == "emergency":
        audience_term = random.choice(["Property Owners", "Homeowners & Businesses", "Customers"])
        service_term = random.choice(["Emergency Services", "Urgent Response", "Emergency Work"])
    else:
        audience_term = random.choice(["Property Owners", "Customers", "Clients"])
        service_term = random.choice(["Services", "Solutions", "Work"])
    
    headings = {
        'who_for': random.choice([
            f"Who Benefits from {hub_label} {trade_name.title()} {service_term}",
            f"Is This Right for Your Property?",
            f"Who We Serve with {hub_label} {service_term}",
            f"{audience_term} Who Need {hub_label} {service_term}"
        ]),
        'projects': random.choice([
            f"Common {hub_label} {trade_name.title()} Projects",
            f"Typical {hub_label} Work We Handle",
            f"What We Do for {audience_term}",
            f"{hub_label} Projects We Complete"
        ]),
        'process': random.choice([
            f"Our {hub_label} Service Process",
            f"How We Work with {audience_term}",
            f"What to Expect from Our {hub_label} {service_term}",
            f"Our Approach to {hub_label} Work"
        ]),
        'compliance': random.choice([
            "Permits, Codes & Safety Standards",
            "Code Compliance & Permits",
            "Safety Standards & Regulations",
            "Meeting Code Requirements"
        ]),
        'service_areas': random.choice([
            "Primary Service Areas",
            "Areas We Serve",
            "Service Coverage",
            "Where We Work"
        ]),
        'pricing': random.choice([
            "Understanding Project Costs",
            "What Affects Pricing",
            "Investment & Pricing Factors",
            "Cost Considerations"
        ]),
        'faqs': "Frequently Asked Questions"
    }
    
    return headings


def _call_openai_hub_generation(
    generator,
    data: PageData,
    vertical_profile: Dict,
    hub_key: str,
    hub_label: str,
    trade_name: str
) -> Dict:
    """
    Call OpenAI with randomized, less prescriptive prompt (like service pages).
    """
    vocabulary = vertical_profile.get("vocabulary", [])
    
    # Randomize structure elements (like service pages)
    num_faqs = random.randint(4, 7)  # Variable FAQ count
    headings = _get_random_hub_headings(hub_label, trade_name, hub_key)
    
    # Hub-specific guidance
    hub_guidance = _get_hub_specific_guidance(hub_key, hub_label, trade_name)
    
    # Build services list
    services_list = ""
    if data.services_for_hub:
        services_list = "\n".join([f"- {s.get('name', '')}" for s in data.services_for_hub[:20]])
    
    # Simple, less prescriptive system prompt (like service pages)
    system_prompt = f"""You are a professional {trade_name} content writer. Write natural, helpful content that genuinely helps {hub_guidance['audience']} understand these services and make informed decisions. Focus on practical, actionable information rather than marketing fluff."""
    
    user_prompt = f"""Generate content for a {hub_label.lower()} {trade_name} service hub page.

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

Return ONLY valid JSON with this structure:
{{
  "sections": [
    {{"heading": "{headings['who_for']}", "paragraph": "2-3 sentences explaining who these services are for and who they're not for"}},
    {{"heading": "{headings['projects']}", "paragraph": "2-3 sentences with specific project examples relevant to {hub_guidance['audience']}"}},
    {{"heading": "{headings['process']}", "paragraph": "2-3 sentences about how you work, emphasizing {hub_guidance['process_focus']}"}},
    {{"heading": "{headings['compliance']}", "paragraph": "2-3 sentences about compliance, emphasizing {hub_guidance['compliance_focus']}"}},
    {{"heading": "{headings['service_areas']}", "paragraph": "1-2 sentences about serving the area"}},
    {{"heading": "{headings['pricing']}", "paragraph": "2-3 sentences about pricing factors, mentioning {hub_guidance['pricing_focus']}"}}
  ],
  "faqs": [
    {', '.join(['{{"question": "string", "answer": "string"}}'] * num_faqs)}
  ],
  "cta_text": "{data.cta_text or 'Contact Us Today'}"
}}

CRITICAL RULES:
1. Do NOT mention specific cities, towns, or neighborhoods
2. Use trade-specific vocabulary: {', '.join(vocabulary[:8])}
3. Focus on {hub_guidance['audience']} needs and concerns
4. Write unique, natural content - avoid generic templates
5. Make FAQs specific to {hub_guidance['audience']} concerns
6. No marketing fluff like "top-notch", "premier", "best-in-class"

FAQ Examples for this audience: {hub_guidance['faq_examples']}"""

    try:
        result = generator._call_openai_json(system_prompt, user_prompt, max_tokens=3000, temperature=0.9)
        
        # Add shortcode to service areas section
        if result.get("sections"):
            for section in result["sections"]:
                if section.get("heading") == headings['service_areas']:
                    section["paragraph"] += f" [seogen_service_hub_city_links hub_key=\"{data.hub_key}\" limit=\"6\"]"
        
        return result
    except Exception as e:
        print(f"[HUB] OpenAI generation failed: {e}, using fallback")
        return _generate_fallback_content(hub_key, hub_label, trade_name, data, headings, num_faqs)


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


def _generate_fallback_content(hub_key: str, hub_label: str, trade_name: str, data: PageData, headings: Dict, num_faqs: int) -> Dict:
    """Generate fallback content if AI generation fails."""
    return {
        "sections": [
            {
                "heading": headings['who_for'],
                "paragraph": f"These services are designed for property owners who need reliable {trade_name} work. We work with clients who value quality workmanship and professional service."
            },
            {
                "heading": headings['projects'],
                "paragraph": f"We handle a wide range of {hub_label.lower()} {trade_name} projects including installations, repairs, maintenance, and upgrades."
            },
            {
                "heading": headings['process'],
                "paragraph": f"We begin every project with a thorough assessment and provide clear communication throughout the process."
            },
            {
                "heading": headings['compliance'],
                "paragraph": f"All work complies with applicable building codes and safety standards. We handle necessary permits and inspections."
            },
            {
                "heading": headings['service_areas'],
                "paragraph": f"We provide {hub_label.lower()} {trade_name} services throughout {data.service_area_label or 'the area'}. [seogen_service_hub_city_links hub_key=\"{data.hub_key}\" limit=\"6\"]"
            },
            {
                "heading": headings['pricing'],
                "paragraph": f"Project costs vary based on scope, materials, and complexity. We provide detailed estimates before starting work."
            }
        ],
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
            }
        ][:num_faqs],
        "cta_text": data.cta_text or "Contact Us Today"
    }


def _convert_to_blocks(ai_content: Dict, h1_text: str, data: PageData) -> List[Dict]:
    """Convert AI-generated content to block format."""
    blocks = []
    
    # H1
    blocks.append({
        "type": "heading",
        "level": 1,
        "text": h1_text
    })
    
    # Sections
    for section in ai_content.get("sections", []):
        if section.get("heading"):
            blocks.append({
                "type": "heading",
                "level": 2,
                "text": section["heading"]
            })
        if section.get("paragraph"):
            blocks.append({
                "type": "paragraph",
                "text": section["paragraph"]
            })
    
    # FAQs
    faqs = ai_content.get("faqs", [])
    if faqs:
        blocks.append({
            "type": "heading",
            "level": 2,
            "text": "Frequently Asked Questions"
        })
        for faq in faqs:
            if faq.get("question") and faq.get("answer"):
                blocks.append({
                    "type": "faq",
                    "question": faq["question"],
                    "answer": faq["answer"]
                })
    
    # CTA
    blocks.append({
        "type": "cta",
        "text": ai_content.get("cta_text", data.cta_text or "Contact Us Today"),
        "phone": data.phone or ""
    })
    
    return blocks
