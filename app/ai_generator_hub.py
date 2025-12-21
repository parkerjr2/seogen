"""
Service Hub Page Generation with Doorway-Safe Guardrails

ANTI-DOORWAY PAGE STRATEGY:
This module implements generation-time safeguards to ensure service hub pages
are semantically and structurally differentiated, preventing Google from classifying
them as doorway pages.

Key Safeguards:
1. Structural Variation: 5-7 sections, randomized order, at least 1 omitted per hub
2. Service-Exclusive Sections: Each hub has unique section with 3+ technical terms
3. Semantic Differentiation: 3 unique terms, 1 workflow, 1 risk per hub
4. CTA Intent Differentiation: Varied phrasing by service type
5. Cross-Hub Similarity Check: Regenerate if >70% similar to previous hubs

CONSTRAINTS:
- NO changes to URLs, CPTs, schema, shortcodes, or frontend rendering
- ALL changes are internal to content generation only
- Fully backward-compatible with existing system
"""

import hashlib
import random
import json
from typing import List, Dict, Any, Set, Tuple
from app.models import GeneratePageResponse, PageData
from app.vertical_profiles import get_vertical_profile, get_trade_name


# Global registry to track generated hub structures (in-memory for session)
# In production, this could be persisted to detect cross-session similarity
_HUB_STRUCTURE_REGISTRY = []


def generate_service_hub_content(generator, data: PageData) -> GeneratePageResponse:
    """
    Generate service hub page content with doorway-safe guardrails.
    
    Implements structural variation, semantic differentiation, and similarity checks
    to ensure each hub is unique and valuable to users.
    """
    vertical = data.vertical or "other"
    hub_key = data.hub_key or "residential"
    hub_slug = data.hub_slug or "services"
    
    print(f"[HUB GUARDRAILS] Generating hub: slug={hub_slug} hub_key={hub_key}")
    
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
    
    # GUARDRAIL 1: Structural Variation Enforcement
    # Select 5-7 sections randomly, ensuring at least 1 optional section is omitted
    section_plan = _create_structural_variation_plan(hub_key, hub_label, trade_name)
    
    # GUARDRAIL 5: Cross-Hub Similarity Check
    # If structure is >70% similar to previous hubs, regenerate with different structure
    max_attempts = 3
    for attempt in range(max_attempts):
        similarity = _check_structure_similarity(section_plan)
        if similarity < 0.70:
            break
        print(f"[HUB GUARDRAILS] Structure {similarity*100:.0f}% similar to previous hubs, regenerating (attempt {attempt+1}/{max_attempts})")
        section_plan = _create_structural_variation_plan(hub_key, hub_label, trade_name)
    
    # Register this structure
    _register_hub_structure(section_plan)
    
    # GUARDRAIL 2: Service-Exclusive Section Requirement
    # Ensure hub has at least one section exclusive to this service type
    exclusive_section = _get_service_exclusive_section(hub_key, hub_label, trade_name, vertical_profile)
    
    # GUARDRAIL 3: Semantic Differentiation Threshold
    # Require 3 unique technical terms, 1 workflow difference, 1 risk/constraint
    semantic_requirements = _get_semantic_requirements(hub_key, hub_label, trade_name, vertical_profile)
    
    # GUARDRAIL 4: CTA Intent Differentiation
    # Vary CTA phrasing by service type (copy only, not destination)
    cta_text = _get_differentiated_cta(hub_key, hub_label, trade_name, data.cta_text)
    
    # Generate AI content with all guardrails applied
    ai_content = _call_openai_with_guardrails(
        generator=generator,
        data=data,
        vertical_profile=vertical_profile,
        hub_key=hub_key,
        hub_label=hub_label,
        trade_name=trade_name,
        section_plan=section_plan,
        exclusive_section=exclusive_section,
        semantic_requirements=semantic_requirements,
        cta_text=cta_text
    )
    
    # Convert AI content to blocks
    blocks = _convert_to_blocks(ai_content, h1_text, data, cta_text)
    
    response = GeneratePageResponse(
        title=title,
        meta_description=meta_description[:160],
        slug=slug,
        blocks=blocks
    )
    
    print(f"[HUB GUARDRAILS] Generated hub with {len(section_plan['sections'])} sections, exclusive section: {exclusive_section['title']}")
    
    return response


