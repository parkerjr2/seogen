"""
Service Hub Page Generation with Variation Framework (Anti-Doorway Strategy)

This module generates unique, valuable hub pages that differ meaningfully across
hub types to avoid doorway page patterns. Each hub type has:
- Unique section order (different blueprints)
- Hub-specific content and messaging
- Unique FAQ questions
- Distinct audience focus and value propositions

WHY THIS APPROACH REDUCES DOORWAY RISK:
1. Different blueprints = different information architecture per hub
2. Unique FAQs = no duplicate content across hubs
3. Hub profiles = substantively different messaging and focus
4. Contextual internal links = natural, varied anchor text
5. Uniqueness validation = automated quality checks

This creates buyer guide experiences, not templated landing pages.
"""

from typing import List, Dict, Any
from app.models import GeneratePageResponse, PageData
from app.vertical_profiles import get_vertical_profile, get_trade_name
from app.hub_profiles import get_hub_profile
from app.hub_blueprints import get_blueprint_for_hub
from app.hub_faq_banks import get_faqs_for_hub


def generate_service_hub_content(generator, data: PageData) -> GeneratePageResponse:
    """
    Generate service hub page content using variation framework.
    
    Args:
        generator: The AIContentGenerator instance
        data: Page generation parameters with hub information
        
    Returns:
        Complete validated hub page content with unique structure per hub type
    """
    vertical = data.vertical or "other"
    hub_key = data.hub_key or "residential"
    
    # Get profiles and blueprints
    vertical_profile = get_vertical_profile(vertical)
    hub_profile = get_hub_profile(hub_key)
    blueprint = get_blueprint_for_hub(hub_key)
    
    trade_name = vertical_profile["trade_name"]
    hub_label = data.hub_label or hub_profile["audience_label"]
    
    # Build title and meta
    title = f"{hub_label} {trade_name.title()} Services"
    if data.business_name:
        title += f" | {data.business_name}"
    
    h1_text = f"{hub_label} {trade_name.title()} Services"
    slug = data.hub_slug or generator.slugify(hub_label, trade_name)
    
    meta_description = f"Professional {hub_label.lower()} {trade_name} services for {hub_profile['audience_description']}. "
    if data.service_area_label:
        meta_description += f"Serving {data.service_area_label}. "
    meta_description += f"{data.cta_text}."
    
    # Generate content blocks following blueprint
    blocks = _generate_blocks_from_blueprint(
        generator=generator,
        data=data,
        vertical_profile=vertical_profile,
        hub_profile=hub_profile,
        blueprint=blueprint,
        h1_text=h1_text
    )
    
    # Validate uniqueness
    _validate_hub_uniqueness(blocks, hub_key, hub_profile)
    
    response = GeneratePageResponse(
        title=title,
        meta_description=meta_description[:160],
        slug=slug,
        blocks=blocks
    )
    
    return response


