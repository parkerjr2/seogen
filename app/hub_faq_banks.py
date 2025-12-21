"""
Hub-Specific FAQ Banks - Unique questions per hub type

Each hub type has 8-12 unique FAQs that reflect the specific concerns
and questions of that audience. NO question strings are shared across
different hub types to avoid duplicate content.

WHY UNIQUE FAQS MATTER:
- Prevents duplicate content across hub pages
- Reflects different audience concerns and priorities
- Adds substantive value specific to each hub type
- Helps search engines see pages as distinct resources
"""

from typing import List, Dict


# Residential Hub FAQs (Homeowner focus)
RESIDENTIAL_FAQS = [
    {
        "question": "Do I need to be home during the service appointment?",
        "answer": "For most residential services, we recommend having an adult present to provide access, answer questions about your home's history, and approve any additional work if needed. However, if you can't be home, we can often work with lockbox access or coordinate with a trusted neighbor or property manager. We'll discuss the best arrangement during scheduling."
    },
    {
        "question": "Will you protect my floors and furniture during the work?",
        "answer": "Yes, we take home protection seriously. Our technicians use drop cloths, floor protection, and shoe covers as standard practice. We'll move furniture if needed (with your permission) and always clean up our work area before leaving. If there's any drywall patching or wall penetrations required, we'll discuss the extent of repairs needed beforehand."
    },
    {
        "question": "How do I know if my home's system needs upgrading or just repair?",
        "answer": "During our inspection, we'll assess your system's age, condition, safety, and capacity for your home's needs. We'll explain what's working, what's not, and whether repairs will give you reliable service or if upgrading makes more sense long-term. You'll get honest recommendations with options at different price points, never pressure to replace something that can be properly repaired."
    },
    {
        "question": "What happens if you find additional problems during the work?",
        "answer": "If we discover issues beyond the original scope, we'll stop and explain what we found, why it matters, and what it will cost to address. You'll approve any additional work before we proceed. We never perform unauthorized work or surprise you with unexpected charges. Our goal is to keep you informed and in control of decisions about your home."
    },
    {
        "question": "Do you offer financing for larger home projects?",
        "answer": "Yes, we offer financing options for qualifying homeowners on approved credit. This can make larger projects like whole-home upgrades or system replacements more manageable with monthly payments. We'll provide financing information during your estimate so you can make the best decision for your family's budget."
    },
    {
        "question": "How long will my home be without service during the work?",
        "answer": "For most residential repairs, service is restored the same day. For larger projects like panel upgrades or system replacements, we'll schedule the work to minimize disruption and clearly communicate the timeline. We understand your family depends on these systems, so we work efficiently and keep you informed of progress throughout the project."
    },
    {
        "question": "Will this work affect my home's resale value?",
        "answer": "Properly permitted and code-compliant work typically maintains or increases home value. Outdated or non-compliant systems can be red flags during home inspections and may affect your ability to sell. We ensure all work meets current codes and provide documentation you can share with future buyers or their inspectors."
    },
    {
        "question": "What warranty comes with residential service work?",
        "answer": "We warranty our workmanship on residential installations and repairs. Specific warranty terms depend on the type of work and materials used. Equipment and parts typically carry manufacturer warranties, which we'll help you understand and utilize if needed. We stand behind our work and will address any issues that arise during the warranty period."
    },
    {
        "question": "Can you work around my family's schedule?",
        "answer": "We offer flexible scheduling to accommodate working families, including some evening and weekend appointments. During scheduling, let us know your constraints and preferences. We'll do our best to find a time that works for your household while ensuring we can complete quality work without rushing."
    },
    {
        "question": "How do I prepare my home for the service visit?",
        "answer": "Clear access to the work area and related systems (like electrical panels or mechanical rooms). Secure pets in a separate area for their safety and our technicians' comfort. If work involves attics or crawl spaces, let us know about any access challenges. We'll provide specific preparation instructions when we schedule your appointment."
    }
]


