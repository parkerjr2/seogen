"""
Shared text processing utilities for AI content generation.
Used across all generators to ensure consistent text quality.
"""

import re


# Vertical-specific language mappings for audience and property terminology
VERTICAL_LANGUAGE = {
    'residential': {
        'audience': 'homeowners',
        'audience_singular': 'homeowner',
        'property': 'homes',
        'property_singular': 'home',
        'surge_protection': 'whole-home',
    },
    'commercial': {
        'audience': 'businesses',
        'audience_singular': 'business',
        'property': 'facilities',
        'property_singular': 'facility',
        'surge_protection': 'commercial',
    },
}


def get_vertical_language(hub_key: str) -> dict:
    """
    Get language mappings for a hub type.

    Args:
        hub_key: Hub type ('residential', 'commercial')

    Returns:
        Dictionary with audience and property terminology
    """
    if not hub_key:
        return VERTICAL_LANGUAGE['residential']
    return VERTICAL_LANGUAGE.get(hub_key.lower(), VERTICAL_LANGUAGE['residential'])


def fix_residential_language(text: str, hub_key: str) -> str:
    """
    Replace residential language with vertical-appropriate language.
    Only applies replacements when hub_key is NOT residential.

    This is a post-processing safety net to catch cases where the LLM
    ignores prompt instructions and still outputs residential terminology
    in commercial content.

    Args:
        text: The text to fix
        hub_key: Hub type ('residential', 'commercial')

    Returns:
        Text with vertical-appropriate language (unchanged for residential)
    """
    if not hub_key or hub_key.lower() == 'residential':
        return text  # No changes for residential

    target = get_vertical_language(hub_key)

    # Replacements ordered: phrases first (longer matches), then words (shorter)
    replacements = [
        # Context-specific phrases (process before word-level to avoid partial matches)
        (r'\bin homes built\b', 'in facilities built'),
        (r'\bin homes from\b', 'in facilities from'),
        (r'\bfor homes\b', 'for facilities'),
        (r'\bthese homes\b', 'these facilities'),
        (r'\bolder homes\b', 'older commercial properties'),
        (r'\bmany homes\b', 'many commercial properties'),
        (r'\brewire homes\b', 'rewire facilities'),
        (r'\bmodernize homes\b', 'modernize facilities'),
        (r'\bhome systems\b', 'building systems'),
        (r'\bhome electrical\b', 'electrical'),

        # Plural forms
        (r'\bhomeowners\b', target['audience']),
        (r'\bHomeowners\b', target['audience'].title()),
        (r'\bhomes\b', target['property']),
        (r'\bHomes\b', target['property'].title()),
        (r'\bhouses\b', 'buildings'),
        (r'\bHouses\b', 'Buildings'),
        (r'\bfamilies\b', 'businesses'),
        (r'\bFamilies\b', 'Businesses'),

        # Singular forms
        (r'\bhomeowner\b', target['audience_singular']),
        (r'\bHomeowner\b', target['audience_singular'].title()),
        (r'\bhome\b', target['property_singular']),
        (r'\bHome\b', target['property_singular'].title()),
        (r'\bhouse\b', 'building'),
        (r'\bHouse\b', 'Building'),

        # Possessive forms
        (r"\bfamily's\b", "business's"),
        (r"\bFamily's\b", "Business's"),

        # Specific phrases
        (r'\bwhole-home\b', target['surge_protection']),
        (r'\bWhole-home\b', target['surge_protection'].title()),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return text


def validate_grammar(text: str, city: str = "") -> str:
    """
    Fix common grammar issues in AI-generated content.
    Generic rules that work across all trades and cities.

    Args:
        text: The text to validate and fix
        city: Optional city name for context-aware fixes

    Returns:
        Text with grammar issues fixed
    """
    # Rule 1: Subject-Verb Agreement for compound subjects
    # "X and Y creates" → "X and Y create"
    compound_verbs = ['creates', 'causes', 'damages', 'leads', 'results', 'affects', 'requires', 'needs']
    for verb in compound_verbs:
        # Match: [word] and [word(s)] [singular verb]
        pattern = rf'(\w+)\s+and\s+(\w+(?:\s+\w+)?)\s+{verb}\b'
        plural_verb = verb.rstrip('s')  # creates → create
        text = re.sub(pattern, rf'\1 and \2 {plural_verb}', text, flags=re.IGNORECASE)

    # Rule 1.5: Equipment is always singular (uncountable noun)
    text = re.sub(r'\bequipment are\b', 'equipment is', text, flags=re.IGNORECASE)
    text = re.sub(r'\bequipment were\b', 'equipment was', text, flags=re.IGNORECASE)

    # Rule 2: Incomplete comparatives
    text = re.sub(r'\bfrom older in\b', 'in older', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfor homes from older\b', 'in older homes', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfrom older,', 'from an older era,', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfrom older\.', 'from an older era.', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfrom newer in\b', 'in newer', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfrom newer,', 'from a newer era,', text, flags=re.IGNORECASE)

    # Rule 3: Missing relative pronouns
    # "have old wiring creates" → "have old wiring that creates"
    verbs_needing_that = ['creates', 'causes', 'leads', 'results', 'affects', 'requires']
    for verb in verbs_needing_that:
        pattern = rf'\b(have|has)\s+(\w+(?:\s+\w+)?)\s+({verb})\b'
        text = re.sub(pattern, rf'\1 \2 that \3', text, flags=re.IGNORECASE)

    # Rule 4: Article agreement (a/an)
    # "a older" → "an older"
    text = re.sub(r'\ba\s+(older|aging|electrical|original|outdated|urgent|unusual|early|easy)\b', r'an \1', text, flags=re.IGNORECASE)
    # "an system" → "a system"
    text = re.sub(r'\ban\s+(system|service|property|home|panel|circuit|building|business|commercial)\b', r'a \1', text, flags=re.IGNORECASE)

    # Rule 5: Double words
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text)

    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize various whitespace characters to standard spaces.
    AI models sometimes output non-breaking spaces or other Unicode whitespace.

    Args:
        text: The text to normalize

    Returns:
        Text with normalized whitespace
    """
    text = text.replace('\u00a0', ' ')  # non-breaking space
    text = text.replace('\u2007', ' ')  # figure space
    text = text.replace('\u202f', ' ')  # narrow no-break space
    text = text.replace('\u2009', ' ')  # thin space
    text = text.replace('\u200a', ' ')  # hair space
    return text


def fix_banned_phrases(text: str, city: str) -> str:
    """
    Replace common banned phrases with city-specific alternatives.

    Args:
        text: The text to fix
        city: The city name to use as replacement

    Returns:
        Text with banned phrases replaced
    """
    # Normalize whitespace first
    text = normalize_whitespace(text)

    # Pattern 1: Standard "in the area" with regex
    text = re.sub(r'\bin\s+the\s+area\b', f'in {city}', text, flags=re.IGNORECASE)

    # Pattern 2: Just "the area" at word boundaries
    text = re.sub(r'\bthe\s+area\b', city, text, flags=re.IGNORECASE)

    # Pattern 3: Literal string replacements for common cases
    text = text.replace('In the area', f'In {city}')
    text = text.replace('in the area', f'in {city}')
    text = text.replace('IN THE AREA', f'IN {city}')

    # Pattern 4: Edge cases with context prefixes
    text = text.replace(' In the area', f' In {city}')
    text = text.replace(', In the area', f', In {city}')
    text = text.replace('. In the area', f'. In {city}')
    text = text.replace(' in the area', f' in {city}')
    text = text.replace(', in the area', f', in {city}')
    text = text.replace('. in the area', f'. in {city}')

    # Pattern 5: Common phrases that trigger "in the area"
    text = re.sub(r'\blandmarks\s+[Ii]n\s+the\s+area\b', f'landmarks in {city}', text)
    text = re.sub(r'\bproperties\s+[Ii]n\s+the\s+area\b', f'properties in {city}', text)
    text = re.sub(r'\bcalls\s+[Ii]n\s+the\s+area\b', f'calls in {city}', text)
    text = re.sub(r'\bhomes\s+[Ii]n\s+the\s+area\b', f'homes in {city}', text)
    text = re.sub(r'\bbusinesses\s+[Ii]n\s+the\s+area\b', f'businesses in {city}', text)
    text = re.sub(r'\bfacilities\s+[Ii]n\s+the\s+area\b', f'facilities in {city}', text)
    text = re.sub(r'\bclimate\s+[Ii]n\s+the\s+area\b', f'climate in {city}', text)

    # Pattern 6: After newlines or line breaks
    text = re.sub(r'\n\s*[Ii]n the area,', f'\nIn {city},', text)

    # Pattern 7: After "such as" or "including"
    text = re.sub(r'(such as|including)\s+[Ii]n\s+the\s+area', rf'\1 in {city}', text, flags=re.IGNORECASE)

    # Pattern 8: Within parentheses
    text = re.sub(r'\(\s*[Ii]n\s+the\s+area\s*\)', f'(in {city})', text)

    return text


def fix_incomplete_sentences(text: str) -> str:
    """
    Fix incomplete sentences that end with dangling noun phrases.
    LLM sometimes generates sentences like:
    "...due to severe thunderstorms and urban heat island effect."
    which should end with a verb completing the causal relationship.

    Args:
        text: The text to fix

    Returns:
        Text with incomplete sentences fixed
    """
    # Pattern 1: Ends with "due to [noun phrase] and [noun phrase]." without verb
    # e.g., "...due to severe storms and heat island effect."
    def add_completion_due_to(match):
        phrase = match.group(1) + match.group(2)
        # Check if it already ends with a verb phrase
        ending_verbs = ['create', 'cause', 'lead', 'result', 'affect', 'require', 'strain', 'stress', 'damage']
        has_verb = any(verb in phrase.lower() for verb in ending_verbs)
        if not has_verb:
            return f'{phrase} that create added strain on systems.'
        return match.group(0)

    # Match: "due to [stuff] and [stuff]." where [stuff] doesn't contain a verb
    pattern = r'(due to [^.]+?)((?:and|or) [^.]+?)(\.)(?=\s|$)'
    text = re.sub(pattern, add_completion_due_to, text)

    # Pattern 2: Ends with "where [noun] and [noun]." without verb
    # e.g., "...where severe storms and heat."
    def add_completion_where(match):
        phrase = match.group(1)
        ending_verbs = ['create', 'cause', 'lead', 'result', 'affect', 'require', 'occur', 'happen']
        has_verb = any(verb in phrase.lower() for verb in ending_verbs)
        if not has_verb and ' and ' in phrase:
            return f'{phrase} create unique challenges.'
        return match.group(0)

    pattern = r'(where [^.]+?)(\.)(?=\s|$)'
    text = re.sub(pattern, add_completion_where, text)

    # Pattern 3: Ends with "especially in [location] due to [factor]." without completion
    # e.g., "...especially in Elm Creek due to storms."
    def add_completion_especially(match):
        phrase = match.group(1)
        if 'due to' in phrase.lower():
            ending_verbs = ['create', 'cause', 'lead', 'result', 'affect', 'require', 'strain']
            has_verb = any(verb in phrase.lower() for verb in ending_verbs)
            if not has_verb:
                return f'{phrase} which create added service demands.'
        return match.group(0)

    pattern = r'(especially in [^.]+?)(\.)(?=\s|$)'
    text = re.sub(pattern, add_completion_especially, text)

    return text