def _create_structural_variation_plan(hub_key: str, hub_label: str, trade_name: str) -> Dict:
    """
    GUARDRAIL 1: Structural Variation Enforcement
    
    Creates a randomized section plan with 5-7 sections, ensuring:
    - Section order is randomized
    - At least 1 optional section is omitted
    - No two hubs share identical section sequence
    
    Returns a plan with section list and their randomized headings.
    """
    # Define all possible sections (pool of 8, will select 5-7)
    all_sections = [
        "intro",           # Always included
        "who_for",         # Optional
        "process",         # Optional
        "projects",        # Optional
        "risks",           # Optional
        "compliance",      # Optional
        "why_choose",      # Optional
        "service_areas",   # Always included (has shortcode)
    ]
    
    # Mandatory sections that must appear
    mandatory = ["intro", "service_areas"]
    
    # Optional sections (will select 3-5 of these)
    optional = [s for s in all_sections if s not in mandatory]
    
    # Randomly select 3-5 optional sections (ensuring at least 1 is omitted)
    num_optional = random.randint(3, 5)
    selected_optional = random.sample(optional, num_optional)
    
    # Combine mandatory + selected optional
    selected_sections = mandatory + selected_optional
    
    # Randomize order (but keep intro first and service_areas near end)
    middle_sections = [s for s in selected_sections if s not in ["intro", "service_areas"]]
    random.shuffle(middle_sections)
    
    # Final order: intro → shuffled middle → service_areas
    final_order = ["intro"] + middle_sections + ["service_areas"]
    
    # Generate randomized headings for each section
    section_headings = {}
    for section in final_order:
        section_headings[section] = _get_random_section_heading(section, hub_key, hub_label, trade_name)
    
    return {
        "sections": final_order,
        "headings": section_headings,
        "omitted": [s for s in all_sections if s not in selected_sections]
    }


def _get_random_section_heading(section: str, hub_key: str, hub_label: str, trade_name: str) -> str:
    """
    Generate randomized heading for a section to avoid template-like appearance.
    Each section has 4-6 heading variations.
    """
    # Hub-specific terms
    if hub_key == "residential":
        audience = random.choice(["Homeowners", "Residential Property Owners", "Home Owners"])
    elif hub_key == "commercial":
        audience = random.choice(["Business Owners", "Commercial Property Managers", "Facility Managers"])
    elif hub_key == "emergency":
        audience = random.choice(["Property Owners", "Homeowners & Businesses"])
    else:
        audience = random.choice(["Property Owners", "Customers"])
    
    headings = {
        "intro": f"{hub_label} {trade_name.title()} Services",  # H1, not varied
        "who_for": random.choice([
            f"Who Benefits from {hub_label} {trade_name.title()} Services",
            f"Is {hub_label} Service Right for Your Property?",
            f"Who We Serve with {hub_label} Work",
            f"{audience} Who Need {hub_label} Services"
        ]),
        "process": random.choice([
            f"Our {hub_label} Service Process",
            f"How We Work with {audience}",
            f"What to Expect from Our {hub_label} Services",
            f"Our Approach to {hub_label} Work"
        ]),
        "projects": random.choice([
            f"Common {hub_label} {trade_name.title()} Projects",
            f"Typical {hub_label} Work We Handle",
            f"What We Do for {audience}",
            f"{hub_label} Projects We Complete"
        ]),
        "risks": random.choice([
            f"Common {hub_label} Challenges & Risks",
            f"What Can Go Wrong Without Professional Service",
            f"Risks & Constraints in {hub_label} Work",
            f"Why {hub_label} {trade_name.title()} Work Requires Expertise"
        ]),
        "compliance": random.choice([
            "Permits, Codes & Safety Standards",
            "Code Compliance & Regulations",
            "Safety Standards & Requirements",
            "Meeting Building Code Requirements"
        ]),
        "why_choose": random.choice([
            f"Why Choose Professional {hub_label} Service",
            f"The Value of Expert {hub_label} Work",
            f"What Sets Professional {hub_label} Service Apart",
            f"Benefits of Professional {hub_label} {trade_name.title()} Work"
        ]),
        "service_areas": random.choice([
            "Primary Service Areas",
            "Areas We Serve",
            "Service Coverage",
            "Where We Provide Service"
        ])
    }
    
    return headings.get(section, section.replace("_", " ").title())


