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

    # Final safety net: case-insensitive replacements for critical terms
    # This catches any remaining variations (ALL CAPS, mixed case, etc.)
    text = re.sub(r'\bhomeowners\b', target['audience'], text, flags=re.IGNORECASE)
    text = re.sub(r'\bhomeowner\b', target['audience_singular'], text, flags=re.IGNORECASE)

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
    Normalize various whitespace and invisible characters to standard spaces.
    AI models sometimes output non-breaking spaces, zero-width characters,
    or other Unicode artifacts that break regex matching.

    Args:
        text: The text to normalize

    Returns:
        Text with normalized whitespace
    """
    # Step 1: Remove zero-width characters entirely (they're invisible but break word boundaries)
    zero_width_chars = [
        '\u200b',  # zero-width space
        '\u200c',  # zero-width non-joiner
        '\u200d',  # zero-width joiner
        '\ufeff',  # zero-width no-break space (BOM)
    ]
    for char in zero_width_chars:
        text = text.replace(char, '')

    # Step 2: Normalize all Unicode whitespace to standard space
    unicode_spaces = [
        '\u00a0',  # non-breaking space
        '\u2002',  # en space
        '\u2003',  # em space
        '\u2004',  # three-per-em space
        '\u2005',  # four-per-em space
        '\u2006',  # six-per-em space
        '\u2007',  # figure space
        '\u2008',  # punctuation space
        '\u2009',  # thin space
        '\u200a',  # hair space
        '\u202f',  # narrow no-break space
        '\u205f',  # medium mathematical space
    ]
    for space in unicode_spaces:
        text = text.replace(space, ' ')

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

    # Pattern 2.5: Possessive form "the area's"
    text = re.sub(r"\bthe\s+area's\b", f"{city}'s", text, flags=re.IGNORECASE)

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

    # Pattern 6.5: After double newlines (section breaks) - more aggressive
    text = re.sub(r'(\n\n+)\s*[Ii]n the area', rf'\1In {city}', text)

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


def fix_passive_voice(text: str) -> str:
    """
    Fix common passive voice constructions in AI-generated content.
    Targets the most frequent passive patterns that LLMs produce.

    This is a best-effort post-processing pass. It catches mechanical
    passive constructions but won't catch every instance. The prompt-level
    instructions are the primary defense; this is a safety net.

    Args:
        text: The text to fix

    Returns:
        Text with common passive voice patterns converted to active voice
    """
    # Helper to pick singular/plural verb based on whether new subject ends in 's'
    def _verb_form(new_subject: str, singular: str, plural: str) -> str:
        """Pick verb form based on likely plurality of new subject."""
        subj = new_subject.strip().lower()
        # Common plural indicators: ends in 's' but not 'ss' (e.g., "storms" but not "stress")
        if subj.endswith('s') and not subj.endswith('ss') and not subj.endswith('us'):
            return plural
        return singular

    # Pattern 1: "X is/are caused by Y" → "Y causes/cause X"
    # e.g., "Damage is caused by storms" → "Storms cause damage"
    text = re.sub(
        r'\b([A-Z][a-z]+(?:\s+\w+)?)\s+(?:is|are)\s+(often\s+)?caused\s+by\s+(\w+(?:\s+\w+)?)',
        lambda m: f'{m.group(3).capitalize()} {m.group(2) or ""}{_verb_form(m.group(3), "causes", "cause")} {m.group(1).lower()}',
        text
    )

    # Pattern 2: "X is/are affected by Y" → "Y affects/affect X"
    text = re.sub(
        r'\b([A-Z][a-z]+(?:\s+\w+)?)\s+(?:is|are)\s+(often\s+)?affected\s+by\s+(\w+(?:\s+\w+)?)',
        lambda m: f'{m.group(3).capitalize()} {m.group(2) or ""}{_verb_form(m.group(3), "affects", "affect")} {m.group(1).lower()}',
        text
    )

    # Pattern 3: "X is/are damaged by Y" → "Y damages/damage X"
    text = re.sub(
        r'\b([A-Z][a-z]+(?:\s+\w+)?)\s+(?:is|are)\s+(often\s+)?damaged\s+by\s+(\w+(?:\s+\w+)?)',
        lambda m: f'{m.group(3).capitalize()} {m.group(2) or ""}{_verb_form(m.group(3), "damages", "damage")} {m.group(1).lower()}',
        text
    )

    # Pattern 4: "is known for" → "sees frequent" (common in city descriptions)
    text = re.sub(r'\bis known for\b', 'sees frequent', text, flags=re.IGNORECASE)

    # Pattern 5: "is/are required by" → invert
    # e.g., "Permits are required by the city" → "The city requires permits"
    text = re.sub(
        r'\b([A-Z][a-z]+(?:\s+\w+)?)\s+(?:is|are)\s+required\s+by\s+(the\s+\w+|\w+)',
        lambda m: f'{m.group(2).capitalize()} requires {m.group(1).lower()}',
        text
    )

    # Pattern 6: "can be found" → "exist" or "appear"
    text = re.sub(r'\bcan be found\b', 'appear', text, flags=re.IGNORECASE)

    # Pattern 7: "is/are typically seen" → "typically appears/appear"
    text = re.sub(r'\bis typically seen\b', 'typically appears', text, flags=re.IGNORECASE)
    text = re.sub(r'\bare typically seen\b', 'typically appear', text, flags=re.IGNORECASE)

    # Pattern 8: "is/are recommended" → "we recommend" (service context)
    text = re.sub(r'\bit is recommended\b', 'we recommend', text, flags=re.IGNORECASE)
    text = re.sub(r'\bis recommended\b', 'works best', text, flags=re.IGNORECASE)

    return text


def count_passive_sentences(text: str) -> dict:
    """
    Count passive voice usage in text for validation/reporting.

    Args:
        text: The text to analyze

    Returns:
        Dictionary with 'total_sentences', 'passive_count', 'passive_percentage',
        and 'passive_sentences' (list of flagged sentences)
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if len(s) > 5]  # filter fragments

    passive_patterns = [
        r'\b(?:is|are|was|were|been|being)\s+\w+ed\b',  # "is damaged", "are affected"
        r'\b(?:is|are|was|were|been|being)\s+\w+en\b',  # "is broken", "are taken"
        r'\b(?:is|are|was|were)\s+(?:often|typically|usually|commonly|frequently)\s+\w+ed\b',
        r'\bcan be \w+ed\b',  # "can be fixed"
        r'\bshould be \w+ed\b',  # "should be replaced"
        r'\bmust be \w+ed\b',  # "must be inspected"
        r'\bit is recommended\b',
        r'\bis known for\b',
    ]

    passive_sentences = []
    for sentence in sentences:
        for pattern in passive_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                passive_sentences.append(sentence)
                break

    total = len(sentences)
    passive_count = len(passive_sentences)
    percentage = (passive_count / total * 100) if total > 0 else 0

    return {
        'total_sentences': total,
        'passive_count': passive_count,
        'passive_percentage': round(percentage, 1),
        'passive_sentences': passive_sentences,
    }


