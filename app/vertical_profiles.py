"""
Vertical-specific profiles for different home service businesses.
Maps business verticals to trade-specific vocabulary and characteristics.
"""

VERTICAL_PROFILES = {
    "roofer": {
        "trade_name": "roofing",
        "vocabulary": ["shingles", "flashing", "underlayment", "vents", "decking", "ridge", "valley", 
                      "eave", "rake", "drip edge", "ice dam", "membrane", "felt paper"],
        "common_services": ["roof repair", "roof replacement", "roof inspection", "leak repair", "storm damage repair"],
    },
    "electrician": {
        "trade_name": "electrical",
        "vocabulary": ["breaker", "circuit", "panel", "outlet", "wiring", "voltage", "amp", "fuse", 
                      "junction", "conduit", "ground", "neutral", "hot wire", "gfci", "afci"],
        "common_services": ["outlet installation", "panel upgrade", "lighting repair", "wiring", "electrical inspection"],
    },
    "plumber": {
        "trade_name": "plumbing",
        "vocabulary": ["pipe", "drain", "trap", "valve", "fixture", "water pressure", "sewer line", 
                      "shutoff", "coupling", "elbow", "tee", "gasket", "flange"],
        "common_services": ["drain cleaning", "pipe repair", "water heater installation", "leak repair", "fixture installation"],
    },
    "hvac": {
        "trade_name": "HVAC",
        "vocabulary": ["compressor", "condenser", "evaporator", "refrigerant", "ductwork", "thermostat", 
                      "filter", "blower", "coil", "heat exchanger", "airflow", "tonnage", "seer"],
        "common_services": ["AC repair", "furnace repair", "HVAC installation", "duct cleaning", "maintenance"],
    },
    "landscaper": {
        "trade_name": "landscaping",
        "vocabulary": ["irrigation", "mulch", "sod", "drainage", "grading", "hardscape", "softscape",
                      "edging", "pruning", "fertilization", "aeration", "seeding"],
        "common_services": ["lawn care", "landscape design", "tree trimming", "irrigation installation", "hardscaping"],
    },
    "handyman": {
        "trade_name": "handyman services",
        "vocabulary": ["repair", "installation", "maintenance", "fixture", "drywall", "painting",
                      "assembly", "carpentry", "hardware", "trim", "caulking"],
        "common_services": ["general repairs", "furniture assembly", "drywall repair", "painting", "fixture installation"],
    },
    "painter": {
        "trade_name": "painting",
        "vocabulary": ["primer", "finish coat", "brush", "roller", "sprayer", "tape", "drop cloth",
                      "caulk", "sanding", "prep work", "sheen", "coverage"],
        "common_services": ["interior painting", "exterior painting", "cabinet painting", "deck staining", "drywall repair"],
    },
    "concrete": {
        "trade_name": "concrete",
        "vocabulary": ["rebar", "aggregate", "slump", "cure", "expansion joint", "control joint", 
                      "trowel", "float", "pour", "mix", "psi", "footing"],
        "common_services": ["driveway installation", "patio installation", "foundation repair", "concrete repair", "stamped concrete"],
    },
    "siding": {
        "trade_name": "siding",
        "vocabulary": ["lap", "j-channel", "soffit", "fascia", "trim", "flashing", "vapor barrier", 
                      "starter strip", "corner post", "furring", "sheathing"],
        "common_services": ["siding installation", "siding repair", "siding replacement", "trim work", "soffit repair"],
    },
    "locksmith": {
        "trade_name": "locksmith services",
        "vocabulary": ["deadbolt", "cylinder", "key", "lock", "rekey", "master key", "strike plate",
                      "latch", "tumbler", "pin", "keyway", "lockset"],
        "common_services": ["lock installation", "rekeying", "lockout service", "key duplication", "security upgrades"],
    },
    "cleaning": {
        "trade_name": "cleaning services",
        "vocabulary": ["sanitize", "disinfect", "vacuum", "mop", "dust", "scrub", "polish",
                      "deodorize", "deep clean", "surface", "solution", "equipment"],
        "common_services": ["house cleaning", "deep cleaning", "move-out cleaning", "commercial cleaning", "carpet cleaning"],
    },
    "garage-door": {
        "trade_name": "garage door",
        "vocabulary": ["opener", "spring", "track", "roller", "cable", "sensor", "panel",
                      "torsion spring", "extension spring", "remote", "keypad", "motor"],
        "common_services": ["garage door repair", "spring replacement", "opener installation", "door installation", "maintenance"],
    },
    "windows": {
        "trade_name": "window services",
        "vocabulary": ["sash", "frame", "pane", "glazing", "weatherstripping", "sill", "jamb", 
                      "mullion", "casing", "flashing", "argon", "low-e", "u-factor"],
        "common_services": ["window installation", "window replacement", "window repair", "glass replacement", "weatherproofing"],
    },
    "pest-control": {
        "trade_name": "pest control",
        "vocabulary": ["treatment", "inspection", "barrier", "bait", "trap", "spray", "fumigation",
                      "prevention", "infestation", "extermination", "monitoring", "exclusion"],
        "common_services": ["pest inspection", "termite treatment", "rodent control", "insect control", "preventative treatment"],
    },
    "other": {
        "trade_name": "home services",
        "vocabulary": ["repair", "installation", "maintenance", "service", "inspection", "upgrade",
                      "replacement", "improvement", "solution", "quality", "professional"],
        "common_services": ["general services", "repairs", "installations", "maintenance", "inspections"],
    },
}

def get_vertical_profile(vertical: str) -> dict:
    """
    Get the profile for a specific vertical.
    
    Args:
        vertical: The business vertical key
        
    Returns:
        Dictionary with trade_name, vocabulary, and common_services
    """
    return VERTICAL_PROFILES.get(vertical, VERTICAL_PROFILES["other"])

def get_trade_name(vertical: str) -> str:
    """Get the trade name for a vertical."""
    profile = get_vertical_profile(vertical)
    return profile.get("trade_name", "home services")

def get_vocabulary(vertical: str) -> list:
    """Get trade-specific vocabulary for a vertical."""
    profile = get_vertical_profile(vertical)
    return profile.get("vocabulary", [])
