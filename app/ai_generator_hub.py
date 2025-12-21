"""
Service Hub Page Generation with 3 Deterministic Variants

Simplified hub generation with exactly 3 variants to reduce maintenance complexity
while maintaining content quality and avoiding doorway page patterns.

Variants are deterministically selected based on hub slug to ensure consistent
regeneration of the same hub produces the same output.
"""

import hashlib
from typing import List, Dict, Any
from app.models import GeneratePageResponse, PageData
from app.vertical_profiles import get_vertical_profile, get_trade_name


def generate_service_hub_content(generator, data: PageData) -> GeneratePageResponse:
    """
    Generate service hub page content with deterministic variant selection.
    
    Args:
        generator: The AIContentGenerator instance
        data: Page generation parameters with hub information
        
    Returns:
        Complete validated hub page content
    """
    vertical = data.vertical or "other"
    hub_key = data.hub_key or "residential"
    hub_slug = data.hub_slug or "services"
    
    # Deterministic variant selection based on slug
    variant = _get_variant_from_slug(hub_slug)
    
    # Debug log
    print(f"[HUB] slug={hub_slug} variant={variant}")
    
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
    
    # Generate content blocks using selected variant
    blocks = _generate_blocks_for_variant(
        variant=variant,
        generator=generator,
        data=data,
        vertical_profile=vertical_profile,
        h1_text=h1_text,
        hub_key=hub_key,
        hub_label=hub_label,
        trade_name=trade_name
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


def _generate_blocks_for_variant(
    variant: int,
    generator,
    data: PageData,
    vertical_profile: Dict,
    h1_text: str,
    hub_key: str,
    hub_label: str,
    trade_name: str
) -> List[Dict]:
    """
    Generate content blocks according to the selected variant.
    
    Variant 0: Problem-first intro, Standard order, Direct CTA
    Variant 1: Benefit-first intro, Reordered sections, Value CTA
    Variant 2: Authority-first intro, Alternative order, Action CTA
    """
    blocks = []
    
    # Hero section (H1)
    blocks.append({
        "type": "heading",
        "level": 1,
        "text": h1_text
    })
    
    # Hero intro paragraph - varies by variant
    intro_text = _generate_intro_for_variant(variant, hub_label, trade_name, data)
    blocks.append({
        "type": "paragraph",
        "text": intro_text
    })
    
    # Generate sections in variant-specific order
    if variant == 0:
        # Variant 0: Problem-first, standard order
        blocks.extend(_generate_who_this_is_for_section(hub_label, trade_name))
        blocks.extend(_generate_common_projects_section(hub_label, trade_name))
        blocks.extend(_generate_process_section(hub_label, trade_name))
        blocks.extend(_generate_compliance_section(hub_label, trade_name))
        blocks.extend(_generate_service_areas_section(hub_key, hub_label, trade_name, data))
        blocks.extend(_generate_pricing_section(hub_label, trade_name))
        blocks.extend(_generate_faqs_section(hub_label, trade_name))
        blocks.append(_generate_cta_block(data, variant))
        
    elif variant == 1:
        # Variant 1: Benefit-first, reordered
        blocks.extend(_generate_common_projects_section(hub_label, trade_name))
        blocks.extend(_generate_who_this_is_for_section(hub_label, trade_name))
        blocks.extend(_generate_compliance_section(hub_label, trade_name))
        blocks.extend(_generate_process_section(hub_label, trade_name))
        blocks.extend(_generate_service_areas_section(hub_key, hub_label, trade_name, data))
        blocks.extend(_generate_faqs_section(hub_label, trade_name))
        blocks.extend(_generate_pricing_section(hub_label, trade_name))
        blocks.append(_generate_cta_block(data, variant))
        
    else:  # variant == 2
        # Variant 2: Authority-first, alternative order
        blocks.extend(_generate_process_section(hub_label, trade_name))
        blocks.extend(_generate_compliance_section(hub_label, trade_name))
        blocks.extend(_generate_who_this_is_for_section(hub_label, trade_name))
        blocks.extend(_generate_common_projects_section(hub_label, trade_name))
        blocks.extend(_generate_pricing_section(hub_label, trade_name))
        blocks.extend(_generate_service_areas_section(hub_key, hub_label, trade_name, data))
        blocks.extend(_generate_faqs_section(hub_label, trade_name))
        blocks.append(_generate_cta_block(data, variant))
    
    return blocks


def _generate_intro_for_variant(variant: int, hub_label: str, trade_name: str, data: PageData) -> str:
    """Generate intro paragraph based on variant style."""
    
    if variant == 0:
        # Problem-first
        intro = f"Many property owners face challenges with {trade_name} systems that require professional attention. "
        intro += f"Our {hub_label.lower()} {trade_name} services address these issues with experienced technicians, "
        intro += f"quality materials, and proven methods. We understand the importance of reliable service and work "
        intro += f"to ensure your systems function properly and safely."
        
    elif variant == 1:
        # Benefit-first
        intro = f"Professional {hub_label.lower()} {trade_name} services provide peace of mind and long-term value. "
        intro += f"Our team delivers quality workmanship, clear communication, and solutions tailored to your needs. "
        intro += f"Whether you need routine maintenance, repairs, or new installations, we bring expertise and "
        intro += f"reliability to every project."
        
    else:  # variant == 2
        # Authority-first
        intro = f"With extensive experience in {hub_label.lower()} {trade_name} services, our team has the knowledge "
        intro += f"and skills to handle projects of any complexity. We stay current with industry standards, use "
        intro += f"quality materials, and follow best practices to deliver results that meet or exceed expectations. "
        intro += f"Our reputation is built on consistent quality and customer satisfaction."
    
    return intro


def _generate_who_this_is_for_section(hub_label: str, trade_name: str) -> List[Dict]:
    """Generate 'Who This Is For / Not For' section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": f"Who Benefits from {hub_label} {trade_name.title()} Services"
    })
    
    who_for_text = f"These services are designed for property owners who need reliable {trade_name} work, "
    who_for_text += f"whether for routine maintenance, repairs, upgrades, or new installations. "
    who_for_text += f"We work with homeowners, business owners, property managers, and contractors who value "
    who_for_text += f"quality workmanship and professional service."
    
    blocks.append({
        "type": "paragraph",
        "text": who_for_text
    })
    
    not_for_text = f"Our services may not be the best fit for DIY projects, work requiring specialized licensing "
    not_for_text += f"we don't hold, or situations where immediate emergency response is needed but we're not available. "
    not_for_text += f"We'll always be honest about whether we're the right fit for your specific needs."
    
    blocks.append({
        "type": "paragraph",
        "text": not_for_text
    })
    
    return blocks


def _generate_common_projects_section(hub_label: str, trade_name: str) -> List[Dict]:
    """Generate common projects section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": f"Common {hub_label} {trade_name.title()} Projects"
    })
    
    projects_text = f"We handle a wide range of {hub_label.lower()} {trade_name} projects including system installations, "
    projects_text += f"repairs and troubleshooting, preventive maintenance, upgrades and improvements, code compliance work, "
    projects_text += f"and emergency services. Each project receives thorough assessment, clear communication about scope "
    projects_text += f"and costs, and professional execution from start to finish."
    
    blocks.append({
        "type": "paragraph",
        "text": projects_text
    })
    
    return blocks