# Commercial Hub FAQs (Business focus)
COMMERCIAL_FAQS = [
    {
        "question": "Can you work outside of business hours to avoid disrupting operations?",
        "answer": "Yes, we regularly schedule commercial work during evenings, weekends, and overnight hours to minimize impact on your business operations. Our technicians are experienced with after-hours work and understand the importance of having your facility ready for business the next day. We'll coordinate timing that works best for your operation."
    },
    {
        "question": "Who handles the permit applications and inspection scheduling?",
        "answer": "We handle all permit applications and coordinate required inspections as part of our commercial service. We're familiar with local commercial code requirements and inspection processes. You'll receive copies of all permits and inspection reports for your facility records and compliance documentation."
    },
    {
        "question": "Do you provide documentation for insurance and compliance audits?",
        "answer": "Yes, we provide detailed documentation including work orders, inspection reports, permits, and compliance certificates. This documentation is essential for insurance requirements, safety audits, and regulatory compliance. We understand commercial properties need thorough records and we maintain organized documentation for your facility management files."
    },
    {
        "question": "What's included in a commercial maintenance contract?",
        "answer": "Commercial maintenance contracts typically include scheduled inspections, preventive maintenance, priority service response, detailed reporting, and often discounted rates on repairs. We'll customize a maintenance program based on your facility type, equipment, and operational requirements. Regular maintenance helps prevent unexpected downtime and extends equipment life."
    },
    {
        "question": "How do you coordinate with other contractors during tenant improvements?",
        "answer": "We're experienced working as part of construction teams on tenant improvement projects. We'll coordinate with general contractors, architects, and other trades to ensure our work integrates smoothly with the overall project schedule. We attend coordination meetings, provide timely updates, and work efficiently to keep projects on track."
    },
    {
        "question": "What's your response time for commercial emergency calls?",
        "answer": "For commercial emergencies affecting business operations, we prioritize rapid response. Response times vary based on time of day and technician availability, but we understand business downtime costs money. Maintenance contract customers receive priority response. We'll provide an estimated arrival time when you call and keep you updated if circumstances change."
    },
    {
        "question": "Do you carry commercial liability insurance and workers compensation?",
        "answer": "Yes, we maintain comprehensive commercial liability insurance and workers compensation coverage. We can provide certificates of insurance for your facility management records or to meet your property owner's requirements. Our insurance protects both your business and our team during commercial work."
    },
    {
        "question": "Can you provide a detailed quote for budgeting and approval processes?",
        "answer": "We provide detailed commercial quotes that break down labor, materials, permits, and other costs. Our quotes include scope of work descriptions suitable for management review and approval processes. For larger projects, we can work with your budget constraints to provide options or phased approaches that meet your financial planning needs."
    },
    {
        "question": "How do you handle multi-location businesses?",
        "answer": "We can service multiple locations within our coverage area and provide consistent service standards across your facilities. For businesses with several locations, we can establish master service agreements, centralized billing, and standardized maintenance schedules. This simplifies facility management and ensures all locations receive the same quality service."
    },
    {
        "question": "What qualifications do your commercial technicians have?",
        "answer": "Our commercial technicians hold appropriate licenses for commercial work and have experience with commercial systems, codes, and compliance requirements. They understand the differences between commercial and residential work, including safety protocols, documentation requirements, and the importance of minimizing business disruption. We invest in ongoing training to keep our team current with commercial standards."
    }
]


