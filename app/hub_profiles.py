"""
Hub Profile System for Anti-Doorway Page Strategy

This module defines unique profiles for each hub type to ensure meaningfully
different content, structure, and messaging. Each hub profile includes:
- Audience differentiation
- Unique pain points and proof signals
- Distinct compliance/scheduling focus
- Hub-specific job examples
- Disqualifiers ("Not for..." content)
- Unique CTA angles

WHY THIS REDUCES DOORWAY RISK:
- Different section orders prevent templated appearance
- Unique FAQs avoid duplicate content across hubs
- Audience-specific language creates distinct value propositions
- Job examples and disqualifiers add substantive differences
- Varied CTAs reflect different buyer intents
"""

HUB_PROFILES = {
    "residential": {
        "audience_label": "Homeowners",
        "audience_description": "homeowners and residential property owners",
        "primary_pain_points": [
            "Safety concerns with outdated systems",
            "Minimizing disruption to daily home life",
            "Understanding what's normal vs. urgent",
            "Coordinating work around family schedules",
            "Protecting home value and preventing damage"
        ],
        "proof_signals": [
            "Licensed and insured for residential work",
            "Background-checked technicians",
            "Respectful of your home and family",
            "Clear pricing before work begins",
            "Warranty on residential installations"
        ],
        "compliance_focus": "residential safety codes and homeowner permits",
        "scheduling_focus": "flexible scheduling around your family's routine",
        "typical_job_examples": [
            "Whole-home system upgrades during remodels",
            "Safety inspections before buying or selling",
            "Emergency repairs affecting daily living",
            "Preventive maintenance to avoid breakdowns",
            "Energy efficiency improvements"
        ],
        "disqualifiers": [
            "Large commercial facilities",
            "Industrial-scale projects",
            "Multi-unit apartment complexes (see Commercial)"
        ],
        "cta_angle": "Protect your home and family",
        "blueprint": "residential_focused"
    },
    
    "commercial": {
        "audience_label": "Business Owners & Facility Managers",
        "audience_description": "business owners, facility managers, and commercial property operators",
        "primary_pain_points": [
            "Minimizing business downtime and revenue loss",
            "Meeting commercial code and inspection requirements",
            "Managing liability and insurance compliance",
            "Coordinating work around business operations",
            "Budgeting for maintenance vs. emergency costs"
        ],
        "proof_signals": [
            "Licensed for commercial work",
            "Experience with business permits and inspections",
            "After-hours and weekend availability",
            "Detailed documentation for insurance/compliance",
            "Commercial warranty coverage"
        ],
        "compliance_focus": "commercial building codes, permits, and inspection coordination",
        "scheduling_focus": "after-hours and weekend service to minimize business disruption",
        "typical_job_examples": [
            "Tenant improvement projects",
            "Code compliance upgrades for inspections",
            "Preventive maintenance contracts",
            "Emergency repairs during business hours",
            "System expansions for business growth"
        ],
        "disqualifiers": [
            "Single-family homes (see Residential)",
            "DIY projects",
            "Projects without proper permits"
        ],
        "cta_angle": "Keep your business running smoothly",
        "blueprint": "commercial_focused"
    },
    
    "emergency": {
        "audience_label": "Property Owners Facing Urgent Issues",
        "audience_description": "property owners dealing with urgent or time-sensitive issues",
        "primary_pain_points": [
            "Immediate safety hazards requiring fast response",
            "Damage prevention and mitigation",
            "Uncertainty about severity and next steps",
            "Need for 24/7 availability",
            "Stress of unexpected repair costs"
        ],
        "proof_signals": [
            "24/7 emergency response",
            "Rapid triage and assessment",
            "Mobile-equipped service vehicles",
            "Direct communication with on-call technicians",
            "Emergency stabilization before full repairs"
        ],
        "compliance_focus": "immediate safety protocols and emergency code compliance",
        "scheduling_focus": "same-day and after-hours emergency response",
        "typical_job_examples": [
            "Safety hazards requiring immediate attention",
            "System failures causing property damage",
            "Loss of essential services",
            "Storm or weather-related damage",
            "Urgent repairs before inspections or closings"
        ],
        "disqualifiers": [
            "Routine maintenance (see Residential or Commercial)",
            "Non-urgent upgrades or improvements",
            "Projects that can wait for regular scheduling"
        ],
        "cta_angle": "Get immediate help now",
        "blueprint": "emergency_focused"
    },
    
    "repair": {
        "audience_label": "Property Owners Needing Fixes",
        "audience_description": "property owners addressing existing system problems",
        "primary_pain_points": [
            "Diagnosing the root cause of problems",
            "Avoiding unnecessary replacements",
            "Getting accurate repair vs. replace guidance",
            "Understanding warranty coverage",
            "Preventing recurring issues"
        ],
        "proof_signals": [
            "Thorough diagnostic process",
            "Honest repair vs. replace recommendations",
            "Warranty on repair work",
            "Detailed explanation of issues",
            "Follow-up to ensure lasting fixes"
        ],
        "compliance_focus": "repair standards and code-compliant fixes",
        "scheduling_focus": "prompt diagnosis and efficient repair scheduling",
        "typical_job_examples": [
            "Troubleshooting intermittent problems",
            "Repairing failed components",
            "Fixing code violations found in inspections",
            "Restoring functionality after damage",
            "Addressing wear and tear issues"
        ],
        "disqualifiers": [
            "New construction or additions (see Installation)",
            "Emergencies requiring immediate response (see Emergency)",
            "Complete system replacements (see Installation)"
        ],
        "cta_angle": "Get it fixed right the first time",
        "blueprint": "repair_focused"
    },
    
    "installation": {
        "audience_label": "Property Owners Planning New Systems",
        "audience_description": "property owners planning new installations or major upgrades",
        "primary_pain_points": [
            "Choosing the right system for needs and budget",
            "Understanding long-term costs and benefits",
            "Coordinating with other contractors",
            "Ensuring proper sizing and specifications",
            "Meeting code requirements for new work"
        ],
        "proof_signals": [
            "Detailed planning and specification process",
            "Multiple options at different price points",
            "Coordination with other trades",
            "Permit handling and inspection scheduling",
            "Manufacturer warranties on new equipment"
        ],
        "compliance_focus": "new installation codes, permits, and inspection requirements",
        "scheduling_focus": "project planning and milestone-based scheduling",
        "typical_job_examples": [
            "New construction installations",
            "Complete system replacements",
            "Home additions and expansions",
            "Upgrade projects for efficiency or capacity",
            "New feature installations"
        ],
        "disqualifiers": [
            "Emergency repairs (see Emergency or Repair)",
            "Minor fixes or adjustments (see Repair)",
            "Routine maintenance (see Maintenance)"
        ],
        "cta_angle": "Plan your project with confidence",
        "blueprint": "installation_focused"
    },
    
    "maintenance": {
        "audience_label": "Property Owners Protecting Their Investment",
        "audience_description": "property owners focused on preventive care and system longevity",
        "primary_pain_points": [
            "Avoiding unexpected breakdowns and costs",
            "Maximizing system lifespan and efficiency",
            "Remembering to schedule regular service",
            "Understanding what maintenance is actually needed",
            "Budgeting for ongoing care"
        ],
        "proof_signals": [
            "Comprehensive maintenance programs",
            "Scheduled service reminders",
            "Detailed inspection reports",
            "Priority service for maintenance customers",
            "Maintenance records for warranty and resale"
        ],
        "compliance_focus": "preventive care standards and manufacturer requirements",
        "scheduling_focus": "regular service intervals and seasonal maintenance",
        "typical_job_examples": [
            "Annual or seasonal inspections",
            "Preventive cleaning and adjustments",
            "Early problem detection and correction",
            "System optimization for efficiency",
            "Maintenance contract services"
        ],
        "disqualifiers": [
            "Emergency repairs (see Emergency)",
            "Major installations or replacements (see Installation)",
            "One-time fixes without ongoing care (see Repair)"
        ],
        "cta_angle": "Protect your investment with regular care",
        "blueprint": "maintenance_focused"
    }
}


def get_hub_profile(hub_key):
    """
    Get the profile for a specific hub type.
    Returns default residential profile if hub_key not found.
    """
    return HUB_PROFILES.get(hub_key, HUB_PROFILES["residential"])


def get_all_hub_keys():
    """Get list of all defined hub keys."""
    return list(HUB_PROFILES.keys())
