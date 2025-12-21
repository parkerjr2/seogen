"""
Hub Blueprint System - Defines distinct content structures per hub type

Each blueprint specifies:
- Section order (different per blueprint to avoid templated appearance)
- Section headings (unique per hub type)
- Content focus for each section

WHY DIFFERENT BLUEPRINTS MATTER:
- Prevents all hubs from having identical structure
- Different section orders signal different information priorities
- Unique headings avoid duplicate content patterns
- Varied focus areas create substantive differences
"""

from typing import List, Dict, Any


class HubBlueprint:
    """Defines the structure and sections for a hub page."""
    
    def __init__(self, name: str, sections: List[Dict[str, Any]]):
        self.name = name
        self.sections = sections
    
    def get_section_headings(self) -> List[str]:
        """Get list of all section headings in this blueprint."""
        return [s.get("heading", "") for s in self.sections if s.get("heading")]


# Blueprint 1: Residential-Focused (Homeowner Journey)
RESIDENTIAL_BLUEPRINT = HubBlueprint(
    name="residential_focused",
    sections=[
        {
            "type": "hero",
            "heading": None,  # H1 generated separately
            "focus": "Safety and home protection angle"
        },
        {
            "type": "who_this_is_for",
            "heading": "Is This Service Right for Your Home?",
            "focus": "Homeowner scenarios, family safety, property value"
        },
        {
            "type": "common_projects",
            "heading": "Common Home Projects We Handle",
            "focus": "Residential job examples with home context"
        },
        {
            "type": "how_we_work",
            "heading": "Our Home Service Process",
            "focus": "Respectful, family-friendly, minimal disruption"
        },
        {
            "type": "safety_and_code",
            "heading": "Safety Standards & Residential Codes",
            "focus": "Homeowner safety, permits, inspections"
        },
        {
            "type": "service_areas",
            "heading": "Primary Service Areas",
            "focus": "City links with homeowner context"
        },
        {
            "type": "pricing_factors",
            "heading": "What Affects Your Project Cost",
            "focus": "Residential pricing transparency"
        },
        {
            "type": "faqs",
            "heading": "Homeowner Questions Answered",
            "focus": "Residential-specific FAQs"
        },
        {
            "type": "cta",
            "heading": None,
            "focus": "Family/home protection CTA"
        }
    ]
)


# Blueprint 2: Commercial-Focused (Business Operations)
COMMERCIAL_BLUEPRINT = HubBlueprint(
    name="commercial_focused",
    sections=[
        {
            "type": "hero",
            "heading": None,
            "focus": "Business continuity and compliance angle"
        },
        {
            "type": "compliance_first",
            "heading": "Commercial Code Compliance & Permits",
            "focus": "Business permits, inspections, liability"
        },
        {
            "type": "who_this_is_for",
            "heading": "Commercial Services For Your Business",
            "focus": "Business types, facility management, operations"
        },
        {
            "type": "downtime_management",
            "heading": "Minimizing Business Disruption",
            "focus": "After-hours work, scheduling, coordination"
        },
        {
            "type": "common_projects",
            "heading": "Typical Commercial Projects",
            "focus": "Business-specific job examples"
        },
        {
            "type": "service_areas",
            "heading": "Commercial Service Coverage",
            "focus": "City links with business context"
        },
        {
            "type": "pricing_factors",
            "heading": "Commercial Project Investment",
            "focus": "Business budgeting, ROI, maintenance contracts"
        },
        {
            "type": "faqs",
            "heading": "Business Owner FAQs",
            "focus": "Commercial-specific FAQs"
        },
        {
            "type": "cta",
            "heading": None,
            "focus": "Business continuity CTA"
        }
    ]
)


# Blueprint 3: Emergency/Urgent-Focused (Rapid Response)
EMERGENCY_BLUEPRINT = HubBlueprint(
    name="emergency_focused",
    sections=[
        {
            "type": "hero",
            "heading": None,
            "focus": "Immediate help and safety angle"
        },
        {
            "type": "when_to_call",
            "heading": "When You Need Emergency Service",
            "focus": "Urgent vs. non-urgent triage"
        },
        {
            "type": "response_process",
            "heading": "Our Emergency Response Process",
            "focus": "Speed, safety protocols, communication"
        },
        {
            "type": "common_emergencies",
            "heading": "Common Emergency Situations",
            "focus": "Urgent scenarios we handle"
        },
        {
            "type": "service_areas",
            "heading": "Emergency Service Coverage",
            "focus": "City links with response time context"
        },
        {
            "type": "who_this_is_for",
            "heading": "Emergency vs. Routine Service",
            "focus": "Clarifying emergency criteria"
        },
        {
            "type": "pricing_factors",
            "heading": "Emergency Service Costs",
            "focus": "After-hours rates, urgency factors"
        },
        {
            "type": "faqs",
            "heading": "Emergency Service Questions",
            "focus": "Emergency-specific FAQs"
        },
        {
            "type": "cta",
            "heading": None,
            "focus": "Immediate action CTA"
        }
    ]
)


