"""
Robust LLM-backed API for SEO-optimized local service pages.
Implements programmatic enforcement, validation, and repair passes.

Updates in this version (SEO-quality fixes):
- Adds validations for: (1) local differentiators, (2) field-insight density, (3) broader-area sentence,
  (4) observable outcomes in Section 4, (5) overly-generic/templated H2 headings.
- Tightens prompts to reduce “interchangeable template” feel (stronger local proof signals + non-generic headings).
- Fixes a prompt contradiction: removed “homeowners typically notice…” from repair prompt (was banned by anti-symmetry).
"""

import json
import re
import os
from typing import Dict, Any, List
import httpx

from app.config import settings
from app.models import (
    PageData,
    GeneratePageResponse,
    PageBlock,
    HeadingBlock,
    ParagraphBlock,
    FAQBlock,
    NAPBlock,
    CTABlock,
)


class AIContentGenerator:
    """Robust content generator with programmatic enforcement and repair capabilities."""

    # Forbidden meta-language phrases (case-insensitive)
    FORBIDDEN_PHRASES = [
        "seo",
        "keyword",
        "word count",
        "structure",
        "first 100 words",
        "this page",
        "this article",
        "in this section",
    ]

    # Forbidden marketing filler phrases (case-insensitive)
    FORBIDDEN_MARKETING_FILLER = [
        "top-notch",
        "premier",
        "high-quality solutions",
        "trusted experts",
        "we understand the importance of",
        "industry-leading",
        "best-in-class",
        "cutting-edge",
        "state-of-the-art",
        "world-class",
        "best in the area",
        "leading provider",
        "your trusted",
        "your go-to",
        "number one choice",
    ]

    # Forbidden regional references and unsafe location language (case-insensitive)
    FORBIDDEN_REGION_PHRASES = [
        "south florida",
        "miami-dade",
        "broward",
        "salt air",
        "coastal",
    ]

    # Extra: headings that commonly signal templated/AI content (case-insensitive)
    # We don't forbid useful words like "process" outright; we forbid common generic frames.
    FORBIDDEN_GENERIC_HEADING_FRAGMENTS = [
        "understanding ",
        "reliable ",
        "quality ",
        "why choose",
        "trusted ",
        "premier ",
        "top-notch ",
        "best-in-class ",
        "world-class ",
        "common service needs",
        "service needs in ",
    ]

    # Trade vocabulary by service category (for validation)
    TRADE_VOCABULARY = {
        "electrical": [
            "breaker",
            "circuit",
            "panel",
            "outlet",
            "wiring",
            "voltage",
            "amp",
            "fuse",
            "junction",
            "conduit",
            "ground",
            "neutral",
            "hot wire",
            "gfci",
            "afci",
        ],
        "gutter": [
            "downspout",
            "fascia",
            "pitch",
            "water flow",
            "debris",
            "soffit",
            "elbow",
            "splash block",
            "gutter guard",
            "seam",
            "hanger",
            "end cap",
            "overflow",
        ],
        "roofing": [
            "shingles",
            "flashing",
            "underlayment",
            "vents",
            "decking",
            "ridge",
            "valley",
            "eave",
            "rake",
            "drip edge",
            "ice dam",
            "membrane",
            "felt paper",
        ],
        "hvac": [
            "compressor",
            "condenser",
            "evaporator",
            "refrigerant",
            "ductwork",
            "thermostat",
            "filter",
            "blower",
            "coil",
            "heat exchanger",
            "airflow",
            "tonnage",
            "seer",
        ],
        "plumbing": [
            "pipe",
            "drain",
            "trap",
            "valve",
            "fixture",
            "water pressure",
            "sewer line",
            "shutoff",
            "coupling",
            "elbow",
            "tee",
            "gasket",
            "flange",
        ],
        "window": [
            "sash",
            "frame",
            "pane",
            "glazing",
            "weatherstripping",
            "sill",
            "jamb",
            "mullion",
            "casing",
            "flashing",
            "argon",
            "low-e",
            "u-factor",
        ],
        "door": [
            "threshold",
            "jamb",
            "weatherstripping",
            "deadbolt",
            "strike plate",
            "hinge",
            "sweep",
            "lockset",
            "frame",
            "sill",
            "casing",
            "astragal",
        ],
        "siding": [
            "lap",
            "j-channel",
            "soffit",
            "fascia",
            "trim",
            "flashing",
            "vapor barrier",
            "starter strip",
            "corner post",
            "furring",
            "sheathing",
        ],
        "concrete": [
            "rebar",
            "aggregate",
            "slump",
            "cure",
            "expansion joint",
            "control joint",
            "trowel",
            "float",
            "pour",
            "mix",
            "psi",
            "footing",
        ],
        "fence": [
            "post",
            "rail",
            "picket",
            "cap",
            "bracket",
            "gate",
            "latch",
            "hinge",
            "concrete footing",
            "stringer",
            "panel",
            "post hole",
        ],
    }

    # Local differentiator phrases/patterns that are "safe" (no neighborhoods/counties).
    # We count occurrences to ensure the page isn't interchangeable across cities.
    LOCAL_DIFFERENTIATORS = {
        "home_style": [
            r"\bolder homes\b",
            r"\bnewer subdivisions\b",
            r"\bhomes built (in|around) the (80s|90s)\b",
            r"\bslab-on-grade\b",
            r"\bslab on grade\b",
            r"\bpier-and-beam\b",
            r"\bpier and beam\b",
        ],
        "maintenance": [
            r"\btree debris\b",
            r"\bcleanouts?\b",
            r"\bclog(?:ged|s|ging)\b",
            r"\bdiy extensions?\b",
            r"\bleaf(?:s)?\b",
            r"\bneedles?\b",
        ],
        "construction": [
            r"\blong runs?\b",
            r"\broofline\b",
            r"\bdownspout placement\b",
            r"\battachment points?\b",
            r"\bhangers?\b",
            r"\bend caps?\b",
        ],
        # Weather is state-scoped elsewhere; we still count it as a differentiator signal
        "weather": [
            r"\bheavy rain\b",
            r"\bstorms?\b",
            r"\bwind\b",
            r"\bhail\b",
            r"\bheat\b",
            r"\bdownpour\b",
        ],
        # Mechanics: ties environment -> physical failure modes (highly valuable signal)
        "mechanics": [
            r"\bexpansion\b",
            r"\bpitch drift\b",
            r"\boverflow points?\b",
            r"\bseam separation\b",
            r"\bhanger loosening\b",
            r"\bsag(?:ging)?\b",
        ],
    }

    # Markers that suggest real “field insight” rather than generic marketing
    # (We count marker occurrences, not exact sentence templates.)
    FIELD_INSIGHT_MARKERS = [
        "what brings most calls",
        "a common call is",
        "a frequent issue is",
        "the first sign",
        "one of the first things",
        "we see a lot",
        "we see this when",
        "we hear this when",
        "it usually shows up as",
        "after a heavy",
        "after storms",
        "during a downpour",
        "spring storms",
        "a quick way to tell",
        "the telltale sign",
        "the typical failure point",
    ]

    # Observable outcomes phrases for Section 4 (must include at least 2 signals)
    OBSERVABLE_OUTCOME_MARKERS = [
        "no overflow",
        "end cap",
        "splash block",
        "no staining",
        "fascia",
        "no pooling",
        "discharges",
        "water flows",
        "water runs",
        "stays dry",
        "doesn't spill",
        "doesn’t spill",
    ]

    def __init__(self):
        """Initialize with OpenAI configuration."""
        self.api_key = settings.openai_api_key
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.base_url = "https://api.openai.com/v1"

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

    def generate_page_content(self, data: PageData) -> GeneratePageResponse:
        """
        Generate robust SEO-optimized content with validation and repair passes.

        Raises:
            Exception: If generation and repair both fail
        """
        try:
            content_json = self._call_openai_generation(data)
            response = self._assemble_response(content_json, data)

            validation_errors = self._validate_output(response, data)

            if validation_errors:
                print(f"Validation failed: {validation_errors}")
                repaired_content = self._repair_output(content_json, validation_errors, data)
                response = self._assemble_response(repaired_content, data)

                final_validation_errors = self._validate_output(response, data)
                if final_validation_errors:
                    raise Exception(
                        f"Content generation failed validation even after repair: {final_validation_errors}"
                    )

            return response

        except Exception as e:
            raise Exception(f"AI content generation failed: {str(e)}")

    def generate_page_content_preview(self, data: PageData) -> GeneratePageResponse:
        """Generate a fast preview response (no repair loop, reduced output)."""
        try:
            content_json = self._call_openai_generation_preview(data)
            response = self._assemble_response(content_json, data)

            validation_errors = self._validate_preview_output(response, data)
            if validation_errors:
                raise Exception(f"Preview generation failed validation: {validation_errors}")

            return response
        except Exception as e:
            raise Exception(f"AI preview generation failed: {str(e)}")

    def slugify(self, service: str, city: str) -> str:
        """Generate clean slug as {service}-{city} (lowercase, hyphenated, max 60 chars)."""
        clean_service = re.sub(r"[^a-zA-Z0-9\s]", "", service.strip().lower())
        clean_city = re.sub(r"[^a-zA-Z0-9\s]", "", city.strip().lower())
        service_slug = re.sub(r"\s+", "-", clean_service)
        city_slug = re.sub(r"\s+", "-", clean_city)
        slug = f"{service_slug}-{city_slug}"
        return slug[:60].rstrip("-")

    def _call_openai_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 4000,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """Call OpenAI API via httpx and return parsed JSON."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )

                if response.status_code != 200:
                    raise Exception(f"OpenAI API error {response.status_code}: {response.text}")

                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)

        except json.JSONDecodeError as e:
            raise Exception(f"OpenAI returned invalid JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")

    def _call_openai_generation(self, data: PageData) -> Dict[str, Any]:
        """Generate content payload using enforced local-proof + anti-template prompt."""
        system_prompt = (
            "You are a professional local service copywriter. Write natural, trustworthy marketing copy. "
            "Avoid any writing-process language. Sound like a real contractor explaining real problems."
        )

        user_prompt = f"""Generate content for a local service landing page about {data.service} using:
