"""
Robust LLM-backed API for SEO-optimized roofing service pages.
Implements programmatic enforcement, validation, and repair passes.
"""

import json
import re
import os
from typing import Dict, Any, List, Tuple
import httpx
from app.config import settings
from app.models import PageData, GeneratePageResponse, PageBlock, HeadingBlock, ParagraphBlock, FAQBlock, NAPBlock, CTABlock

class AIContentGenerator:
    """Robust content generator with programmatic enforcement and repair capabilities."""
    
    # Forbidden meta-language phrases (case-insensitive)
    FORBIDDEN_PHRASES = [
        "seo", "keyword", "word count", "structure", "first 100 words", 
        "this page", "this article", "in this section"
    ]
    
    # Forbidden marketing filler phrases (case-insensitive)
    FORBIDDEN_MARKETING_FILLER = [
        "top-notch", "premier", "high-quality solutions", "trusted experts",
        "we understand the importance of", "industry-leading", "best-in-class",
        "cutting-edge", "state-of-the-art", "world-class", "best in the area",
        "leading provider", "your trusted", "your go-to", "number one choice"
    ]
    
    # Trade vocabulary by service category (for validation)
    TRADE_VOCABULARY = {
        "electrical": ["breaker", "circuit", "panel", "outlet", "wiring", "voltage", "amp", "fuse", 
                      "junction", "conduit", "ground", "neutral", "hot wire", "gfci", "afci"],
        "gutter": ["downspout", "fascia", "pitch", "water flow", "debris", "soffit", "elbow", 
                  "splash block", "gutter guard", "seam", "hanger", "end cap", "overflow"],
        "roofing": ["shingles", "flashing", "underlayment", "vents", "decking", "ridge", "valley", 
                   "eave", "rake", "drip edge", "ice dam", "membrane", "felt paper"],
        "hvac": ["compressor", "condenser", "evaporator", "refrigerant", "ductwork", "thermostat", 
                "filter", "blower", "coil", "heat exchanger", "airflow", "tonnage", "seer"],
        "plumbing": ["pipe", "drain", "trap", "valve", "fixture", "water pressure", "sewer line", 
                    "shutoff", "coupling", "elbow", "tee", "gasket", "flange"],
        "window": ["sash", "frame", "pane", "glazing", "weatherstripping", "sill", "jamb", 
                  "mullion", "casing", "flashing", "argon", "low-e", "u-factor"],
        "door": ["threshold", "jamb", "weatherstripping", "deadbolt", "strike plate", "hinge", 
                "sweep", "lockset", "frame", "sill", "casing", "astragal"],
        "siding": ["lap", "j-channel", "soffit", "fascia", "trim", "flashing", "vapor barrier", 
                  "starter strip", "corner post", "furring", "sheathing"],
        "concrete": ["rebar", "aggregate", "slump", "cure", "expansion joint", "control joint", 
                    "trowel", "float", "pour", "mix", "psi", "footing"],
        "fence": ["post", "rail", "picket", "cap", "bracket", "gate", "latch", "hinge", 
                 "concrete footing", "stringer", "panel", "post hole"],
    }

    # Forbidden regional references and unsafe location language (case-insensitive)
    # These must never appear unless explicitly provided as an input (not supported in MVP).
    FORBIDDEN_REGION_PHRASES = [
        "south florida",
        "miami-dade",
        "broward",
        "salt air",
        "coastal",
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
        
        Args:
            data: Page generation parameters
            
        Returns:
            Complete validated page content
            
        Raises:
            Exception: If generation and repair both fail
        """
        try:
            # Step 1: Generate content via LLM (NOT title/slug/H1)
            content_json = self._call_openai_generation(data)
            
            # Step 2: Assemble complete response with programmatic fields
            response = self._assemble_response(content_json, data)
            
            # Step 3: Validate output
            validation_errors = self._validate_output(response, data)
            
            # Step 4: If validation fails, attempt repair pass
            if validation_errors:
                print(f"Validation failed: {validation_errors}")
                repaired_content = self._repair_output(content_json, validation_errors, data)
                response = self._assemble_response(repaired_content, data)
                
                # Re-validate after repair
                final_validation_errors = self._validate_output(response, data)
                if final_validation_errors:
                    raise Exception(f"Content generation failed validation even after repair: {final_validation_errors}")
            
            return response
            
        except Exception as e:
            raise Exception(f"AI content generation failed: {str(e)}")

    def generate_page_content_preview(self, data: PageData) -> GeneratePageResponse:
        """Generate a fast preview response (no repair loop, reduced output)."""
        try:
            content_json = self._call_openai_generation_preview(data)
            response = self._assemble_response(content_json, data)

            validation_errors = self._validate_preview_output(response)
            if validation_errors:
                raise Exception(f"Preview generation failed validation: {validation_errors}")

            return response
        except Exception as e:
            raise Exception(f"AI preview generation failed: {str(e)}")
    
    def slugify(self, service: str, city: str) -> str:
        """Generate clean slug as {service}-{city} (lowercase, hyphenated, max 60 chars)."""
        clean_service = re.sub(r'[^a-zA-Z0-9\s]', '', service.strip().lower())
        clean_city = re.sub(r'[^a-zA-Z0-9\s]', '', city.strip().lower())
        service_slug = re.sub(r'\s+', '-', clean_service)
        city_slug = re.sub(r'\s+', '-', clean_city)
        slug = f"{service_slug}-{city_slug}"
        # Cap at 60 characters
        return slug[:60].rstrip('-')
    
    def _call_openai_json(self, system_prompt: str, user_prompt: str, *, max_tokens: int = 4000, timeout: int = 60) -> Dict[str, Any]:
        """Call OpenAI API via httpx and return parsed JSON."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.4,
            "max_tokens": max_tokens
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout
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
        """Generate content payload using exact specified prompt."""
        system_prompt = "You are a professional local service copywriter. Write natural, trustworthy marketing copy. Avoid any writing-process language."
        
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
If the service is "Gutter Repair", write ONLY about gutters - never mention roofing, shingles, or roof repairs.
If the service is "HVAC Installation", write ONLY about HVAC - never mention plumbing or electrical.
Section headings must be specific to {data.service}, not generic or about other services.
Do NOT use generic "roofing" content as filler - stay 100% focused on the specified service.

CONTENT STRUCTURE (OPTIMIZED FOR MAP PACK VISIBILITY):
4 sections, each with an H2 heading and paragraph (at least 650 characters):

- Section 1: Heading about {data.service} in {data.city}. 
  Paragraph introduces {data.service} and must include exact service '{data.service}' and city '{data.city}' naturally near the beginning.
  MANDATORY FIELD INSIGHT: Include at least 2 sentences reflecting real-world service observations (but VARY the phrasing - see anti-symmetry rules below).
  CITY DIFFERENTIATION PACK (MANDATORY): Include at least 2 "local differentiators" from these safe categories:
  * Home style/build era WITHOUT naming neighborhoods: "older homes", "newer subdivisions", "homes built in the 80s-90s", "many slab-on-grade homes", "pier-and-beam foundations"
  * Climate-driven mechanics (state-safe weather only - TX: heat, hail, wind, heavy rain, storms): tie weather to physical failures like "expansion", "pitch drift", "overflow points", "seam separation", "hanger loosening"
  * Maintenance patterns: "tree debris frequency", "neglected cleanouts", "DIY extensions"
  * Construction details: "long runs", "roofline complexity", "downspout placement" (no neighborhood references)
  Do NOT start with "At {data.company_name}, we..." - start with the problem or customer observation.
  TONE: Experienced local explanation, not marketing reassurance.

- Section 2: LOCAL EXPERTISE + DECISION GUIDANCE - Heading about common {data.service} issues in {data.city}. 
  Paragraph must include:
  * CITY DIFFERENTIATION PACK (MANDATORY): At least 2 local differentiators from the safe categories above
  * DECISION GUIDANCE: Help users decide when to act (e.g., "If water is spilling behind the gutter instead of into the downspout, this needs immediate attention because...")
  * WARNING SIGNS: What escalates if ignored (e.g., "Once this starts happening, it can quickly lead to...")
  * INFORMATIONAL ASYMMETRY: Include one insight competitors often omit (common homeowner mistakes, assumptions that worsen problems, issues that look minor but aren't)
  MANDATORY: At least 2 field insight sentences (but VARY the phrasing - see anti-symmetry rules below).
  Do NOT start with brand-first language.
  RANDOMIZE NARRATIVE ORDER: Do NOT always follow "downspouts first, elbows second, then outcomes" - vary the order of topics across cities.

- Section 3: MICRO-NARRATIVE PROCESS + PRACTICAL GUIDANCE - Heading about your {data.service} process. 
  Paragraph must read like a walkthrough:
  * What's checked first and why
  * What problems are commonly found
  * FORK DECISION POINT (MANDATORY): Include 1-2 sentences explaining when a repair is enough vs when sectional replacement is needed, tied to observable conditions (seam failure, sagging, fascia rot, pitch issues)
  * What changes after the work
  * CITY DIFFERENTIATION PACK (MANDATORY): At least 2 local differentiators from the safe categories above
  MANDATORY: At least 2 field insight sentences (but VARY the phrasing - see anti-symmetry rules below).
  Use calm, confident, practical explanations.
  Avoid generic "thorough and professional" language.
  RANDOMIZE NARRATIVE ORDER: Vary the inspection sequence and problem emphasis across cities.

- Section 4: Heading about reliability and customer outcomes (NOT "why choose us"). 
  OBSERVABLE OUTCOMES ONLY (MANDATORY): Focus on measurable/observable results:
  * "no overflow at the end cap"
  * "water discharges at the splash block"
  * "no staining on fascia"
  * "no pooling near foundation"
  Replace emotional/social proof phrasing with concrete outcomes customers can verify.
  MANDATORY: At least 2 field insight sentences about outcomes/concerns you hear repeatedly (but VARY the phrasing - see anti-symmetry rules below).
  Start with customer scenarios or outcomes, not company claims.
  TONE: Observational and helpful, not promotional.
  This section can be more customer-focused and doesn't require as many technical terms.

Example headings for "Gutter Installation":
- "Professional Gutter Installation in [City]"
- "Common Gutter Issues We See in [City]"
- "How We Install Gutters: Step by Step"
- "Why Choose Us for Gutter Installation"

TRADE VOCABULARY REQUIREMENT (CRITICAL):
Paragraphs 1-3 MUST each include at least 2 service-specific technical terms. Paragraph 4 (why choose us) can focus more on customer satisfaction. Examples:
- Electrical: breaker, circuit, panel, outlet, wiring, voltage, amp, fuse, junction, conduit
- Gutter: downspout, fascia, pitch, water flow, debris, soffit, elbow, hanger, seam
- Roofing: shingles, flashing, underlayment, vents, decking, ridge, valley, eave
- HVAC: compressor, condenser, evaporator, refrigerant, ductwork, thermostat, filter, coil
- Plumbing: pipe, drain, trap, valve, fixture, water pressure, sewer line, shutoff
Use these terms naturally in context. Avoid vague marketing language.

REDUCE EXACT-MATCH KEYWORD REPETITION:
The service name '{data.service}' is required where validation checks for it, but do NOT repeat it mechanically in every sentence.
Use natural substitutes and functional descriptions:
- Instead of repeating "Gutter Repair" → use "fixing sagging sections", "getting water flowing properly", "addressing common gutter problems"
- Instead of repeating "Electrical Repair" → use "fixing the wiring", "getting your outlets working", "addressing circuit issues"
- Instead of repeating "HVAC Installation" → use "getting your system installed", "setting up your new unit", "installing the equipment"
The service name must appear where required, but vary your language throughout the rest of the content.

WRITING STYLE (MAP PACK OPTIMIZED):
TONE SHIFT: From "marketing reassurance" to "experienced local explanation"
- Use observational phrasing that demonstrates experience: "we often see", "most calls start with", "homeowners typically notice"
- Use practical explanations that teach, not just reassure
- Use calm, confident tone (not promotional or defensive)
- Mix short and long sentences for natural rhythm
- Vary sentence openers - avoid starting every sentence the same way
- Allow 1-2 mild contractions per paragraph (we'll, it's, that's, you'll)
- Write conversationally but professionally
- Sound like a knowledgeable local contractor explaining real problems, not a template
- Do NOT use slang or emojis
- Do NOT add testimonials or opinions not grounded in service work
- CRITICAL: Pages for the same service in different cities must NOT be interchangeable - vary examples, order, and emphasis

2 FAQs about {data.service}. OPTIMIZED FOR MAP PACK INTENT - EACH FAQ ANSWER MUST:
- Reference a REAL CUSTOMER SITUATION (e.g., "When you notice water pooling near your foundation...")
- Follow CAUSE→SYMPTOM→CONSEQUENCE→RESOLUTION structure:
  * Explain the cause (e.g., "...this usually means the downspouts are clogged or disconnected...")
  * Explain the symptom/what customers see (e.g., "...you'll notice water staining on the fascia...")
  * Explain the consequence if ignored (e.g., "...which can lead to foundation damage over time...")
  * Explain how the service resolves it (e.g., "...we clear the blockage and ensure proper drainage away from the house")
- Be at least 350 characters
- Demonstrate EXPERIENCE, not just correctness
- Include one LOCAL DIFFERENTIATOR from the City Differentiation Pack categories
- Include one TRADE TERM beyond the minimum paragraph requirements
- Include "WHEN TO ACT TODAY VS MONITOR" guidance (e.g., "If you're seeing active overflow during rain, address this immediately. If it's just minor staining, you can monitor it through the next storm.")
- CRITICAL: If an FAQ could apply to any city with zero changes, rewrite it with city-specific context
- Read like you're answering a real customer question you've heard many times
- TONE: Calm, confident, practical explanation - not marketing reassurance

ANTI-SYMMETRY RULES (CRITICAL - AVOID TEMPLATE PATTERNS):
Do NOT reuse these generic sentence templates across cities. Keep the idea but VARY the wording and sentence structure:
- ❌ "Homeowners typically notice..."
- ❌ "We often see this after the first major storm..."
- ❌ "Most issues we see start when..."
- ❌ "In many homes around {{city}}, this usually happens when..."
- ❌ "Once this starts happening, it can quickly lead to..."
- ❌ "We start by inspecting..."

Instead, vary your phrasing:
- ✅ "The first sign usually shows up as...", "What brings most calls is...", "Property owners around {{city}} run into this when..."
- ✅ "After a heavy downpour, you'll notice...", "Spring storms tend to expose...", "When hail hits, we see..."
- ✅ "Problems build up when...", "This develops over time as...", "The issue compounds if..."
- ✅ "Checking the attachment points first...", "Our inspection focuses on...", "The critical area to examine is..."

IMPORTANT: You must still include 2 field-insight sentences per section, but phrase them differently each time. Do NOT start every field-insight sentence with the same clause structure.

Include one sentence referencing the broader area using ONLY safe terms like 'nearby areas' or 'the greater {data.city} area'. Do NOT mention counties, regions, or specific neighborhoods.
Weather considerations must be generic and safe for the given state. Do NOT mention salt air.
If state is TX, only mention weather risks like heat, hail, wind, heavy rain, and storms.
Do NOT use Florida-specific wording unless state is FL.

Meta description must include the service and city naturally.
CTA text must include the city and the phone number.

STRICTLY FORBIDDEN PHRASES (will cause validation failure):
Do NOT use: "top-notch", "premier", "high-quality solutions", "trusted experts", "we understand the importance of", "industry-leading", "best-in-class", "cutting-edge", "state-of-the-art", "world-class", "best in the area", "leading provider", "your trusted", "your go-to", "number one choice"
Do NOT start paragraphs with: "At {{company_name}}, we...", "Choosing {{company_name}} means...", "{{company_name}} understands..."
Do NOT use HTML, markdown, or bullet points.
Do NOT mention SEO, keywords, word counts, structure, "this page", "this article", or similar meta language.
Do NOT mention any county names or specific neighborhoods.
Do NOT mention regions (e.g., South Florida, Midwest, Pacific Northwest), coastal/salt-air considerations, or unrelated geography.
Forbidden terms (case-insensitive): south florida, miami-dade, broward, salt air, coastal.
Do NOT invent reviews, awards, certifications, years in business, or claim specific local projects.
Do NOT write about services other than {data.service}.

Keep wording natural and not repetitive.
Return JSON only. No extra text."""
        
        return self._call_openai_json(system_prompt, user_prompt)

    def _call_openai_generation_preview(self, data: PageData) -> Dict[str, Any]:
        """Generate a fast preview content payload (reduced output, no repair loop)."""
        system_prompt = "You are a professional local service copywriter. Write natural, trustworthy marketing copy. Avoid any writing-process language."

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
Write ONLY about {data.service}. Every section must be exclusively about {data.service}.
If the service is "Gutter Repair", write ONLY about gutters - never mention roofing, shingles, or roof repairs.
Section headings must be specific to {data.service}, not generic or about other services.
Do NOT use generic "roofing" content as filler - stay 100% focused on the specified service.

PREVIEW REQUIREMENTS:
3 sections, each with an H2 heading and paragraph (at least 300 characters):
- Section 1: Heading about {data.service} in {data.city}. Paragraph must include exact service '{data.service}' and city '{data.city}' naturally near the beginning.
- Section 2: Heading about common {data.service} issues. Paragraph discusses problems specific to {data.service}.
- Section 3: Heading about your {data.service} quality or process. Paragraph focuses on expertise related to {data.service}.
Include one sentence referencing the broader area using ONLY safe terms like 'nearby areas' or 'the greater {data.city} area'.
Weather considerations must be generic and safe for the given state. Do NOT mention salt air.
If state is TX, only mention weather risks like heat, hail, wind, heavy rain, and storms.
Do NOT use Florida-specific wording unless state is FL.
1 FAQ about {data.service}. The answer must be at least 200 characters and specifically address {data.service}, not other services.
Meta description must include the service and city naturally.
CTA text must include the city and the phone number.
Do NOT use HTML, markdown, or bullet points.
Do NOT mention any county names or specific neighborhoods.
Do NOT mention regions (e.g., South Florida, Midwest, Pacific Northwest), coastal/salt-air considerations, or unrelated geography.
Forbidden terms (case-insensitive): south florida, miami-dade, broward, salt air, coastal.
Do NOT write about services other than {data.service}.
Return JSON only. No extra text."""

        return self._call_openai_json(system_prompt, user_prompt, max_tokens=1200, timeout=45)

    def _validate_preview_output(self, response: GeneratePageResponse) -> List[str]:
        """Lightweight validation for preview mode (fast, no repair)."""
        errors = []

        all_text = [response.title, response.meta_description]
        for block in response.blocks:
            if hasattr(block, 'text') and block.text:
                all_text.append(block.text)
            if hasattr(block, 'question') and block.question:
                all_text.append(block.question)
            if hasattr(block, 'answer') and block.answer:
                all_text.append(block.answer)

        combined_text = " ".join(all_text).lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase.lower() in combined_text:
                errors.append(f"Contains forbidden phrase: '{phrase}'")

        for phrase in self.FORBIDDEN_REGION_PHRASES:
            if phrase.lower() in combined_text:
                errors.append(f"Contains forbidden region phrase: '{phrase}'")

        return errors
    
    def _assemble_response(self, content_json: Dict[str, Any], data: PageData) -> GeneratePageResponse:
        """Assemble complete response with programmatic fields and minimal block schemas."""
        # Programmatic fields (NOT generated by LLM)
        slug = self.slugify(data.service, data.city)
        title = f"{data.service} in {data.city}, {data.state} | {data.company_name}"
        h1_text = f"Expert {data.service} in {data.city}, {data.state}"
        
        # Build blocks with minimal schemas - NO null fields
        blocks = []
        
        # H1 heading (programmatic) - only type, level, text
        blocks.append(self._create_heading_block(h1_text, 1))
        
        # 4 sections with H2 headings and paragraphs
        for section in content_json.get("sections", []):
            heading = section.get("heading", "")
            paragraph = section.get("paragraph", "")
            if heading:
                blocks.append(self._create_heading_block(heading, 2))
            if paragraph:
                blocks.append(self._create_paragraph_block(paragraph))
        
        # 2 FAQs - only type, question, answer
        for faq in content_json.get("faqs", []):
            blocks.append(self._create_faq_block(
                faq.get("question", ""),
                faq.get("answer", "")
            ))
        
        # NAP block - only type, business_name, address, phone
        blocks.append(self._create_nap_block(
            data.company_name,
            data.address,
            data.phone
        ))
        
        # CTA block - only type, text, phone
        blocks.append(self._create_cta_block(
            content_json.get("cta_text", ""),
            data.phone
        ))
        
        return GeneratePageResponse(
            title=title,
            meta_description=content_json.get("meta_description", ""),
            slug=slug,
            blocks=blocks
        )
    
    def _create_heading_block(self, text: str, level: int) -> HeadingBlock:
        """Create heading block with minimal schema: type, level, text only."""
        return HeadingBlock(level=level, text=text)
    
    def _create_paragraph_block(self, text: str) -> ParagraphBlock:
        """Create paragraph block with minimal schema: type, text only."""
        return ParagraphBlock(text=text)
    
    def _create_faq_block(self, question: str, answer: str) -> FAQBlock:
        """Create FAQ block with minimal schema: type, question, answer only."""
        return FAQBlock(question=question, answer=answer)
    
    def _create_nap_block(self, business_name: str, address: str, phone: str) -> NAPBlock:
        """Create NAP block with minimal schema: type, business_name, address, phone only."""
        return NAPBlock(business_name=business_name, address=address, phone=phone)
    
    def _create_cta_block(self, text: str, phone: str) -> CTABlock:
        """Create CTA block with minimal schema: type, text, phone only."""
        return CTABlock(text=text, phone=phone)
    
    def _get_trade_vocabulary_for_service(self, service: str) -> List[str]:
        """Get relevant trade vocabulary for a service by matching keywords."""
        service_lower = service.lower()
        
        # Direct category matches
        for category, vocab in self.TRADE_VOCABULARY.items():
            if category in service_lower:
                return vocab
        
        # Fallback: return a generic set if no match
        return []
    
    def _count_trade_terms_in_text(self, text: str, vocab: List[str]) -> int:
        """Count how many trade-specific terms appear in the text."""
        text_lower = text.lower()
        count = 0
        for term in vocab:
            if term.lower() in text_lower:
                count += 1
        return count
    
    def _validate_output(self, response: GeneratePageResponse, data: PageData) -> List[str]:
        """Validate output and return list of validation errors."""
        errors = []
        
        # Count total words across paragraphs and FAQ answers
        total_words = 0
        paragraph_blocks = [b for b in response.blocks if b.type == "paragraph"]
        faq_blocks = [b for b in response.blocks if b.type == "faq"]
        
        for block in paragraph_blocks:
            if block.text:
                total_words += len(block.text.split())
        
        for block in faq_blocks:
            if block.answer:
                total_words += len(block.answer.split())
            if block.question:
                total_words += len(block.question.split())
        
        # Validation 1: Word count >= 300
        if total_words < 300:
            errors.append(f"Total word count {total_words} < 300")
        
        # Validation 2: Check for forbidden meta-language
        all_text = [response.title, response.meta_description]
        for block in response.blocks:
            if hasattr(block, 'text') and block.text:
                all_text.append(block.text)
            if hasattr(block, 'question') and block.question:
                all_text.append(block.question)
            if hasattr(block, 'answer') and block.answer:
                all_text.append(block.answer)
        
        combined_text = " ".join(all_text).lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase.lower() in combined_text:
                errors.append(f"Contains forbidden phrase: '{phrase}'")

        # Validation 2b: Forbid incorrect regional references / unsafe geography
        for phrase in self.FORBIDDEN_REGION_PHRASES:
            if phrase.lower() in combined_text:
                errors.append(f"Contains forbidden region phrase: '{phrase}'")
        
        # Validation 2c: Check for forbidden marketing filler phrases
        for phrase in self.FORBIDDEN_MARKETING_FILLER:
            if phrase.lower() in combined_text:
                errors.append(f"Contains forbidden marketing filler: '{phrase}'")
        
        # Validation 3: First paragraph includes service + city within 150 words
        if paragraph_blocks:
            first_para = paragraph_blocks[0].text or ""
            first_150_words = " ".join(first_para.split()[:150]).lower()
            if not (data.service.lower() in first_150_words and data.city.lower() in first_150_words):
                errors.append("First paragraph missing service + city in first 150 words")
        
        # Validation 4: Meta description includes service + city
        meta_desc = response.meta_description.lower()
        if not (data.service.lower() in meta_desc and data.city.lower() in meta_desc):
            errors.append("Meta description missing service + city")
        
        # Validation 5: Trade vocabulary density (paragraphs 1-3 must have at least 2 trade terms)
        trade_vocab = self._get_trade_vocabulary_for_service(data.service)
        if trade_vocab:
            for idx, block in enumerate(paragraph_blocks[:3]):
                if block.text:
                    term_count = self._count_trade_terms_in_text(block.text, trade_vocab)
                    if term_count < 2:
                        errors.append(f"Paragraph {idx+1} has only {term_count} trade-specific terms (need at least 2)")
        
        # Validation 6: Block count requirements
        block_counts = {}
        for block in response.blocks:
            block_counts[block.type] = block_counts.get(block.type, 0) + 1
        
        # Expect 1 H1 + 4 H2s = 5 headings total
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
        
        # Validation 7: Block schema validation
        schema_errors = self._validate_block_schemas(response.blocks)
        errors.extend(schema_errors)
        
        return errors
    
    def _validate_block_schemas(self, blocks: List[PageBlock]) -> List[str]:
        """Validate that blocks have only allowed keys for their type."""
        errors = []
        
        # With specific block types, schema validation is handled by Pydantic
        # This method now just validates that we have the right block instances
        for block in blocks:
            if not hasattr(block, 'type'):
                errors.append("Block missing 'type' attribute")
                continue
                
            block_type = block.type
            
            # Validate block type matches expected class
            if block_type == "heading" and not isinstance(block, HeadingBlock):
                errors.append(f"Block with type 'heading' is not HeadingBlock instance")
            elif block_type == "paragraph" and not isinstance(block, ParagraphBlock):
                errors.append(f"Block with type 'paragraph' is not ParagraphBlock instance")
            elif block_type == "faq" and not isinstance(block, FAQBlock):
                errors.append(f"Block with type 'faq' is not FAQBlock instance")
            elif block_type == "nap" and not isinstance(block, NAPBlock):
                errors.append(f"Block with type 'nap' is not NAPBlock instance")
            elif block_type == "cta" and not isinstance(block, CTABlock):
                errors.append(f"Block with type 'cta' is not CTABlock instance")
        
        return errors
    
    def _repair_output(self, bad_json: Dict[str, Any], validation_errors: List[str], data: PageData) -> Dict[str, Any]:
        """Attempt to repair failing content with targeted LLM call."""
        system_prompt = "You are an editor fixing an existing JSON response. Keep the same structure and only change fields that fail the requirements."
        
        user_prompt = f"""We generated JSON but it failed these validations:
{', '.join(validation_errors)}

Here is the JSON to repair:
{json.dumps(bad_json, indent=2)}

CRITICAL: The service is {data.service}. Remove ALL content about other services.
If validation mentions "wrong service term", completely rewrite those paragraphs to focus ONLY on {data.service}.
Do NOT mention roofing, roof repair, shingles, or any other service unless {data.service} explicitly contains those words.

MAP PACK OPTIMIZATION - FIELD INSIGHT REQUIREMENT (MANDATORY):
Each paragraph must include at least 2 sentences reflecting real-world service observations.
ANTI-SYMMETRY: Do NOT use these template patterns:
- ❌ "Homeowners typically notice..."
- ❌ "We often see this after the first major storm..."
- ❌ "Most issues we see start when..."
- ❌ "In many homes around {data.city}, this usually happens when..."
Instead, vary your phrasing: "The first sign usually shows up as...", "What brings most calls is...", "After a heavy downpour, you'll notice...", "Problems build up when..."

CITY DIFFERENTIATION PACK (MANDATORY):
Sections 1-3 must EACH include at least 2 "local differentiators" from these safe categories:
- Home style/build era WITHOUT naming neighborhoods: "older homes", "newer subdivisions", "homes built in the 80s-90s", "many slab-on-grade homes", "pier-and-beam foundations"
- Climate-driven mechanics (state-safe weather only - TX: heat, hail, wind, heavy rain, storms): tie weather to physical failures like "expansion", "pitch drift", "overflow points", "seam separation", "hanger loosening"
- Maintenance patterns: "tree debris frequency", "neglected cleanouts", "DIY extensions"
- Construction details: "long runs", "roofline complexity", "downspout placement" (no neighborhood references)

RANDOMIZE NARRATIVE ORDER:
Do NOT always follow "downspouts first, elbows second, then outcomes" - vary the order of topics across cities.
Vary the inspection sequence and problem emphasis.

FORK DECISION POINT (Section 3):
Include 1-2 sentences explaining when a repair is enough vs when sectional replacement is needed, tied to observable conditions (seam failure, sagging, fascia rot, pitch issues).

OBSERVABLE OUTCOMES (Section 4):
Focus on measurable/observable results: "no overflow at the end cap", "water discharges at the splash block", "no staining on fascia", "no pooling near foundation"
Replace emotional/social proof phrasing with concrete outcomes customers can verify.

DECISION GUIDANCE (REQUIRED):
Include content that helps users decide:
- When to act immediately vs when to monitor
- What escalates if ignored
- When a repair is enough vs when replacement is needed

INFORMATIONAL ASYMMETRY (REQUIRED):
Include at least one insight competitors often omit:
- Common homeowner mistakes
- Assumptions that make problems worse
- Issues that look minor but aren't
Avoid "we're dedicated / trusted / professional" filler. Teach, don't just reassure.

REDUCE BRAND-FIRST OPENERS:
Do NOT start paragraphs with "At {data.company_name}, we..." or "Choosing {data.company_name} means..."
Start with the problem, customer observation, or scenario instead.

REDUCE KEYWORD REPETITION:
Do NOT repeat '{data.service}' mechanically in every sentence.
Use natural substitutes and functional descriptions throughout.

TRADE VOCABULARY REQUIREMENT:
If validation mentions "trade-specific terms", rewrite that paragraph to include at least 2 technical terms for {data.service}.
Examples by service:
- Electrical: breaker, circuit, panel, outlet, wiring, voltage, amp, fuse, junction, conduit
- Gutter: downspout, fascia, pitch, water flow, debris, soffit, elbow, hanger, seam
- Roofing: shingles, flashing, underlayment, vents, decking, ridge, valley, eave
- HVAC: compressor, condenser, evaporator, refrigerant, ductwork, thermostat, filter, coil
- Plumbing: pipe, drain, trap, valve, fixture, water pressure, sewer line, shutoff
Use these terms naturally in context. Avoid vague marketing language.

FAQ MAP PACK OPTIMIZATION:
Each FAQ answer must:
- Reference a real customer situation
- Follow CAUSE→SYMPTOM→CONSEQUENCE→RESOLUTION structure
- Demonstrate experience, not just correctness
- Include one LOCAL DIFFERENTIATOR from the City Differentiation Pack categories
- Include one TRADE TERM beyond the minimum paragraph requirements
- Include "WHEN TO ACT TODAY VS MONITOR" guidance
- If it could apply to any city with zero changes, add city-specific context

TONE SHIFT (CRITICAL):
From "marketing reassurance" to "experienced local explanation"
- Use observational phrasing: "we often see", "most calls start with", "homeowners typically notice"
- Use practical explanations that teach
- Use calm, confident tone (not promotional)
- Mix short and long sentences for natural rhythm
- Vary sentence openers
- Allow 1-2 mild contractions per paragraph
- Sound like a knowledgeable local contractor explaining real problems

Rules:
Return ONLY valid JSON in the same structure.
Fix only the failing fields.
Remove any forbidden meta-language terms.
Remove any forbidden marketing filler phrases: "top-notch", "premier", "high-quality solutions", "trusted experts", "we understand the importance of", "industry-leading", "best-in-class", "cutting-edge", "state-of-the-art", "world-class", "best in the area", "leading provider", "your trusted", "your go-to", "number one choice"
Remove any forbidden regional references and unsafe geography (south florida, miami-dade, broward, salt air, coastal).
Do NOT mention specific regions (e.g., South Florida, Midwest, Pacific Northwest).
Do NOT mention salt air.
If state is TX, keep weather references limited to heat, hail, wind, heavy rain, and storms.
Ensure paragraphs meet minimum character lengths and total content exceeds 300 words.
Ensure paragraphs 1-3 each include at least 2 trade-specific technical terms.
Ensure meta_description includes service and city.
Ensure first paragraph includes service and city within its first 150 words.
Ensure CTA includes city and phone number.
Return JSON only."""
        
        return self._call_openai_json(system_prompt, user_prompt)
    
# Global AI generator instance
ai_generator = AIContentGenerator()
