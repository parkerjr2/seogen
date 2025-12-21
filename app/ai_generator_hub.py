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
        blocks.extend(_generate_who_this_is_for_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_common_projects_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_process_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_compliance_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_service_areas_section(hub_key, hub_label, trade_name, data))
        blocks.extend(_generate_pricing_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_faqs_section(hub_label, trade_name, hub_key))
        blocks.append(_generate_cta_block(data, variant))
        
    elif variant == 1:
        # Variant 1: Benefit-first, reordered
        blocks.extend(_generate_common_projects_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_who_this_is_for_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_compliance_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_process_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_service_areas_section(hub_key, hub_label, trade_name, data))
        blocks.extend(_generate_faqs_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_pricing_section(hub_label, trade_name, hub_key))
        blocks.append(_generate_cta_block(data, variant))
        
    else:  # variant == 2
        # Variant 2: Authority-first, alternative order
        blocks.extend(_generate_process_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_compliance_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_who_this_is_for_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_common_projects_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_pricing_section(hub_label, trade_name, hub_key))
        blocks.extend(_generate_service_areas_section(hub_key, hub_label, trade_name, data))
        blocks.extend(_generate_faqs_section(hub_label, trade_name, hub_key))
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


def _generate_who_this_is_for_section(hub_label: str, trade_name: str, hub_key: str) -> List[Dict]:
    """Generate 'Who This Is For / Not For' section with hub-specific content."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": f"Who Benefits from {hub_label} {trade_name.title()} Services"
    })
    
    # Hub-specific content
    if hub_key == "residential":
        who_for_text = f"These services are designed for homeowners who need reliable {trade_name} work for their properties. "
        who_for_text += f"Whether you're dealing with safety concerns, planning a remodel, preparing to sell, or maintaining your home's systems, "
        who_for_text += f"we provide solutions that protect your family and property value. We understand the unique needs of residential properties "
        who_for_text += f"and work around your family's schedule with minimal disruption to daily life."
        
        not_for_text = f"Our residential services may not be the best fit for large commercial facilities, multi-unit apartment complexes, "
        not_for_text += f"or industrial-scale projects. For those needs, our commercial services team may be a better match."
        
    elif hub_key == "commercial":
        who_for_text = f"These services are designed for business owners, facility managers, and commercial property operators who need reliable {trade_name} work. "
        who_for_text += f"We understand that business downtime costs money, so we offer flexible scheduling including after-hours and weekend service. "
        who_for_text += f"Our team handles commercial permits, coordinates inspections, and provides documentation for insurance and compliance requirements. "
        who_for_text += f"We work with retail, office, industrial, and multi-tenant properties of all sizes."
        
        not_for_text = f"Our commercial services focus on business and multi-tenant properties. For single-family homes and residential properties, "
        not_for_text += f"our residential services team specializes in homeowner needs and may be a better fit."
        
    elif hub_key == "emergency":
        who_for_text = f"These services are for property owners facing urgent {trade_name} issues that require immediate attention. "
        who_for_text += f"If you're dealing with safety hazards, active property damage, or complete loss of essential services, our emergency response team "
        who_for_text += f"provides 24/7 availability. We triage situations quickly, stabilize immediate problems, and coordinate follow-up repairs. "
        who_for_text += f"Emergency service is available for both residential and commercial properties."
        
        not_for_text = f"Emergency service is for urgent situations only. For routine maintenance, planned upgrades, or non-urgent repairs, "
        not_for_text += f"our standard scheduling provides better value and allows for proper planning and preparation."
        
    else:
        # Generic fallback for other hub types
        who_for_text = f"These services are designed for property owners who need reliable {trade_name} work, "
        who_for_text += f"whether for routine maintenance, repairs, upgrades, or new installations. "
        who_for_text += f"We work with homeowners, business owners, property managers, and contractors who value "
        who_for_text += f"quality workmanship and professional service."
        
        not_for_text = f"Our services may not be the best fit for DIY projects, work requiring specialized licensing "
        not_for_text += f"we don't hold, or situations where immediate emergency response is needed but we're not available. "
        not_for_text += f"We'll always be honest about whether we're the right fit for your specific needs."
    
    blocks.append({
        "type": "paragraph",
        "text": who_for_text
    })
    
    blocks.append({
        "type": "paragraph",
        "text": not_for_text
    })
    
    return blocks


def _generate_common_projects_section(hub_label: str, trade_name: str, hub_key: str) -> List[Dict]:
    """Generate common projects section with hub-specific examples."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": f"Common {hub_label} {trade_name.title()} Projects"
    })
    
    # Hub-specific project examples
    if hub_key == "residential":
        projects_text = f"We handle a wide range of residential {trade_name} projects including whole-home system upgrades during remodels, "
        projects_text += f"safety inspections before buying or selling, emergency repairs affecting daily living, preventive maintenance to avoid breakdowns, "
        projects_text += f"and energy efficiency improvements. Each project is completed with respect for your home and family, using quality materials "
        projects_text += f"and clean work practices. We schedule around your routine and minimize disruption to your household."
        
    elif hub_key == "commercial":
        projects_text = f"We handle a wide range of commercial {trade_name} projects including tenant improvement work, code compliance upgrades for inspections, "
        projects_text += f"preventive maintenance contracts, emergency repairs during business hours, and system expansions for business growth. "
        projects_text += f"We understand the importance of minimizing downtime and offer flexible scheduling including after-hours and weekend service. "
        projects_text += f"All work is documented for insurance and compliance requirements."
        
    elif hub_key == "emergency":
        projects_text = f"We respond to urgent {trade_name} situations including safety hazards requiring immediate attention, system failures causing property damage, "
        projects_text += f"loss of essential services, storm or weather-related damage, and urgent repairs before inspections or closings. "
        projects_text += f"Our emergency response team provides 24/7 availability, rapid triage and assessment, and immediate stabilization before full repairs. "
        projects_text += f"We maintain mobile-equipped service vehicles for fast response."
        
    else:
        # Generic fallback
        projects_text = f"We handle a wide range of {hub_label.lower()} {trade_name} projects including system installations, "
        projects_text += f"repairs and troubleshooting, preventive maintenance, upgrades and improvements, code compliance work, "
        projects_text += f"and emergency services. Each project receives thorough assessment, clear communication about scope "
        projects_text += f"and costs, and professional execution from start to finish."
    
    blocks.append({
        "type": "paragraph",
        "text": projects_text
    })
    
    return blocks