# Emergency Hub FAQs (Urgent response focus)
EMERGENCY_FAQS = [
    {
        "question": "How quickly can someone get to my property for an emergency?",
        "answer": "Emergency response times vary based on technician location, time of day, and current call volume. When you call, we'll provide an estimated arrival time based on real-time availability. We prioritize true emergencies involving safety hazards or significant property damage. Our goal is to get a qualified technician to you as quickly as possible to assess and stabilize the situation."
    },
    {
        "question": "What qualifies as an emergency versus a regular service call?",
        "answer": "Emergencies involve immediate safety hazards, active property damage, or complete loss of essential services. Examples include exposed wiring, flooding from failed systems, or total loss of heating in winter. If you're unsure whether your situation is an emergency, call us and describe the problem. We'll help you determine the appropriate response level and timing."
    },
    {
        "question": "Will the emergency technician have the parts needed to fix my problem?",
        "answer": "Our emergency service vehicles stock common parts and materials for typical urgent repairs. However, some situations require specialized parts that must be ordered. In those cases, the technician will stabilize the situation, make it safe, and schedule a follow-up visit to complete permanent repairs once parts arrive. We'll explain the temporary measures and timeline for final resolution."
    },
    {
        "question": "How much do emergency services cost compared to regular appointments?",
        "answer": "Emergency service typically includes premium rates for after-hours availability, rapid response, and immediate technician dispatch. The exact cost depends on the time of day, day of week, and complexity of the work required. We'll provide pricing information when you call so you can make an informed decision. In true emergencies involving safety or property protection, the cost of immediate service is often justified by preventing greater damage or hazards."
    },
    {
        "question": "Can you make temporary repairs if I can't afford the full fix right now?",
        "answer": "In many emergency situations, we can provide temporary stabilization to make things safe and functional while you arrange for permanent repairs. We'll explain what temporary measures are possible, how long they'll last, and what permanent repairs will be needed. Our priority in emergencies is safety and preventing further damage, and we'll work with you on solutions that fit your immediate circumstances."
    },
    {
        "question": "What should I do while waiting for emergency service to arrive?",
        "answer": "When you call, we'll provide specific safety instructions based on your situation. General guidance includes staying away from hazards, shutting off affected systems if safe to do so, protecting property from ongoing damage if possible, and ensuring clear access for our technician. Never put yourself at risk trying to fix emergency situations. Wait for professional help in a safe location."
    },
    {
        "question": "Do you provide emergency service on holidays and weekends?",
        "answer": "Yes, emergencies don't follow business hours, so we provide emergency response 24/7 including holidays and weekends. Premium rates apply for after-hours and holiday service. When you call our emergency line, you'll reach a real person who can dispatch a technician or provide guidance on your situation."
    },
    {
        "question": "Will insurance cover emergency repairs?",
        "answer": "Insurance coverage depends on your specific policy and the cause of the emergency. We can provide detailed documentation of emergency work for insurance claims, including photos, descriptions of damage, and itemized invoices. We recommend contacting your insurance company as soon as possible after an emergency to understand your coverage and claims process."
    },
    {
        "question": "What if the emergency happens in the middle of the night?",
        "answer": "Our emergency service operates 24/7. If you have an emergency in the middle of the night, call our emergency line. We'll assess the situation, provide immediate safety guidance, and dispatch a technician if needed. Overnight emergencies receive the same priority response as daytime calls when safety or property protection is at stake."
    },
    {
        "question": "Can you help me determine if I should call emergency services like fire department?",
        "answer": "If you smell gas, see flames, have electrical arcing or sparking, or face any immediate life-threatening situation, call 911 first. Once emergency services have secured the scene and declared it safe, then call us for repairs. We work with fire departments and other emergency responders regularly and can coordinate repairs after they've addressed immediate safety concerns."
    }
]