Service: {data.service}
City: {data.city}
State: {data.state}
Company Name: {data.company_name}
Phone: {data.phone}
Address: {data.address}

Return ONLY valid JSON with this exact structure:
{{
  "meta_description": "string",
  "sections": [
    {{ "heading": "string", "paragraph": "string" }},
    {{ "heading": "string", "paragraph": "string" }},
    {{ "heading": "string", "paragraph": "string" }},
    {{ "heading": "string", "paragraph": "string" }}
  ],
  "faqs": [
    {{ "question": "string", "answer": "string" }},
    {{ "question": "string", "answer": "string" }}
  ],
  "cta_text": "string"
}}

CRITICAL SERVICE FOCUS RULES:
Write ONLY about {data.service}. Every section must be exclusively about {data.service}.
Do NOT mention other services (e.g., roofing, shingles) unless {data.service} explicitly includes them.

HEADING QUALITY RULES (CRITICAL - AVOID GENERIC/AI HEADERS):
Each section heading must be specific and non-generic:
- Must NOT start with "Understanding", "Reliable", "Quality", "Trusted", "Why Choose Us"
- Must include at least ONE concrete noun/term tied to the work (e.g., for gutters: downspout, fascia, seam, hanger, pitch, overflow)
- Can include {data.city} in at least 2 headings, but do not force it into all of them.