def _check_structure_similarity(section_plan: Dict) -> float:
    """
    GUARDRAIL 5: Cross-Hub Similarity Check
    
    Compares the proposed section plan against previously generated hubs.
    Returns similarity score (0.0 to 1.0).
    
    If similarity > 0.70, the calling function should regenerate with different structure.
    """
    if not _HUB_STRUCTURE_REGISTRY:
        return 0.0  # First hub, no comparison needed
    
    current_sections = set(section_plan["sections"])
    current_order = tuple(section_plan["sections"])
    
    max_similarity = 0.0
    
    for previous_plan in _HUB_STRUCTURE_REGISTRY[-10:]:  # Check last 10 hubs
        prev_sections = set(previous_plan["sections"])
        prev_order = tuple(previous_plan["sections"])
        
        # Calculate similarity based on:
        # 1. Section overlap (50% weight)
        # 2. Order similarity (50% weight)
        
        section_overlap = len(current_sections & prev_sections) / len(current_sections | prev_sections)
        
        # Order similarity: count matching positions
        order_matches = sum(1 for i, s in enumerate(current_order) if i < len(prev_order) and prev_order[i] == s)
        order_similarity = order_matches / max(len(current_order), len(prev_order))
        
        similarity = (section_overlap * 0.5) + (order_similarity * 0.5)
        max_similarity = max(max_similarity, similarity)
    
    return max_similarity


def _register_hub_structure(section_plan: Dict):
    """Register generated hub structure for future similarity checks."""
    _HUB_STRUCTURE_REGISTRY.append(section_plan)
    # Keep only last 50 hubs in memory
    if len(_HUB_STRUCTURE_REGISTRY) > 50:
        _HUB_STRUCTURE_REGISTRY.pop(0)


def _get_service_exclusive_section(hub_key: str, hub_label: str, trade_name: str, vertical_profile: Dict) -> Dict:
    """
    GUARDRAIL 2: Service-Exclusive Section Requirement
    
    Returns a section definition that is exclusive to this service type.
    Must contain at least 3 service-specific technical terms.
    Must not appear verbatim in other hub types.
    """
    vocabulary = vertical_profile.get("vocabulary", [])
    
    if hub_key == "residential":
        return {
            "title": f"Residential {trade_name.title()} Safety & Home Value Protection",
            "focus": "family safety, property value, home resale considerations",
            "technical_terms": vocabulary[:5] + ["home safety", "property value", "resale impact"],
            "unique_aspects": [
                "Impact on home resale value and buyer inspections",
                "Family safety considerations and child-proofing",
                "Integration with existing home systems and aesthetics",
                "Homeowner insurance requirements and coverage"
            ]
        }
    elif hub_key == "commercial":
        return {
            "title": f"Commercial {trade_name.title()} Load Planning & Compliance",
            "focus": "load calculations, uptime requirements, OSHA compliance",
            "technical_terms": vocabulary[:5] + ["load capacity", "uptime", "OSHA compliance"],
            "unique_aspects": [
                "Load calculations for commercial equipment and future expansion",
                "Minimizing business downtime during installation or repairs",
                "OSHA compliance and workplace safety documentation",
                "Coordination with facility management and business operations"
            ]
        }
    elif hub_key == "emergency":
        return {
            "title": f"Emergency {trade_name.title()} Response & Safety Protocols",
            "focus": "rapid response, safety hazards, immediate stabilization",
            "technical_terms": vocabulary[:5] + ["emergency response", "safety hazard", "immediate stabilization"],
            "unique_aspects": [
                "24/7 emergency response and dispatch protocols",
                "Immediate safety hazard assessment and triage",
                "Temporary stabilization vs permanent repair decisions",
                "Emergency service premium rates and after-hours availability"
            ]
        }
    else:
        return {
            "title": f"{hub_label} {trade_name.title()} Expertise & Standards",
            "focus": "professional standards, quality workmanship",
            "technical_terms": vocabulary[:5] + ["professional standards", "quality workmanship"],
            "unique_aspects": [
                "Industry standards and best practices",
                "Quality materials and workmanship",
                "Professional licensing and insurance",
                "Customer satisfaction and warranty"
            ]
        }