# Repair Hub FAQs (Diagnostic and fix focus)
REPAIR_FAQS = [
    {
        "question": "How do you diagnose problems that only happen intermittently?",
        "answer": "Intermittent problems require systematic diagnostic approaches. We'll gather information about when the problem occurs, what conditions trigger it, and any patterns you've noticed. Our technicians use diagnostic tools to test components under various conditions and may need to monitor the system over time. We'll explain our diagnostic process and may recommend follow-up visits if the problem doesn't occur during our initial visit."
    },
    {
        "question": "Do you charge for diagnostics even if I don't proceed with repairs?",
        "answer": "Yes, diagnostic time and expertise have value regardless of whether you proceed with repairs. We'll explain diagnostic fees upfront before starting work. The diagnostic fee typically covers the service call, inspection, testing, and a written assessment of the problem and repair options. If you proceed with recommended repairs, we often apply the diagnostic fee toward the repair cost."
    },
    {
        "question": "How do I know if repair makes sense versus replacing the whole system?",
        "answer": "We consider several factors: the system's age, overall condition, repair cost versus replacement cost, likelihood of future problems, efficiency of current versus new systems, and your long-term plans. We'll provide honest recommendations explaining the pros and cons of repair versus replacement. Our goal is to help you make the best decision for your situation, not to sell you a replacement you don't need."
    },
    {
        "question": "What if the repair doesn't fix the problem?",
        "answer": "We warranty our repair work. If the problem persists after our repair, we'll return to reassess at no additional diagnostic charge. Sometimes problems have multiple causes or symptoms point to different issues than initially diagnosed. We'll work with you until the problem is properly resolved, standing behind our diagnostic work and repairs."
    },
    {
        "question": "Can you give me a repair estimate before starting the work?",
        "answer": "After diagnosing the problem, we'll provide a detailed repair estimate including parts, labor, and any other costs before starting repairs. You'll approve the estimate before we proceed. If we discover additional issues during repairs, we'll stop and get your approval for any additional work and costs."
    },
    {
        "question": "How long do repairs typically last?",
        "answer": "Repair longevity depends on what was repaired, the quality of parts used, the system's overall condition, and how well it's maintained. We use quality parts and proper repair techniques to maximize repair life. We'll give you realistic expectations about repair longevity and let you know if the system's age or condition means repairs may only be a short-term solution."
    },
    {
        "question": "Do you repair all brands and models?",
        "answer": "We repair most common brands and models. For some specialized or very old equipment, parts availability may be limited. During diagnostics, we'll let you know if we can obtain necessary parts and how long that might take. If we can't repair a particular brand or model, we'll recommend alternatives including replacement options."
    },
    {
        "question": "What's included in your repair warranty?",
        "answer": "We warranty our repair workmanship for a specified period (terms provided with your repair invoice). Parts typically carry manufacturer warranties. If a repaired component fails during the warranty period due to our workmanship, we'll return to make it right at no charge. We'll explain specific warranty terms when providing your repair estimate."
    },
    {
        "question": "Can you repair code violations found during home inspections?",
        "answer": "Yes, we regularly repair code violations identified during home inspections or insurance assessments. We'll assess the violation, explain what's required to bring it to code, provide an estimate, and coordinate any required inspections after repairs. We're familiar with local code requirements and can help you resolve violations efficiently."
    },
    {
        "question": "How soon can you schedule a repair diagnostic visit?",
        "answer": "Repair diagnostic appointments are typically available within a few days, depending on our schedule and your availability. If your situation is urgent but not an emergency, let us know and we'll try to accommodate an earlier appointment. We'll provide a clear time window for our arrival and call ahead when we're on the way."
    }
]