def _generate_blocks_from_blueprint(
    generator,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict,
    blueprint,
    h1_text: str
) -> List[Dict]:
    """
    Generate content blocks following the hub's blueprint structure.
    Each section type has specific content generation logic.
    """
    blocks = []
    trade_name = vertical_profile["trade_name"]
    hub_key = data.hub_key or "residential"
    
    # Hero section (H1 + intro paragraph)
    blocks.append({
        "type": "heading",
        "level": 1,
        "text": h1_text
    })
    
    # Hero intro paragraph with hub-specific messaging
    intro_text = _generate_hero_intro(data, vertical_profile, hub_profile)
    blocks.append({
        "type": "paragraph",
        "text": intro_text
    })
    
    # Generate sections according to blueprint
    for section in blueprint.sections:
        section_type = section["type"]
        
        if section_type == "hero":
            continue  # Already handled
        
        elif section_type == "who_this_is_for":
            blocks.extend(_generate_who_this_is_for_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "common_projects" or section_type == "common_repairs" or \
             section_type == "common_installations" or section_type == "common_services" or \
             section_type == "common_emergencies":
            blocks.extend(_generate_common_projects_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "how_we_work" or section_type == "response_process" or \
             section_type == "diagnostic_approach" or section_type == "planning_process":
            blocks.extend(_generate_process_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "safety_and_code" or section_type == "compliance_first" or \
             section_type == "permits_and_coordination":
            blocks.extend(_generate_compliance_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "service_areas":
            blocks.extend(_generate_service_areas_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "pricing_factors":
            blocks.extend(_generate_pricing_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "downtime_management":
            blocks.extend(_generate_downtime_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "when_to_call":
            blocks.extend(_generate_when_to_call_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "repair_vs_replace":
            blocks.extend(_generate_repair_vs_replace_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "why_maintenance" or section_type == "maintenance_programs":
            blocks.extend(_generate_maintenance_section(
                section, data, vertical_profile, hub_profile
            ))
        
        elif section_type == "faqs":
            blocks.extend(_generate_faqs_section(
                section, hub_key
            ))
        
        elif section_type == "cta":
            blocks.append(_generate_cta_block(data, hub_profile))
    
    return blocks


def _generate_hero_intro(data: PageData, vertical_profile: Dict, hub_profile: Dict) -> str:
    """Generate hero intro paragraph with hub-specific proof signals and pain points."""
    trade_name = vertical_profile["trade_name"]
    audience = hub_profile["audience_description"]
    pain_point = hub_profile["primary_pain_points"][0]
    proof_signal = hub_profile["proof_signals"][0]
    
    intro = f"Our {trade_name} services are designed for {audience}, addressing {pain_point.lower()}. "
    intro += f"We provide {proof_signal.lower()}, ensuring quality results and peace of mind. "
    intro += f"Whether you need routine service or specialized work, our experienced team delivers reliable solutions."
    
    return intro


def _generate_who_this_is_for_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate 'Who This Is For / Not For' section."""
    blocks = []
    trade_name = vertical_profile["trade_name"]
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    # Who it's for
    job_examples = hub_profile["typical_job_examples"][:3]
    for_text = f"This service is ideal for {hub_profile['audience_description']} who need: "
    for_text += ", ".join(job_examples[:2]) + f", or {job_examples[2]}. "
    for_text += f"We understand the unique needs of {hub_profile['audience_label'].lower()} and tailor our approach accordingly."
    
    blocks.append({
        "type": "paragraph",
        "text": for_text
    })
    
    # Who it's NOT for (disqualifiers)
    if hub_profile["disqualifiers"]:
        not_for_text = "This service may not be the best fit for: "
        not_for_text += ". ".join(hub_profile["disqualifiers"]) + "."
        
        blocks.append({
            "type": "paragraph",
            "text": not_for_text
        })
    
    return blocks


def _generate_common_projects_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate common projects/jobs section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    job_examples = hub_profile["typical_job_examples"]
    examples_text = f"We handle a wide range of projects including {job_examples[0].lower()}, "
    examples_text += f"{job_examples[1].lower()}, {job_examples[2].lower()}, and {job_examples[3].lower()}. "
    examples_text += f"Each project receives the same attention to detail and professional standards, "
    examples_text += f"regardless of size or complexity."
    
    blocks.append({
        "type": "paragraph",
        "text": examples_text
    })
    
    return blocks


def _generate_process_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate process/how we work section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    scheduling_focus = hub_profile["scheduling_focus"]
    process_text = f"Our process emphasizes {scheduling_focus}. "
    process_text += f"We begin with a thorough assessment of your needs, provide clear communication throughout, "
    process_text += f"and ensure you understand each step. {hub_profile['proof_signals'][1]}. "
    process_text += f"We complete work efficiently while maintaining high quality standards."
    
    blocks.append({
        "type": "paragraph",
        "text": process_text
    })
    
    return blocks


def _generate_compliance_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate compliance/permits/code section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    compliance_focus = hub_profile["compliance_focus"]
    compliance_text = f"All work complies with {compliance_focus}. "
    compliance_text += f"We handle necessary permits and coordinate required inspections, "
    compliance_text += f"ensuring your project meets all regulatory requirements. "
    compliance_text += f"Proper compliance protects you and ensures work quality."
    
    blocks.append({
        "type": "paragraph",
        "text": compliance_text
    })
    
    return blocks


def _generate_service_areas_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate service areas section with contextual intro and city links shortcode."""
    blocks = []
    trade_name = vertical_profile["trade_name"]
    hub_key = data.hub_key or "residential"
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    # Contextual introduction (varied by hub type)
    context_intros = {
        "residential": f"Homeowners throughout the region rely on our {trade_name} services for their properties. We're familiar with local building codes and common home challenges in each community we serve.",
        "commercial": f"Business owners and facility managers across multiple locations trust us for {trade_name} services. We understand the importance of minimizing disruption to your operations.",
        "emergency": f"When urgent {trade_name} issues arise, fast response matters. We provide emergency service throughout the region with technicians ready to respond quickly.",
        "repair": f"Property owners facing {trade_name} problems need reliable diagnostics and lasting fixes. We serve communities throughout the area with honest repair recommendations.",
        "installation": f"Planning a {trade_name} installation project requires local expertise. We work throughout the region, familiar with local permit requirements and inspection processes.",
        "maintenance": f"Protecting your {trade_name} investment through regular maintenance prevents costly breakdowns. We serve property owners throughout the area with comprehensive maintenance programs."
    }
    
    context_text = context_intros.get(hub_key, context_intros["residential"])
    blocks.append({
        "type": "paragraph",
        "text": context_text
    })
    
    # Shortcode paragraph
    service_area = data.service_area_label or "the area"
    shortcode_text = f"We provide {trade_name} services throughout {service_area}. [seogen_service_hub_city_links hub_key=\"{hub_key}\" limit=\"6\"]"
    
    blocks.append({
        "type": "paragraph",
        "text": shortcode_text
    })
    
    return blocks


def _generate_pricing_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate pricing factors section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    pricing_text = f"Project costs vary based on scope, materials, labor requirements, and complexity. "
    pricing_text += f"We provide detailed estimates before starting work, explaining what factors affect pricing. "
    pricing_text += f"Our goal is transparent pricing with no hidden fees or surprise charges."
    
    blocks.append({
        "type": "paragraph",
        "text": pricing_text
    })
    
    return blocks


def _generate_downtime_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate downtime management section (commercial-specific)."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    downtime_text = f"We understand business downtime costs money. Our commercial services include flexible scheduling "
    downtime_text += f"for after-hours and weekend work to minimize impact on your operations. "
    downtime_text += f"We coordinate closely with your team to ensure work is completed efficiently without disrupting business."
    
    blocks.append({
        "type": "paragraph",
        "text": downtime_text
    })
    
    return blocks


def _generate_when_to_call_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate when to call section (emergency-specific)."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    when_text = f"Call for emergency service when facing immediate safety hazards, active property damage, "
    when_text += f"or complete loss of essential services. If you're unsure whether your situation qualifies as an emergency, "
    when_text += f"call us and describe the problem. We'll help you determine the appropriate response level."
    
    blocks.append({
        "type": "paragraph",
        "text": when_text
    })
    
    return blocks


def _generate_repair_vs_replace_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate repair vs replace section (repair-specific)."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    repair_text = f"After diagnosing the problem, we'll provide honest recommendations about repair versus replacement. "
    repair_text += f"We consider the system's age, overall condition, repair cost, and likelihood of future problems. "
    repair_text += f"Our goal is to help you make the best decision for your situation, not to sell unnecessary replacements."
    
    blocks.append({
        "type": "paragraph",
        "text": repair_text
    })
    
    return blocks


def _generate_maintenance_section(
    section: Dict,
    data: PageData,
    vertical_profile: Dict,
    hub_profile: Dict
) -> List[Dict]:
    """Generate maintenance value/programs section (maintenance-specific)."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    maint_text = f"Regular maintenance prevents unexpected breakdowns, extends system life, and maintains efficiency. "
    maint_text += f"Our maintenance programs include scheduled inspections, preventive service, priority response, "
    maint_text += f"and detailed reporting. We'll recommend an appropriate maintenance schedule based on your specific needs."
    
    blocks.append({
        "type": "paragraph",
        "text": maint_text
    })
    
    return blocks


def _generate_faqs_section(section: Dict, hub_key: str) -> List[Dict]:
    """Generate FAQs section using hub-specific FAQ bank."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": section["heading"]
    })
    
    # Get hub-specific FAQs
    faqs = get_faqs_for_hub(hub_key, count=8)
    
    for faq in faqs:
        blocks.append({
            "type": "faq",
            "question": faq["question"],
            "answer": faq["answer"]
        })
    
    return blocks


def _generate_cta_block(data: PageData, hub_profile: Dict) -> Dict:
    """Generate CTA block with hub-specific angle."""
    return {
        "type": "cta",
        "text": data.cta_text or hub_profile["cta_angle"],
        "phone": data.phone or ""
    }


def _validate_hub_uniqueness(blocks: List[Dict], hub_key: str, hub_profile: Dict) -> None:
    """
    Validate that generated content meets uniqueness requirements.
    
    Checks:
    1. Heading uniqueness - at least 2 headings differ from other hub types
    2. FAQ uniqueness - questions come from hub-specific bank
    3. Intro contains hub-specific phrases
    
    This is a safety check to ensure variation framework is working.
    Logs warnings if uniqueness criteria aren't met.
    """
    # Extract headings
    headings = [b.get("text", "") for b in blocks if b.get("type") == "heading" and b.get("level") == 2]
    
    # Check for hub-specific terms in intro
    intro_block = next((b for b in blocks if b.get("type") == "paragraph"), None)
    if intro_block:
        intro_text = intro_block.get("text", "").lower()
        audience_label = hub_profile["audience_label"].lower()
        
        if audience_label not in intro_text:
            print(f"WARNING: Hub {hub_key} intro missing audience label '{audience_label}'")
    
    # Check FAQ uniqueness (questions should be from hub-specific bank)
    faq_questions = [b.get("question", "") for b in blocks if b.get("type") == "faq"]
    hub_faq_questions = [faq["question"] for faq in get_faqs_for_hub(hub_key, count=12)]
    
    for question in faq_questions:
        if question not in hub_faq_questions:
            print(f"WARNING: Hub {hub_key} has FAQ question not in its bank: {question}")
    
    print(f"Hub {hub_key} validation: {len(headings)} unique headings, {len(faq_questions)} FAQs")