def _generate_process_section(hub_label: str, trade_name: str, hub_key: str) -> List[Dict]:
    """Generate process/how we work section with hub-specific focus."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": f"Our {hub_label} Service Process"
    })
    
    # Hub-specific process emphasis
    if hub_key == "residential":
        process_text = f"We begin every residential project with a thorough assessment of your home's needs and current system condition. "
        process_text += f"You'll receive clear explanations in plain language about what work is needed, why it matters for your family's safety and comfort, "
        process_text += f"and what it will cost before we start. Our technicians are background-checked, respectful of your home, and work around your schedule. "
        process_text += f"We protect floors and furniture, clean up thoroughly, and ensure you're satisfied with the results."
        
    elif hub_key == "commercial":
        process_text = f"We begin every commercial project with a thorough assessment of your facility's needs and operational requirements. "
        process_text += f"You'll receive detailed documentation suitable for management approval, including scope, timeline, and cost breakdowns. "
        process_text += f"We coordinate with your team to schedule work during off-hours or low-traffic periods to minimize business disruption. "
        process_text += f"All work includes proper permits, inspection coordination, and compliance documentation for your records."
        
    elif hub_key == "emergency":
        process_text = f"Emergency service begins with rapid response and immediate triage of your situation. "
        process_text += f"Our technician will assess safety hazards, stabilize immediate problems, and explain what's needed for permanent repairs. "
        process_text += f"You'll receive clear communication about costs and options, even in urgent situations. We focus first on safety and preventing "
        process_text += f"further damage, then coordinate follow-up work for complete resolution."
        
    else:
        # Generic fallback
        process_text = f"We begin every project with a thorough assessment of your needs and current system condition. "
        process_text += f"You'll receive clear explanations of what work is needed, why it matters, and what it will cost "
        process_text += f"before we start. During the work, we maintain clean work areas, communicate progress, and ensure "
        process_text += f"you're satisfied with the results. All work is completed to code with proper documentation."
    
    blocks.append({
        "type": "paragraph",
        "text": process_text
    })
    
    return blocks


def _generate_compliance_section(hub_label: str, trade_name: str, hub_key: str) -> List[Dict]:
    """Generate compliance/permits/safety section with hub-specific focus."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": "Permits, Codes & Safety Standards"
    })
    
    # Hub-specific compliance emphasis
    if hub_key == "residential":
        compliance_text = f"All residential {trade_name} work complies with local building codes and homeowner safety standards. "
        compliance_text += f"We handle necessary permits and coordinate inspections to ensure your home improvements are properly documented. "
        compliance_text += f"This protects your family's safety, maintains your home's value, and prevents issues during future sales or refinancing. "
        compliance_text += f"We're familiar with residential code requirements and work with local inspectors regularly."
        
    elif hub_key == "commercial":
        compliance_text = f"All commercial {trade_name} work complies with commercial building codes, OSHA requirements, and industry-specific regulations. "
        compliance_text += f"We handle permit applications, coordinate inspections, and provide documentation for insurance and compliance audits. "
        compliance_text += f"Proper compliance protects your business from liability, satisfies insurance requirements, and ensures tenant and employee safety. "
        compliance_text += f"We maintain current knowledge of commercial code requirements and work with inspectors to ensure smooth approval processes."
        
    elif hub_key == "emergency":
        compliance_text = f"Even in emergency situations, we follow safety protocols and code requirements. "
        compliance_text += f"Emergency stabilization work focuses on immediate safety, with permanent repairs completed to full code compliance. "
        compliance_text += f"We'll explain what permits or inspections may be needed for permanent repairs and handle those requirements. "
        compliance_text += f"Our priority is making your property safe quickly while ensuring all work meets regulatory standards."
        
    else:
        # Generic fallback
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