CONTENT STRUCTURE (MAP PACK SUPPORT):
4 sections, each with an H2 heading and paragraph (at least 650 characters each):

SECTION 1 (LOCAL PROOF OPEN):
- Include exact service '{data.service}' and city '{data.city}' naturally near the beginning.
- Start with a customer scenario or what you see on homes (NOT brand-first).
- Include at least 2 field-insight sentences that sound like real patterns you encounter.
- CITY DIFFERENTIATION PACK: include at least 2 differentiators from safe categories:
  * Home style/build era (no neighborhoods): older homes, newer subdivisions, 80s-90s builds, slab-on-grade, pier-and-beam
  * Weather mechanics (state-safe): tie heat/hail/wind/heavy rain/storms to physical failures (expansion, pitch drift, seam separation, hanger loosening)
  * Maintenance patterns: tree debris frequency, neglected cleanouts, DIY extensions
  * Construction details: long runs, roofline complexity, downspout placement

SECTION 2 (DECISION GUIDANCE + INFORMATIONAL ASYMMETRY):
- At least 2 local differentiators
- When to act now vs monitor
- What escalates if ignored
- One insight competitors often omit (common homeowner mistake or misleading symptom)
- At least 2 field-insight sentences (use different phrasing than Section 1)
- Vary narrative order (don’t always do downspouts then elbows then outcomes)