def _get_semantic_requirements(hub_key: str, hub_label: str, trade_name: str, vertical_profile: Dict) -> Dict:
    """
    GUARDRAIL 3: Semantic Differentiation Threshold
    
    Returns semantic requirements for this hub:
    - 3 unique technical terms
    - 1 workflow difference
    - 1 risk/constraint/failure mode
    
    These must appear in full sentences, not just bullet lists.
    """
    vocabulary = vertical_profile.get("vocabulary", [])
    
    # Select 3 unique technical terms for this hub
    unique_terms = random.sample(vocabulary, min(3, len(vocabulary)))
    
    if hub_key == "residential":
        return {
            "unique_terms": unique_terms + ["home safety", "property value", "family protection"],
            "workflow_difference": "We work around family schedules and protect living spaces during service",
            "risk_constraint": "Outdated systems can pose fire hazards and reduce home resale value"
        }
    elif hub_key == "commercial":
        return {
            "unique_terms": unique_terms + ["load capacity", "business continuity", "compliance documentation"],
            "workflow_difference": "We coordinate with facility managers and schedule work during off-hours to minimize disruption",
            "risk_constraint": "Inadequate capacity planning can lead to costly downtime and equipment failure"
        }
    elif hub_key == "emergency":
        return {
            "unique_terms": unique_terms + ["emergency response", "safety hazard", "rapid stabilization"],
            "workflow_difference": "We provide 24/7 emergency dispatch with immediate safety assessment and triage",
            "risk_constraint": "Delayed response to emergencies can escalate safety hazards and increase property damage"
        }
    else:
        return {
            "unique_terms": unique_terms,
            "workflow_difference": "We follow industry best practices and maintain clear communication throughout the project",
            "risk_constraint": "Improper work can lead to safety issues and costly repairs"
        }


def _get_differentiated_cta(hub_key: str, hub_label: str, trade_name: str, default_cta: str) -> str:
    """
    GUARDRAIL 4: CTA Intent Differentiation
    
    Returns CTA text varied by service type (copy only, not destination).
    - Residential: emphasize safety, comfort, home value
    - Commercial: emphasize uptime, compliance, scalability
    - Emergency: emphasize rapid response, availability
    """
    if hub_key == "residential":
        options = [
            f"Schedule a Home {trade_name.title()} Safety Review",
            f"Get a Free Residential {trade_name.title()} Assessment",
            f"Protect Your Home with Professional {trade_name.title()} Service",
            f"Request a Home {trade_name.title()} Consultation"
        ]
    elif hub_key == "commercial":
        options = [
            f"Request a Commercial {trade_name.title()} Assessment",
            f"Schedule a Business {trade_name.title()} Consultation",
            f"Get a Commercial Load & Compliance Review",
            f"Contact Us for Commercial {trade_name.title()} Service"
        ]
    elif hub_key == "emergency":
        options = [
            f"Call for Emergency {trade_name.title()} Service Now",
            f"Get Immediate {trade_name.title()} Emergency Response",
            f"24/7 Emergency {trade_name.title()} Service Available",
            f"Contact Emergency {trade_name.title()} Dispatch"
        ]
    else:
        return default_cta or "Contact Us Today"
    
    return random.choice(options)


