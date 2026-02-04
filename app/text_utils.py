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