# Blueprint 4: Repair-Focused (Problem Solving)
REPAIR_BLUEPRINT = HubBlueprint(
    name="repair_focused",
    sections=[
        {
            "type": "hero",
            "heading": None,
            "focus": "Problem diagnosis and lasting fixes"
        },
        {
            "type": "diagnostic_approach",
            "heading": "Our Repair Diagnostic Process",
            "focus": "Finding root causes, not just symptoms"
        },
        {
            "type": "common_repairs",
            "heading": "Common Repair Issues We Fix",
            "focus": "Repair-specific job examples"
        },
        {
            "type": "repair_vs_replace",
            "heading": "Repair or Replace? We'll Tell You Honestly",
            "focus": "Transparent recommendations"
        },
        {
            "type": "who_this_is_for",
            "heading": "When Repair Service Makes Sense",
            "focus": "Repair scenarios vs. other services"
        },
        {
            "type": "service_areas",
            "heading": "Repair Service Areas",
            "focus": "City links with repair context"
        },
        {
            "type": "pricing_factors",
            "heading": "How Repair Costs Are Determined",
            "focus": "Diagnostic fees, repair pricing"
        },
        {
            "type": "faqs",
            "heading": "Repair Service FAQs",
            "focus": "Repair-specific FAQs"
        },
        {
            "type": "cta",
            "heading": None,
            "focus": "Fix it right CTA"
        }
    ]
)


# Blueprint 5: Installation-Focused (Planning & Projects)
INSTALLATION_BLUEPRINT = HubBlueprint(
    name="installation_focused",
    sections=[
        {
            "type": "hero",
            "heading": None,
            "focus": "Planning and quality installation"
        },
        {
            "type": "planning_process",
            "heading": "Installation Planning & Consultation",
            "focus": "Sizing, specifications, options"
        },
        {
            "type": "common_installations",
            "heading": "Installation Projects We Complete",
            "focus": "Installation-specific job examples"
        },
        {
            "type": "permits_and_coordination",
            "heading": "Permits, Inspections & Trade Coordination",
            "focus": "New work compliance and scheduling"
        },
        {
            "type": "who_this_is_for",
            "heading": "Installation Services For Your Project",
            "focus": "New construction, upgrades, additions"
        },
        {
            "type": "service_areas",
            "heading": "Installation Service Coverage",
            "focus": "City links with project context"
        },
        {
            "type": "pricing_factors",
            "heading": "Installation Project Investment",
            "focus": "Equipment, labor, warranties"
        },
        {
            "type": "faqs",
            "heading": "Installation Project FAQs",
            "focus": "Installation-specific FAQs"
        },
        {
            "type": "cta",
            "heading": None,
            "focus": "Plan your project CTA"
        }
    ]
)


# Blueprint 6: Maintenance-Focused (Preventive Care)
MAINTENANCE_BLUEPRINT = HubBlueprint(
    name="maintenance_focused",
    sections=[
        {
            "type": "hero",
            "heading": None,
            "focus": "Preventive care and system longevity"
        },
        {
            "type": "why_maintenance",
            "heading": "The Value of Regular Maintenance",
            "focus": "Preventing breakdowns, extending life, efficiency"
        },
        {
            "type": "maintenance_programs",
            "heading": "Our Maintenance Service Options",
            "focus": "Programs, schedules, what's included"
        },
        {
            "type": "common_services",
            "heading": "Maintenance Services We Provide",
            "focus": "Maintenance-specific job examples"
        },
        {
            "type": "who_this_is_for",
            "heading": "Who Benefits from Maintenance Programs",
            "focus": "Homeowners and businesses protecting investments"
        },
        {
            "type": "service_areas",
            "heading": "Maintenance Service Areas",
            "focus": "City links with maintenance context"
        },
        {
            "type": "pricing_factors",
            "heading": "Maintenance Program Costs",
            "focus": "Program pricing, contract options"
        },
        {
            "type": "faqs",
            "heading": "Maintenance Program FAQs",
            "focus": "Maintenance-specific FAQs"
        },
        {
            "type": "cta",
            "heading": None,
            "focus": "Protect your investment CTA"
        }
    ]
)


# Blueprint mapping
BLUEPRINTS = {
    "residential_focused": RESIDENTIAL_BLUEPRINT,
    "commercial_focused": COMMERCIAL_BLUEPRINT,
    "emergency_focused": EMERGENCY_BLUEPRINT,
    "repair_focused": REPAIR_BLUEPRINT,
    "installation_focused": INSTALLATION_BLUEPRINT,
    "maintenance_focused": MAINTENANCE_BLUEPRINT
}


def get_blueprint(blueprint_name: str) -> HubBlueprint:
    """Get blueprint by name, defaults to residential if not found."""
    return BLUEPRINTS.get(blueprint_name, RESIDENTIAL_BLUEPRINT)


def get_blueprint_for_hub(hub_key: str) -> HubBlueprint:
    """
    Get the appropriate blueprint for a hub key.
    Maps hub keys to their designated blueprints.
    """
    # Map hub keys to blueprint names
    hub_to_blueprint = {
        "residential": "residential_focused",
        "commercial": "commercial_focused",
        "emergency": "emergency_focused",
        "repair": "repair_focused",
        "installation": "installation_focused",
        "maintenance": "maintenance_focused"
    }
    
    blueprint_name = hub_to_blueprint.get(hub_key, "residential_focused")
    return get_blueprint(blueprint_name)