def count_long_sentences(text: str, max_words: int = 20) -> dict:
    """
    Count sentences exceeding the word limit for Yoast readability.

    Args:
        text: The text to analyze
        max_words: Maximum words per sentence (Yoast default: 20)

    Returns:
        Dictionary with 'total_sentences', 'long_count', 'long_percentage',
        and 'long_sentences' (list of flagged sentences)
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if len(s) > 5]

    long_sentences = []
    for sentence in sentences:
        word_count = len(sentence.split())
        if word_count > max_words:
            long_sentences.append(sentence)

    total = len(sentences)
    long_count = len(long_sentences)
    percentage = (long_count / total * 100) if total > 0 else 0

    return {
        'total_sentences': total,
        'long_count': long_count,
        'long_percentage': round(percentage, 1),
        'long_sentences': long_sentences,
    }


def split_long_sentences(text: str, max_words: int = 20) -> str:
    """
    Split sentences exceeding max_words at natural conjunction points.
    Targets Yoast SEO readability: ≤25% of sentences over 20 words.

    Splits at these conjunctions (in priority order):
    1. ", which " → ". This "
    2. ", and " → ". Also, " or ". "
    3. ", but " → ". However, "
    4. ", while " → ". Meanwhile, "
    5. ", where " → ". There, "
    6. ", because " → ". This is because "
    7. ", so " → ". As a result, "
    8. ", although " → ". Although "

    Only splits if BOTH resulting halves would be ≥5 words (avoids fragments).

    Args:
        text: The text to process
        max_words: Maximum words per sentence (default: 20)

    Returns:
        Text with long sentences split at natural points
    """
    # Split points ordered by priority (most natural splits first)
    split_points = [
        (', which ', '. This '),
        (', and ', '. '),
        (', but ', '. However, '),
        (', while ', '. Meanwhile, '),
        (', where ', '. There, '),
        (', because ', '. This is because '),
        (', so ', '. As a result, '),
        (', although ', '. Although '),
        # Also handle without leading comma (mid-sentence conjunctions)
        (' which ', '. This '),
        (' and ', '. '),
        (' but ', '. However, '),
        # Relative clauses (lower priority, only for very long sentences)
        (', who ', '. They '),
        (', where ', '. There, '),
        (' that frequently ', '. This frequently '),
    ]

    # Process sentence by sentence
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    result_sentences = []

    for sentence in sentences:
        word_count = len(sentence.split())

        if word_count <= max_words:
            result_sentences.append(sentence)
            continue

        # Try each split point
        split_done = False
        for pattern, replacement in split_points:
            pattern_lower = pattern.lower()
            sentence_lower = sentence.lower()

            if pattern_lower not in sentence_lower:
                continue

            # Find the split position (case-insensitive)
            idx = sentence_lower.find(pattern_lower)
            if idx < 0:
                continue

            before = sentence[:idx].strip()
            after = sentence[idx + len(pattern):].strip()

            before_words = len(before.split())
            after_words = len(after.split())

            # Only split if both halves are substantial (avoid fragments)
            if before_words < 5 or after_words < 5:
                continue

            # Ensure 'before' ends with a period
            if not before.endswith('.'):
                before = before + '.'

            # Capitalize the start of the new sentence
            if replacement.strip() == '.':
                # Simple split: just capitalize 'after'
                after = after[0].upper() + after[1:] if after else after
                result_sentences.append(before)
                # Recursively check the second half too
                if len(after.split()) > max_words:
                    after = split_long_sentences(after, max_words)
                result_sentences.append(after)
            else:
                # Replacement includes a transition word
                transition = replacement.strip().lstrip('. ').rstrip()
                # Ensure space between transition and continuation text
                if after:
                    after_lower = after[0].lower() + after[1:]
                    after_sentence = f'{transition} {after_lower}'
                else:
                    after_sentence = transition
                if after_sentence and not after_sentence[0].isupper():
                    after_sentence = after_sentence[0].upper() + after_sentence[1:]
                result_sentences.append(before)
                if len(after_sentence.split()) > max_words:
                    after_sentence = split_long_sentences(after_sentence, max_words)
                result_sentences.append(after_sentence)

            split_done = True
            break

        if not split_done:
            # No good split point found - keep as-is rather than create awkward breaks
            result_sentences.append(sentence)

    return ' '.join(result_sentences)
