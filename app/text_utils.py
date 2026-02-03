"""
Shared text processing utilities for AI content generation.
Used across all generators to ensure consistent text quality.
"""

import re


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

    # Replace "in the area" variants
    text = re.sub(r'\bin\s+the\s+area\b', f'in {city}', text, flags=re.IGNORECASE)
    text = re.sub(r'\bthe\s+area\b', city, text, flags=re.IGNORECASE)
    text = text.replace('In the area', f'In {city}')
    text = text.replace('in the area', f'in {city}')
    text = text.replace('IN THE AREA', f'IN {city}')

    return text