def _generate_process_section(hub_label: str, trade_name: str) -> List[Dict]:
    """Generate process/how we work section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": f"Our {hub_label} Service Process"
    })
    
    process_text = f"We begin every project with a thorough assessment of your needs and current system condition. "
    process_text += f"You'll receive clear explanations of what work is needed, why it matters, and what it will cost "
    process_text += f"before we start. During the work, we maintain clean work areas, communicate progress, and ensure "
    process_text += f"you're satisfied with the results. All work is completed to code with proper documentation."
    
    blocks.append({
        "type": "paragraph",
        "text": process_text
    })
    
    return blocks


def _generate_compliance_section(hub_label: str, trade_name: str) -> List[Dict]:
    """Generate compliance/permits/safety section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": "Permits, Codes & Safety Standards"
    })
    
    compliance_text = f"All {hub_label.lower()} {trade_name} work complies with applicable building codes and safety standards. "
    compliance_text += f"We handle necessary permits and coordinate required inspections to ensure your project meets all "
    compliance_text += f"regulatory requirements. Proper compliance protects you, maintains property value, and ensures "
    compliance_text += f"work quality. We're familiar with local code requirements and inspection processes."
    
    blocks.append({
        "type": "paragraph",
        "text": compliance_text
    })
    
    return blocks