# Installation Hub FAQs (New work focus)
INSTALLATION_FAQS = [
    {
        "question": "How do I choose the right system size and specifications for my needs?",
        "answer": "Proper sizing requires evaluating your property's specific requirements including square footage, usage patterns, existing infrastructure, and future needs. We'll conduct a thorough assessment, explain sizing considerations, and recommend options that match your needs and budget. Oversized or undersized systems can lead to problems, so we take sizing seriously and provide detailed explanations of our recommendations."
    },
    {
        "question": "What's included in your installation estimate?",
        "answer": "Our installation estimates include equipment, materials, labor, permits, inspections, testing, and cleanup. We itemize costs so you understand what you're paying for. The estimate also includes project timeline, warranty information, and any ongoing maintenance recommendations. We'll explain everything included and answer questions about the scope of work."
    },
    {
        "question": "How long does a typical installation project take?",
        "answer": "Installation timelines vary based on project complexity, permit requirements, and coordination with other trades. Simple installations might take a day, while complex projects could take several days or weeks. We'll provide a realistic timeline in your estimate and keep you informed of progress. We schedule installations to minimize disruption and complete work efficiently without compromising quality."
    },
    {
        "question": "Who obtains the permits and schedules inspections?",
        "answer": "We handle all permit applications and inspection scheduling as part of our installation service. We're familiar with local permitting requirements and inspection processes. You'll receive copies of permits and inspection approvals for your records. Proper permitting protects you by ensuring work meets code and won't cause issues with insurance or future property sales."
    },
    {
        "question": "Can you coordinate with my other contractors?",
        "answer": "Yes, we regularly work as part of larger construction or renovation projects. We'll coordinate with your general contractor, architect, or other trades to ensure our work integrates smoothly with the overall project. We attend coordination meetings, provide timely updates, and work efficiently to keep projects on schedule."
    },
    {
        "question": "What warranties come with new installations?",
        "answer": "New installations include our workmanship warranty plus manufacturer warranties on equipment and materials. Warranty terms vary by manufacturer and product type. We'll explain all applicable warranties, help you understand what's covered, and assist with warranty claims if needed. We also offer extended warranty options on some equipment."
    },
    {
        "question": "Do you offer different quality levels or brands to fit my budget?",
        "answer": "Yes, we work with multiple manufacturers at different price points. We'll present options ranging from budget-friendly to premium, explaining the differences in features, efficiency, longevity, and warranties. Our goal is to help you make an informed decision that fits your budget while meeting your needs. We won't pressure you toward the most expensive option."
    },
    {
        "question": "What happens if you encounter unexpected issues during installation?",
        "answer": "Sometimes installations reveal hidden problems like outdated wiring, structural issues, or code violations that must be addressed. If we encounter unexpected issues, we'll stop, explain what we found, and provide options for addressing it. You'll approve any additional work and costs before we proceed. We try to anticipate potential issues during planning, but some things can't be known until work begins."
    },
    {
        "question": "Can I see examples of similar installations you've completed?",
        "answer": "We're happy to share examples of similar projects, discuss our experience with specific installation types, and provide references from past customers. During consultation, we'll explain our installation process, quality standards, and what you can expect. We take pride in our installation work and want you to feel confident in choosing us for your project."
    },
    {
        "question": "What ongoing maintenance will my new system require?",
        "answer": "New systems require regular maintenance to maintain efficiency, prevent problems, and preserve warranties. We'll explain recommended maintenance schedules and what's involved. Many customers choose maintenance programs to ensure their investment is protected. We'll provide maintenance documentation and reminders to help you stay on schedule with required service."
    }
]