SECTION 3 (WALKTHROUGH + FORK DECISION):
- Read like a walkthrough: what we check first and why, what we commonly find, what changes after
- FORK DECISION POINT: when a repair is enough vs sectional replacement (seam failure, sagging, fascia rot, pitch issues)
- At least 2 local differentiators
- At least 2 field-insight sentences (new phrasing again)

SECTION 4 (OBSERVABLE OUTCOMES ONLY):
- NOT "why choose us"
- Start with outcomes/scenarios people can verify:
  examples: no overflow at the end cap, water discharges at the splash block, no staining on fascia, no pooling near the foundation
- Include at least 2 field-insight sentences about outcomes/concerns you hear repeatedly
- Keep it observational, not promotional

TRADE VOCABULARY REQUIREMENT (CRITICAL):
Paragraphs 1–3 MUST each include at least 2 technical terms relevant to {data.service}.
Use terms naturally.

REDUCE EXACT-MATCH REPETITION:
Use '{data.service}' where required, but do not repeat it mechanically. Use natural substitutes.

BROADER-AREA SENTENCE (MANDATORY):
Include exactly one sentence referencing the broader area using ONLY safe terms like "nearby areas" or "the greater {data.city} area".
No counties, regions, or neighborhood names.

WEATHER SAFETY:
Weather references must be generic and safe for the given state. Do NOT mention salt air or coastal conditions.
If state is TX, only mention heat, hail, wind, heavy rain, storms.

FAQS (2):
Each FAQ answer must:
- Reference a real customer situation
- Follow CAUSE→SYMPTOM→CONSEQUENCE→RESOLUTION
- Include one local differentiator (safe categories above)
- Include one trade term
- Include "act today vs monitor" guidance
- Be at least 350 characters
- Must NOT be city-interchangeable; add city-specific context.

STRICTLY FORBIDDEN:
No HTML/markdown/bullets. No testimonials, awards, years-in-business, or invented projects.
No SEO/meta writing-process language.
No counties/neighborhoods/regions (e.g., South Florida, Midwest) and no "coastal/salt air".

Meta description must include the service and city naturally.
CTA text must include the city and the phone number.
Return JSON only. No extra text.
"""
        return self._call_openai_json(system_prompt, user_prompt)

    def _call_openai_generation_preview(self, data: PageData) -> Dict[str, Any]:
        """Generate a fast preview content payload (reduced output, no repair loop)."""
        system_prompt = (
            "You are a professional local service copywriter. Write natural, trustworthy marketing copy. "
            "Avoid any writing-process language."
        )

        user_prompt = f"""Generate a FAST preview of content for a local service landing page about {data.service} using:
Service: {data.service}
City: {data.city}
State: {data.state}
Company Name: {data.company_name}
Phone: {data.phone}
Address: {data.address}