def _generate_service_areas_section(hub_key: str, hub_label: str, trade_name: str, data: PageData) -> List[Dict]:
    """Generate service areas section with contextual intro and city links shortcode."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": "Primary Service Areas"
    })
    
    # Contextual introduction
    service_area = data.service_area_label or "the area"
    context_text = f"We provide {hub_label.lower()} {trade_name} services throughout {service_area}. "
    context_text += f"Our team is familiar with local building codes, common property challenges, and inspection "
    context_text += f"requirements in the communities we serve. We maintain service vehicles and inventory to respond "
    context_text += f"efficiently to service calls across our coverage area."
    
    blocks.append({
        "type": "paragraph",
        "text": context_text
    })
    
    # Shortcode paragraph
    shortcode_text = f"Explore our {hub_label.lower()} {trade_name} services in your area. [seogen_service_hub_city_links hub_key=\"{hub_key}\" limit=\"6\"]"
    
    blocks.append({
        "type": "paragraph",
        "text": shortcode_text
    })
    
    return blocks


def _generate_pricing_section(hub_label: str, trade_name: str) -> List[Dict]:
    """Generate pricing factors section."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": "Understanding Project Costs"
    })
    
    pricing_text = f"Project costs for {hub_label.lower()} {trade_name} work vary based on scope, materials, labor requirements, "
    pricing_text += f"and complexity. We provide detailed estimates before starting work, explaining what factors affect pricing. "
    pricing_text += f"Our goal is transparent pricing with no hidden fees or surprise charges. We'll discuss options at different "
    pricing_text += f"price points when available and help you make informed decisions about your project."
    
    blocks.append({
        "type": "paragraph",
        "text": pricing_text
    })
    
    return blocks


def _generate_faqs_section(hub_label: str, trade_name: str) -> List[Dict]:
    """Generate FAQs section with common questions."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": "Frequently Asked Questions"
    })
    
    # Generate 6 common FAQs
    faqs = [
        {
            "question": f"What types of {hub_label.lower()} {trade_name} services do you provide?",
            "answer": f"We offer comprehensive {hub_label.lower()} {trade_name} services including installations, repairs, maintenance, upgrades, and emergency services. Our team has experience with both routine and complex projects, ensuring quality results regardless of scope."
        },
        {
            "question": "How quickly can you respond to service requests?",
            "answer": f"Response times vary based on the nature of the request and current schedule. For routine {hub_label.lower()} services, we typically schedule within a few days. Emergency situations receive priority response when available. We'll provide an estimated timeframe when you contact us."
        },
        {
            "question": "Do you provide estimates before starting work?",
            "answer": f"Yes, we provide detailed estimates for all {hub_label.lower()} {trade_name} projects. Our estimates include scope of work, materials, labor, and timeline with transparent pricing. You'll approve the estimate before we begin any work."
        },
        {
            "question": "Are your technicians licensed and insured?",
            "answer": f"Yes, our {trade_name} technicians hold appropriate licenses and we maintain comprehensive insurance coverage. We follow industry best practices and stay current with code requirements to ensure quality and safety on every project."
        },
        {
            "question": "What areas do you serve?",
            "answer": f"We provide {hub_label.lower()} {trade_name} services throughout our coverage area. Our team is familiar with local codes and requirements in the communities we serve. Contact us to confirm service availability for your specific location."
        },
        {
            "question": "What warranty comes with your work?",
            "answer": f"We warranty our workmanship on {hub_label.lower()} {trade_name} installations and repairs. Specific warranty terms depend on the type of work and materials used. Equipment and parts typically carry manufacturer warranties. We'll explain all applicable warranties when providing your estimate."
        }
    ]
    
    for faq in faqs:
        blocks.append({
            "type": "faq",
            "question": faq["question"],
            "answer": faq["answer"]
        })
    
    return blocks


def _generate_cta_block(data: PageData, variant: int) -> Dict:
    """Generate CTA block with variant-specific phrasing."""
    
    if variant == 0:
        # Direct CTA
        cta_text = data.cta_text or "Get Started Today"
    elif variant == 1:
        # Value CTA
        cta_text = data.cta_text or "Request Your Free Estimate"
    else:  # variant == 2
        # Action CTA
        cta_text = data.cta_text or "Schedule Your Service"
    
    return {
        "type": "cta",
        "text": cta_text,
        "phone": data.phone or ""
    }