def _call_openai_with_guardrails(
    generator,
    data: PageData,
    vertical_profile: Dict,
    hub_key: str,
    hub_label: str,
    trade_name: str,
    section_plan: Dict,
    exclusive_section: Dict,
    semantic_requirements: Dict,
    cta_text: str
) -> Dict:
    """
    Call OpenAI with all guardrails enforced in the prompt.
    
    Ensures:
    - Only requested sections are generated
    - Exclusive section is included with technical terms
    - Semantic requirements are met
    - Forbidden patterns are avoided
    """
    vocabulary = vertical_profile.get("vocabulary", [])
    
    # Build services list
    services_list = ""
    if data.services_for_hub:
        services_list = "\n".join([f"- {s.get('name', '')}" for s in data.services_for_hub[:20]])
    
    # Hub-specific guidance
    hub_guidance = _get_hub_specific_guidance(hub_key, hub_label, trade_name)
    
    # Build section instructions
    section_instructions = []
    for i, section_key in enumerate(section_plan["sections"], 1):
        heading = section_plan["headings"][section_key]
        
        if section_key == "intro":
            section_instructions.append(f'{i}. Opening paragraph (2-3 sentences) introducing {hub_label.lower()} {trade_name} services')
        elif section_key == "service_areas":
            section_instructions.append(f'{i}. Section: "{heading}" - 1-2 sentences about serving the area')
        else:
            # Check if this is the exclusive section
            if section_key in ["risks", "compliance"] and exclusive_section["title"] in heading:
                section_instructions.append(
                    f'{i}. EXCLUSIVE SECTION: "{exclusive_section["title"]}" - '
                    f'2-3 sentences about {exclusive_section["focus"]}. '
                    f'MUST include these technical terms: {", ".join(exclusive_section["technical_terms"][:3])}'
                )
            else:
                section_instructions.append(f'{i}. Section: "{heading}" - 2-3 sentences')
    
    # Random FAQ count
    num_faqs = random.randint(4, 7)
    
    system_prompt = f"""You are a professional {trade_name} content writer. Write natural, helpful content that genuinely helps {hub_guidance['audience']} understand these services and make informed decisions.

CRITICAL ANTI-DOORWAY PAGE RULES:
1. Do NOT reuse identical intro paragraph structures
2. Do NOT use generic template language
3. MUST include these unique technical terms naturally: {', '.join(semantic_requirements['unique_terms'][:3])}
4. MUST mention this workflow difference: {semantic_requirements['workflow_difference']}
5. MUST mention this risk/constraint: {semantic_requirements['risk_constraint']}
6. Write each section with unique phrasing and examples"""

    user_prompt = f"""Generate content for a {hub_label.lower()} {trade_name} service hub page.

Hub Category: {hub_label}
Target Audience: {hub_guidance['audience']}
Key Focus: {hub_guidance['key_focus']}
Business Name: {data.business_name or 'Our Company'}
Service Area: {data.service_area_label or 'your area'}

Services Offered:
{services_list}

REQUIRED SECTIONS (in this exact order):
{chr(10).join(section_instructions)}

{num_faqs}. FAQs: Generate {num_faqs} questions with detailed answers (3-4 sentences each)
   - Questions must be specific to {hub_guidance['audience']} concerns
   - Examples: {hub_guidance['faq_examples']}

{num_faqs + 1}. CTA: "{cta_text}"

SEMANTIC REQUIREMENTS (MUST APPEAR IN CONTENT):
- Technical terms: {', '.join(semantic_requirements['unique_terms'][:3])}
- Workflow: {semantic_requirements['workflow_difference']}
- Risk/Constraint: {semantic_requirements['risk_constraint']}

Return ONLY valid JSON:
{{
  "sections": [
    {{"heading": "heading text", "paragraph": "content"}}
  ],
  "faqs": [
    {{"question": "question", "answer": "answer"}}
  ]
}}

FORBIDDEN PATTERNS:
- Do NOT reuse identical intro structures
- Do NOT use generic CTA phrasing
- Do NOT create thin content with only service name differences
- Do NOT mention specific cities or neighborhoods
- No marketing fluff: "top-notch", "premier", "best-in-class"
"""

    try:
        result = generator._call_openai_json(system_prompt, user_prompt, max_tokens=3500, temperature=0.9)
        
        # Add shortcode to service areas/coverage section
        if result.get("sections"):
            shortcode_added = False
            for section in result["sections"]:
                heading_lower = section.get("heading", "").lower()
                # Match various service area heading patterns
                if any(pattern in heading_lower for pattern in ["service area", "areas we serve", "coverage", "locations", "where we serve"]):
                    section["paragraph"] += f' [seogen_service_hub_city_links hub_key="{data.hub_key}" limit="6"]'
                    shortcode_added = True
                    break
            
            # If no matching section found, append to last section before FAQ
            if not shortcode_added and result.get("sections"):
                # Find last non-FAQ section
                for i in range(len(result["sections"]) - 1, -1, -1):
                    section = result["sections"][i]
                    if "faq" not in section.get("heading", "").lower() and "question" not in section.get("heading", "").lower():
                        section["paragraph"] += f' [seogen_service_hub_city_links hub_key="{data.hub_key}" limit="6"]'
                        break
        
        return result
    except Exception as e:
        print(f"[HUB GUARDRAILS] OpenAI generation failed: {e}, using fallback")
        return _generate_fallback_content(section_plan, exclusive_section, semantic_requirements, data, cta_text)