# Maintenance Hub FAQs (Preventive care focus)
MAINTENANCE_FAQS = [
    {
        "question": "What's actually included in a maintenance visit?",
        "answer": "Maintenance visits typically include visual inspection, cleaning of key components, testing of safety controls, checking for wear or damage, adjusting settings for optimal performance, and identifying potential problems before they cause failures. We'll provide a detailed checklist of what we inspect and service. After each visit, you'll receive a report documenting our findings and any recommendations."
    },
    {
        "question": "How often should I schedule maintenance service?",
        "answer": "Maintenance frequency depends on your system type, age, usage, and manufacturer recommendations. Most residential systems benefit from annual maintenance, while commercial systems or heavily-used equipment may need more frequent service. We'll recommend an appropriate schedule based on your specific situation and help you stay on track with service reminders."
    },
    {
        "question": "Will regular maintenance really prevent breakdowns?",
        "answer": "While maintenance can't prevent every possible failure, it significantly reduces breakdown risk by catching problems early, keeping systems clean and properly adjusted, and ensuring components are working correctly. Regular maintenance extends equipment life, maintains efficiency, and often prevents the most common failure modes. It's like regular oil changes for your car – not a guarantee, but proven to prevent many problems."
    },
    {
        "question": "What happens if you find problems during a maintenance visit?",
        "answer": "If we discover issues during maintenance, we'll explain what we found, why it matters, and what should be done about it. We'll categorize findings by urgency – immediate safety concerns, repairs needed soon, and items to monitor. You'll receive a written report and estimate for any recommended repairs. Maintenance customers often receive priority scheduling and discounted rates on repairs."
    },
    {
        "question": "Can I do some maintenance myself to save money?",
        "answer": "Some basic maintenance tasks like changing filters or keeping areas clean can be done by property owners. However, comprehensive maintenance requires specialized tools, training, and knowledge of what to look for. We'll explain which tasks you can handle and which require professional service. DIY maintenance doesn't replace professional service but can complement it between scheduled visits."
    },
    {
        "question": "Do maintenance programs include repairs or just inspections?",
        "answer": "Maintenance programs typically include inspections, cleaning, adjustments, and minor repairs like replacing worn belts or cleaning contacts. Major repairs or parts replacement are usually additional costs. We'll clearly explain what's included in your maintenance program and what would be considered additional repair work. Some programs offer discounts on repairs for members."
    },
    {
        "question": "What if I skip maintenance for a year or two?",
        "answer": "Skipping maintenance allows small problems to become bigger ones, reduces efficiency, shortens equipment life, and may void manufacturer warranties. Systems that haven't been maintained often require more extensive service to bring them back to proper operating condition. If you've missed maintenance, we can assess your system's current condition and recommend a service plan to get it back on track."
    },
    {
        "question": "Will you remind me when maintenance is due?",
        "answer": "Yes, maintenance program customers receive reminders when service is due. We track your maintenance schedule and contact you to arrange appointments. This takes the burden off you to remember and helps ensure your system receives timely service. You can also contact us anytime to schedule service or ask questions between scheduled visits."
    },
    {
        "question": "Does regular maintenance affect my equipment warranty?",
        "answer": "Many manufacturer warranties require proof of regular professional maintenance. Skipping maintenance can void warranty coverage. We provide maintenance documentation you can use to demonstrate compliance with warranty requirements. Regular maintenance protects both your equipment and your warranty coverage."
    },
    {
        "question": "Can I cancel my maintenance program if I need to?",
        "answer": "Maintenance program terms vary, but we generally offer flexible options. Some programs are pay-per-visit, while others are annual contracts. We'll explain terms clearly before you sign up. If your circumstances change, talk to us about your options. Our goal is to provide value that makes you want to continue, not to lock you into something that doesn't work for you."
    }
]


FAQ_BANKS = {
    "residential": RESIDENTIAL_FAQS,
    "commercial": COMMERCIAL_FAQS,
    "emergency": EMERGENCY_FAQS,
    "repair": REPAIR_FAQS,
    "installation": INSTALLATION_FAQS,
    "maintenance": MAINTENANCE_FAQS
}


def get_faq_bank(hub_key: str) -> List[Dict]:
    """Get FAQ bank for a specific hub type."""
    return FAQ_BANKS.get(hub_key, RESIDENTIAL_FAQS)


def get_faqs_for_hub(hub_key: str, count: int = 8) -> List[Dict]:
    """
    Get a specified number of FAQs for a hub type.
    Returns up to 'count' FAQs, defaults to 8.
    """
    bank = get_faq_bank(hub_key)
    return bank[:min(count, len(bank))]


def validate_faq_uniqueness() -> Dict[str, List[str]]:
    """
    Validate that no FAQ questions appear in multiple hub types.
    Returns dict of duplicate questions if any found.
    """
    all_questions = {}
    duplicates = {}
    
    for hub_key, faqs in FAQ_BANKS.items():
        for faq in faqs:
            question = faq["question"]
            if question in all_questions:
                if question not in duplicates:
                    duplicates[question] = [all_questions[question]]
                duplicates[question].append(hub_key)
            else:
                all_questions[question] = hub_key
    
    return duplicates