Return ONLY valid JSON with this exact structure:
{{
  "meta_description": "string",
  "sections": [
    {{ "heading": "string", "paragraph": "string" }},
    {{ "heading": "string", "paragraph": "string" }},
    {{ "heading": "string", "paragraph": "string" }}
  ],
  "faqs": [
    {{ "question": "string", "answer": "string" }}
  ],
  "cta_text": "string"
}}

CRITICAL SERVICE FOCUS RULES:
Write ONLY about {data.service}. Stay 100% focused.

PREVIEW REQUIREMENTS:
3 sections, each with an H2 heading and paragraph (at least 320 characters):
- Section 1: include exact '{data.service}' and '{data.city}' near the beginning. Start with a customer scenario, not brand-first.
- Section 2: include at least 1 local differentiator (safe categories: home style/build era, maintenance patterns, weather mechanics).
- Section 3: include one decision guidance sentence (act now vs monitor) and at least 1 trade term.

BROADER-AREA SENTENCE (MANDATORY):
Include exactly one sentence with "nearby areas" OR "the greater {data.city} area". No neighborhoods/counties.

Do NOT use HTML/markdown/bullets.
Meta description must include the service and city naturally.
CTA text must include the city and the phone number.
Return JSON only. No extra text.
"""
        return self._call_openai_json(system_prompt, user_prompt, max_tokens=1200, timeout=45)

    # -----------------------------
    # Assembly / blocks
    # -----------------------------

    def _assemble_response(self, content_json: Dict[str, Any], data: PageData) -> GeneratePageResponse:
        """Assemble complete response with programmatic fields and minimal block schemas."""
        slug = self.slugify(data.service, data.city)
        title = f"{data.service} in {data.city}, {data.state} | {data.company_name}"
        h1_text = f"Expert {data.service} in {data.city}, {data.state}"

        blocks: List[PageBlock] = []
        blocks.append(self._create_heading_block(h1_text, 1))

        for section in content_json.get("sections", []):
            heading = (section.get("heading") or "").strip()
            paragraph = (section.get("paragraph") or "").strip()
            if heading:
                blocks.append(self._create_heading_block(heading, 2))
            if paragraph:
                blocks.append(self._create_paragraph_block(paragraph))

        for faq in content_json.get("faqs", []):
            blocks.append(self._create_faq_block((faq.get("question") or "").strip(), (faq.get("answer") or "").strip()))

        blocks.append(self._create_nap_block(data.company_name, data.address, data.phone))
        blocks.append(self._create_cta_block((content_json.get("cta_text") or "").strip(), data.phone))

        return GeneratePageResponse(
            title=title,
            meta_description=(content_json.get("meta_description") or "").strip(),
            slug=slug,
            blocks=blocks,
        )

    def _create_heading_block(self, text: str, level: int) -> HeadingBlock:
        return HeadingBlock(level=level, text=text)

    def _create_paragraph_block(self, text: str) -> ParagraphBlock:
        return ParagraphBlock(text=text)

    def _create_faq_block(self, question: str, answer: str) -> FAQBlock:
        return FAQBlock(question=question, answer=answer)

    def _create_nap_block(self, business_name: str, address: str, phone: str) -> NAPBlock:
        return NAPBlock(business_name=business_name, address=address, phone=phone)

    def _create_cta_block(self, text: str, phone: str) -> CTABlock:
        return CTABlock(text=text, phone=phone)

    # -----------------------------
    # Validation helpers
    # -----------------------------

    def _get_trade_vocabulary_for_service(self, service: str) -> List[str]:
        service_lower = service.lower()
        for category, vocab in self.TRADE_VOCABULARY.items():
            if category in service_lower:
                return vocab
        return []

    def _count_trade_terms_in_text(self, text: str, vocab: List[str]) -> int:
        text_lower = text.lower()
        return sum(1 for term in vocab if term.lower() in text_lower)

    def _count_regex_matches(self, text: str, patterns: List[str]) -> int:
        total = 0
        for p in patterns:
            if re.search(p, text, flags=re.IGNORECASE):
                total += 1
        return total

    def _local_differentiator_score(self, text: str) -> int:
        """Counts distinct local differentiator hits across safe categories."""
        score = 0
        for _, patterns in self.LOCAL_DIFFERENTIATORS.items():
            score += self._count_regex_matches(text, patterns)
        return score

    def _field_insight_score(self, text: str) -> int:
        t = text.lower()
        return sum(1 for m in self.FIELD_INSIGHT_MARKERS if m in t)

    def _observable_outcome_score(self, text: str) -> int:
        t = text.lower()
        return sum(1 for m in self.OBSERVABLE_OUTCOME_MARKERS if m in t)

    def _has_broader_area_sentence(self, combined_text: str, city: str) -> bool:
        t = combined_text.lower()
        return ("nearby areas" in t) or (f"the greater {city.lower()} area" in t)

    def _validate_preview_output(self, response: GeneratePageResponse, data: PageData) -> List[str]:
        """Lightweight validation for preview mode (fast, no repair)."""
        errors: List[str] = []

        all_text: List[str] = [response.title, response.meta_description]
        for block in response.blocks:
            if hasattr(block, "text") and block.text:
                all_text.append(block.text)
            if hasattr(block, "question") and block.question:
                all_text.append(block.question)
            if hasattr(block, "answer") and block.answer:
                all_text.append(block.answer)

        combined_text = " ".join(all_text)

        # Forbidden phrases
        low = combined_text.lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase.lower() in low:
                errors.append(f"Contains forbidden phrase: '{phrase}'")
        for phrase in self.FORBIDDEN_REGION_PHRASES:
            if phrase.lower() in low:
                errors.append(f"Contains forbidden region phrase: '{phrase}'")

        # Broader-area sentence required even in preview
        if not self._has_broader_area_sentence(combined_text, data.city):
            errors.append("Missing broader-area sentence ('nearby areas' or 'the greater {city} area')")

        return errors

    def _validate_output(self, response: GeneratePageResponse, data: PageData) -> List[str]:
        """Validate output and return list of validation errors."""
        errors: List[str] = []

        paragraph_blocks = [b for b in response.blocks if b.type == "paragraph"]
        faq_blocks = [b for b in response.blocks if b.type == "faq"]
        heading_blocks = [b for b in response.blocks if b.type == "heading"]

        # Word count
        total_words = 0
        for block in paragraph_blocks:
            if block.text:
                total_words += len(block.text.split())
        for block in faq_blocks:
            if block.question:
                total_words += len(block.question.split())
            if block.answer:
                total_words += len(block.answer.split())

        if total_words < 300:
            errors.append(f"Total word count {total_words} < 300")

        # Collect all text for forbidden checks
        all_text = [response.title, response.meta_description]
        for block in response.blocks:
            if hasattr(block, "text") and block.text:
                all_text.append(block.text)
            if hasattr(block, "question") and block.question:
                all_text.append(block.question)
            if hasattr(block, "answer") and block.answer:
                all_text.append(block.answer)

        combined_text = " ".join(all_text)
        combined_lower = combined_text.lower()

        # Forbidden meta language
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase.lower() in combined_lower:
                errors.append(f"Contains forbidden phrase: '{phrase}'")

        # Forbidden region / unsafe geography
        for phrase in self.FORBIDDEN_REGION_PHRASES:
            if phrase.lower() in combined_lower:
                errors.append(f"Contains forbidden region phrase: '{phrase}'")

        # Forbidden filler
        for phrase in self.FORBIDDEN_MARKETING_FILLER:
            if phrase.lower() in combined_lower:
                errors.append(f"Contains forbidden marketing filler: '{phrase}'")

        # Broader-area sentence requirement (exactly one is hard to validate; we require presence)
        if not self._has_broader_area_sentence(combined_text, data.city):
            errors.append("Missing broader-area sentence ('nearby areas' or 'the greater {city} area')")

        # Meta description includes service + city
        meta_desc = (response.meta_description or "").lower()
        if not (data.service.lower() in meta_desc and data.city.lower() in meta_desc):
            errors.append("Meta description missing service + city")

        # First paragraph includes service + city within 150 words
        if paragraph_blocks:
            first_para = paragraph_blocks[0].text or ""
            first_150_words = " ".join(first_para.split()[:150]).lower()
            if not (data.service.lower() in first_150_words and data.city.lower() in first_150_words):
                errors.append("First paragraph missing service + city in first 150 words")

        # Trade vocabulary density in paragraphs 1-3
        trade_vocab = self._get_trade_vocabulary_for_service(data.service)
        if trade_vocab:
            for idx, block in enumerate(paragraph_blocks[:3]):
                term_count = self._count_trade_terms_in_text(block.text or "", trade_vocab)
                if term_count < 2:
                    errors.append(
                        f"Paragraph {idx+1} has only {term_count} trade-specific terms (need at least 2)"
                    )

        # New: local differentiators in paragraphs 1-3 (at least 2 hits each)
        for idx, block in enumerate(paragraph_blocks[:3]):
            score = self._local_differentiator_score(block.text or "")
            if score < 2:
                errors.append(
                    f"Paragraph {idx+1} has weak local differentiators (score {score} < 2)"
                )

        # New: field insight markers in EACH paragraph (at least 2 markers)
        for idx, block in enumerate(paragraph_blocks):
            score = self._field_insight_score(block.text or "")
            if score < 2:
                errors.append(
                    f"Paragraph {idx+1} lacks field-insight signals (score {score} < 2)"
                )

        # New: observable outcomes in paragraph 4 (at least 2 outcome markers)
        if len(paragraph_blocks) >= 4:
            out_score = self._observable_outcome_score(paragraph_blocks[3].text or "")
            if out_score < 2:
                errors.append(
                    f"Paragraph 4 lacks observable outcome signals (score {out_score} < 2)"
                )

        # Heading count requirements
        block_counts = {}
        for block in response.blocks:
            block_counts[block.type] = block_counts.get(block.type, 0) + 1

        if block_counts.get("heading", 0) != 5:
            errors.append(f"Expected 5 headings (1 H1 + 4 H2s), got {block_counts.get('heading', 0)}")
        if block_counts.get("paragraph", 0) != 4:
            errors.append(f"Expected 4 paragraphs, got {block_counts.get('paragraph', 0)}")
        if block_counts.get("faq", 0) != 2:
            errors.append(f"Expected 2 FAQs, got {block_counts.get('faq', 0)}")
        if block_counts.get("nap", 0) != 1:
            errors.append(f"Expected 1 NAP, got {block_counts.get('nap', 0)}")
        if block_counts.get("cta", 0) != 1:
            errors.append(f"Expected 1 CTA, got {block_counts.get('cta', 0)}")

        # New: heading quality (H2s only)
        h2s = [hb for hb in heading_blocks if getattr(hb, "level", None) == 2]
        for idx, hb in enumerate(h2s, start=1):
            h = (hb.text or "").strip().lower()
            if not h:
                errors.append(f"H2 heading {idx} is empty")
                continue
            for frag in self.FORBIDDEN_GENERIC_HEADING_FRAGMENTS:
                if frag in h:
                    errors.append(f"H2 heading {idx} is too generic/templated (contains '{frag.strip()}')")

        # Block schema validation
        errors.extend(self._validate_block_schemas(response.blocks))

        return errors

    def _validate_block_schemas(self, blocks: List[PageBlock]) -> List[str]:
        """Validate that blocks have only allowed keys for their type (Pydantic handles structure)."""
        errors: List[str] = []

        for block in blocks:
            if not hasattr(block, "type"):
                errors.append("Block missing 'type' attribute")
                continue

            block_type = block.type
            if block_type == "heading" and not isinstance(block, HeadingBlock):
                errors.append("Block with type 'heading' is not HeadingBlock instance")
            elif block_type == "paragraph" and not isinstance(block, ParagraphBlock):
                errors.append("Block with type 'paragraph' is not ParagraphBlock instance")
            elif block_type == "faq" and not isinstance(block, FAQBlock):
                errors.append("Block with type 'faq' is not FAQBlock instance")
            elif block_type == "nap" and not isinstance(block, NAPBlock):
                errors.append("Block with type 'nap' is not NAPBlock instance")
            elif block_type == "cta" and not isinstance(block, CTABlock):
                errors.append("Block with type 'cta' is not CTABlock instance")

        return errors

    # -----------------------------
    # Repair pass
    # -----------------------------

    def _repair_output(self, bad_json: Dict[str, Any], validation_errors: List[str], data: PageData) -> Dict[str, Any]:
        """Attempt to repair failing content with targeted LLM call."""
        system_prompt = (
            "You are an editor fixing an existing JSON response. Keep the same structure and only change "
            "fields that fail the requirements. Improve specificity and local proof signals."
        )

        user_prompt = f"""We generated JSON but it failed these validations:
{', '.join(validation_errors)}