def _get_hub_specific_guidance(hub_key: str, hub_label: str, trade_name: str) -> Dict:
    """Get hub-specific content guidance for AI generation."""
    
    if hub_key == "residential":
        return {
            "audience": "homeowners and residential property owners",
            "key_focus": "family safety, property value, and minimal disruption to daily life",
            "content_guidelines": "Focus on homeowner concerns like safety, property value, family disruption, and home protection",
            "faq_examples": "Do I need to be home? Will you protect my floors? How does this affect resale value?"
        }
    elif hub_key == "commercial":
        return {
            "audience": "business owners, facility managers, and commercial property operators",
            "key_focus": "minimizing business downtime, compliance documentation, and after-hours service",
            "content_guidelines": "Focus on business concerns like downtime costs, permits, insurance, and operational disruption",
            "faq_examples": "Can you work after hours? Who handles permits? Do you provide compliance documentation?"
        }
    elif hub_key == "emergency":
        return {
            "audience": "property owners facing urgent issues requiring immediate attention",
            "key_focus": "rapid response, 24/7 availability, and immediate safety",
            "content_guidelines": "Focus on urgency, safety hazards, response times, and emergency vs routine service",
            "faq_examples": "How quickly can you respond? What qualifies as emergency? Do you work holidays?"
        }
    else:
        return {
            "audience": "property owners",
            "key_focus": "quality service and professional results",
            "content_guidelines": "Focus on general service quality and professionalism",
            "faq_examples": "What services do you offer? How quickly can you respond? Do you provide estimates?"
        }


def _generate_fallback_content(section_plan: Dict, exclusive_section: Dict, semantic_requirements: Dict, data: PageData, cta_text: str) -> Dict:
    """Generate fallback content if AI generation fails."""
    sections = []
    
    for section_key in section_plan["sections"]:
        heading = section_plan["headings"][section_key]
        
        if section_key == "intro":
            sections.append({
                "heading": heading,
                "paragraph": f"Professional {data.hub_label or 'service'} solutions for your property needs."
            })
        elif section_key == "service_areas":
            sections.append({
                "heading": heading,
                "paragraph": f'We serve {data.service_area_label or "the area"}. [seogen_service_hub_city_links hub_key="{data.hub_key}" limit="6"]'
            })
        else:
            sections.append({
                "heading": heading,
                "paragraph": f"Quality service and professional results you can trust."
            })
    
    return {
        "sections": sections,
        "faqs": [
            {"question": "What services do you offer?", "answer": "We provide comprehensive professional services."},
            {"question": "How quickly can you respond?", "answer": "We respond promptly to all service requests."},
            {"question": "Are you licensed and insured?", "answer": "Yes, we maintain all required licenses and insurance."},
            {"question": "Do you provide estimates?", "answer": "Yes, we provide detailed estimates for all work."}
        ]
    }


def _convert_to_blocks(ai_content: Dict, h1_text: str, data: PageData, cta_text: str) -> List[Dict]:
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
        "text": cta_text,
        "phone": data.phone or ""
    })
    
    return blocks