def _generate_pricing_section(hub_label: str, trade_name: str, hub_key: str) -> List[Dict]:
    """Generate pricing factors section with hub-specific considerations."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": "Understanding Project Costs"
    })
    
    # Hub-specific pricing considerations
    if hub_key == "residential":
        pricing_text = f"Residential {trade_name} project costs vary based on your home's size, system age, materials selected, and work complexity. "
        pricing_text += f"We provide clear estimates in plain language before starting work, with no hidden fees or surprise charges. "
        pricing_text += f"Many homeowners appreciate financing options for larger projects, which we can discuss during your estimate. "
        pricing_text += f"We'll explain what affects pricing and present options at different price points when available."
        
    elif hub_key == "commercial":
        pricing_text = f"Commercial {trade_name} project costs depend on facility size, system complexity, downtime requirements, and compliance needs. "
        pricing_text += f"We provide detailed estimates suitable for management approval, breaking down labor, materials, permits, and timeline. "
        pricing_text += f"For ongoing needs, we offer maintenance contracts that provide predictable costs and priority service. "
        pricing_text += f"We understand business budgeting requirements and work within your financial planning constraints."
        
    elif hub_key == "emergency":
        pricing_text = f"Emergency {trade_name} service typically includes premium rates for immediate response, after-hours availability, and rapid dispatch. "
        pricing_text += f"We'll explain costs upfront so you can make informed decisions, even in urgent situations. "
        pricing_text += f"Emergency service focuses on immediate safety and damage prevention, with options for temporary stabilization or permanent repairs. "
        pricing_text += f"The cost of immediate service is often justified by preventing greater damage or safety hazards."
        
    else:
        # Generic fallback
        pricing_text = f"Project costs for {hub_label.lower()} {trade_name} work vary based on scope, materials, labor requirements, "
        pricing_text += f"and complexity. We provide detailed estimates before starting work, explaining what factors affect pricing. "
        pricing_text += f"Our goal is transparent pricing with no hidden fees or surprise charges. We'll discuss options at different "
        pricing_text += f"price points when available and help you make informed decisions about your project."
    
    blocks.append({
        "type": "paragraph",
        "text": pricing_text
    })
    
    return blocks


def _generate_faqs_section(hub_label: str, trade_name: str, hub_key: str) -> List[Dict]:
    """Generate FAQs section with hub-specific questions."""
    blocks = []
    
    blocks.append({
        "type": "heading",
        "level": 2,
        "text": "Frequently Asked Questions"
    })
    
    # Hub-specific FAQs
    if hub_key == "residential":
        faqs = [
            {
                "question": f"Do I need to be home during the service appointment?",
                "answer": f"For most residential services, we recommend having an adult present to provide access, answer questions about your home's history, and approve any additional work if needed. However, if you can't be home, we can often work with lockbox access or coordinate with a trusted neighbor."
            },
            {
                "question": f"Will you protect my floors and furniture during the work?",
                "answer": f"Yes, we take home protection seriously. Our technicians use drop cloths, floor protection, and shoe covers as standard practice. We'll move furniture if needed with your permission and always clean up our work area before leaving."
            },
            {
                "question": f"How do I know if my home needs repair or replacement?",
                "answer": f"During our inspection, we'll assess your system's age, condition, safety, and capacity for your home's needs. We'll explain what's working, what's not, and whether repairs will give you reliable service or if upgrading makes more sense long-term. You'll get honest recommendations with options at different price points."
            },
            {
                "question": f"Do you offer financing for larger home projects?",
                "answer": f"Yes, we offer financing options for qualifying homeowners on approved credit. This can make larger projects like whole-home upgrades or system replacements more manageable with monthly payments. We'll provide financing information during your estimate."
            },
            {
                "question": f"Will this work affect my home's resale value?",
                "answer": f"Properly permitted and code-compliant work typically maintains or increases home value. Outdated or non-compliant systems can be red flags during home inspections. We ensure all work meets current codes and provide documentation you can share with future buyers."
            },
            {
                "question": f"Can you work around my family's schedule?",
                "answer": f"We offer flexible scheduling to accommodate working families, including some evening and weekend appointments. During scheduling, let us know your constraints and preferences. We'll do our best to find a time that works for your household."
            }
        ]
    elif hub_key == "commercial":
        faqs = [
            {
                "question": f"Can you work outside of business hours to avoid disrupting operations?",
                "answer": f"Yes, we regularly schedule commercial work during evenings, weekends, and overnight hours to minimize impact on your business operations. Our technicians are experienced with after-hours work and understand the importance of having your facility ready for business."
            },
            {
                "question": f"Who handles the permit applications and inspection scheduling?",
                "answer": f"We handle all permit applications and coordinate required inspections as part of our commercial service. We're familiar with local commercial code requirements and inspection processes. You'll receive copies of all permits and inspection reports for your facility records."
            },
            {
                "question": f"Do you provide documentation for insurance and compliance audits?",
                "answer": f"Yes, we provide detailed documentation including work orders, inspection reports, permits, and compliance certificates. This documentation is essential for insurance requirements, safety audits, and regulatory compliance."
            },
            {
                "question": f"What's included in a commercial maintenance contract?",
                "answer": f"Commercial maintenance contracts typically include scheduled inspections, preventive maintenance, priority service response, detailed reporting, and often discounted rates on repairs. We'll customize a maintenance program based on your facility type and operational requirements."
            },
            {
                "question": f"How do you coordinate with other contractors during tenant improvements?",
                "answer": f"We're experienced working as part of construction teams on tenant improvement projects. We'll coordinate with general contractors, architects, and other trades to ensure our work integrates smoothly with the overall project schedule."
            },
            {
                "question": f"Do you carry commercial liability insurance and workers compensation?",
                "answer": f"Yes, we maintain comprehensive commercial liability insurance and workers compensation coverage. We can provide certificates of insurance for your facility management records or to meet your property owner's requirements."
            }
        ]
    elif hub_key == "emergency":
        faqs = [
            {
                "question": f"How quickly can someone get to my property for an emergency?",
                "answer": f"Emergency response times vary based on technician location, time of day, and current call volume. When you call, we'll provide an estimated arrival time based on real-time availability. We prioritize true emergencies involving safety hazards or significant property damage."
            },
            {
                "question": f"What qualifies as an emergency versus a regular service call?",
                "answer": f"Emergencies involve immediate safety hazards, active property damage, or complete loss of essential services. If you're unsure whether your situation is an emergency, call us and describe the problem. We'll help you determine the appropriate response level."
            },
            {
                "question": f"Will the emergency technician have the parts needed to fix my problem?",
                "answer": f"Our emergency service vehicles stock common parts for typical urgent repairs. However, some situations require specialized parts that must be ordered. In those cases, the technician will stabilize the situation and schedule a follow-up visit for permanent repairs."
            },
            {
                "question": f"How much do emergency services cost compared to regular appointments?",
                "answer": f"Emergency service typically includes premium rates for after-hours availability, rapid response, and immediate technician dispatch. We'll provide pricing information when you call so you can make an informed decision. In true emergencies involving safety or property protection, the cost of immediate service is often justified."
            },
            {
                "question": f"Do you provide emergency service on holidays and weekends?",
                "answer": f"Yes, emergencies don't follow business hours, so we provide emergency response 24/7 including holidays and weekends. Premium rates apply for after-hours and holiday service. When you call our emergency line, you'll reach a real person who can dispatch a technician."
            },
            {
                "question": f"What should I do while waiting for emergency service to arrive?",
                "answer": f"When you call, we'll provide specific safety instructions based on your situation. General guidance includes staying away from hazards, shutting off affected systems if safe to do so, and ensuring clear access for our technician. Never put yourself at risk trying to fix emergency situations."
            }
        ]
    else:
        # Generic fallback FAQs
        faqs = [
            {
                "question": f"What types of {hub_label.lower()} {trade_name} services do you provide?",
                "answer": f"We offer comprehensive {hub_label.lower()} {trade_name} services including installations, repairs, maintenance, upgrades, and emergency services. Our team has experience with both routine and complex projects, ensuring quality results regardless of scope."
            },
            {
                "question": "How quickly can you respond to service requests?",
                "answer": f"Response times vary based on the nature of the request and current schedule. For routine {hub_label.lower()} services, we typically schedule within a few days. Emergency situations receive priority response when available."
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
                "answer": f"We warranty our workmanship on {hub_label.lower()} {trade_name} installations and repairs. Specific warranty terms depend on the type of work and materials used. Equipment and parts typically carry manufacturer warranties."
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