Here is the JSON to repair:
{json.dumps(bad_json, indent=2)}

CRITICAL:
- Service is {data.service}. Remove ALL content about other services.
- Keep the SAME JSON structure. Return JSON only.

HEADING FIXES:
- Rewrite any generic headings. Avoid starting headings with: "Understanding", "Reliable", "Quality", "Trusted", "Why Choose Us".
- Headings should include a concrete work term (for gutters: downspout, fascia, seam, hanger, pitch, overflow).

LOCAL PROOF + DIFFERENTIATORS (MANDATORY):
Sections 1–3 must EACH include at least 2 local differentiators from safe categories:
- Home style/build era (no neighborhoods): older homes, newer subdivisions, 80s–90s builds, slab-on-grade, pier-and-beam
- Weather mechanics (state-safe): {data.state}-safe weather tied to failures (expansion, pitch drift, seam separation, hanger loosening)
- Maintenance patterns: tree debris frequency, neglected cleanouts, DIY extensions
- Construction details: long runs, roofline complexity, downspout placement

FIELD-INSIGHT SIGNALS (MANDATORY):
Each paragraph must include at least 2 “field insight” moments (real patterns you see/hear).
Avoid templated starters like:
- "Homeowners typically notice..."
- "We often see this after the first major storm..."
- "Most issues we see start when..."
Instead vary phrasing:
- "What brings most calls is..."
- "The first sign usually shows up as..."
- "During a heavy downpour, you'll notice..."
- "A quick way to tell is..."

DECISION GUIDANCE (REQUIRED):
- When to act today vs monitor
- What escalates if ignored
- Section 3 must include the fork decision: repair vs sectional replacement (seam failure, sagging, fascia rot, pitch issues)

SECTION 4 (OBSERVABLE OUTCOMES ONLY):
Replace any promotional language with measurable outcomes customers can verify:
- no overflow at the end cap
- water discharges at the splash block
- no staining on fascia
- no pooling near the foundation

BROADER-AREA SENTENCE (MANDATORY):
Include exactly one sentence using ONLY:
- "nearby areas" OR "the greater {data.city} area"
No counties, regions, neighborhoods.

TRADE VOCABULARY:
If validation mentions trade terms, ensure paragraphs 1–3 each include at least 2 technical terms for {data.service}.

FORBIDDEN:
Remove any SEO/meta writing-process language.
Remove filler phrases (top-notch, premier, trusted experts, etc.).
Remove forbidden regional references (south florida, miami-dade, broward, salt air, coastal).

Ensure meta_description includes service + city.
Ensure first paragraph includes service + city within first 150 words.
Ensure CTA includes city + phone.

Return JSON only.
"""
        return self._call_openai_json(system_prompt, user_prompt)


# Global AI generator instance
ai_generator = AIContentGenerator()
