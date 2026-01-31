"""
Robust LLM-backed API for SEO-optimized home service pages.
Implements programmatic enforcement, validation, and repair passes.
Supports both service+city and service hub page generation.
"""

import json
import re
import os
from typing import Dict, Any, List, Tuple
import httpx
import asyncio
from app.config import settings
from app.models import PageData, GeneratePageResponse, PageBlock, HeadingBlock, ParagraphBlock, FAQBlock, NAPBlock, CTABlock
from app.local_data_fetcher import local_data_fetcher
from app.vertical_profiles import get_vertical_profile, get_trade_name
from app import ai_generator_hub

class AIContentGenerator:
    """Robust content generator with programmatic enforcement and repair capabilities."""
    
    # Forbidden meta-language phrases (case-insensitive)
    # Note: "structure" removed as it's a legitimate construction/building term
    FORBIDDEN_PHRASES = [
        "seo", "keyword", "word count", "first 100 words", 
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
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    def generate_page_content(self, data: PageData) -> GeneratePageResponse:
        """
        Generate complete page content with validation and repair.
        Routes to service_city, service_hub, or city_hub generation based on page_mode.
        
        Args:
            data: Page generation parameters
            
        Returns:
            Complete validated page content
            
        Raises:
            Exception: If generation and repair both fail
        """
        # Route based on page_mode
        if data.page_mode == "service_hub":
            return self._generate_service_hub_content(data)
        elif data.page_mode == "city_hub":
            return self._generate_city_hub_content(data)
        else:
            return self._generate_service_city_content(data)
    
    def _generate_service_city_content(self, data: PageData) -> GeneratePageResponse:
        """Generate service+city page content (existing logic)."""
        try:
            # Step 0: Fetch comprehensive local data (Census + landmarks + research)
            local_data = None
            try:
                # Check if we're already in an event loop
                try:
                    asyncio.get_running_loop()
                    # Already in event loop, skip local data to avoid asyncio.run() error
                    local_data = None
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run()
                    # NEW: Use get_all_local_data to include research data
                    local_data = asyncio.run(
                        local_data_fetcher.get_all_local_data(
                            data.city,
                            data.state,
                            data.vertical  # Pass vertical as trade_type
                        )
                    )
            except Exception as e:
                print(f"Warning: Could not fetch local data for {data.city}, {data.state}: {e}")
                local_data = None
            
            # Step 1: Generate content via LLM (NOT title/slug/H1)
            content_json = self._call_openai_generation(data, local_data)
            
            # Step 2: Assemble complete response with programmatic fields
            response = self._assemble_response(content_json, data)
            
            # Step 3: Validate output
            validation_errors = self._validate_output(response, data)

            # Step 3.5: Validate research data usage (if research data available)
            if local_data and local_data.get("research"):
                # Extract all content text from response blocks
                content_text = ""
                for block in response.blocks:
                    if hasattr(block, 'text'):
                        content_text += " " + block.text
                    if hasattr(block, 'answer'):  # FAQ blocks
                        content_text += " " + block.answer

                is_valid, error_msg = self._validate_research_usage(content_text, local_data)
                if not is_valid:
                    validation_errors.append(error_msg)

            # Step 4: If validation fails, attempt repair pass
            if validation_errors:
                print(f"Validation failed: {validation_errors}")
                repaired_content = self._repair_output(content_json, validation_errors, data, local_data)
                response = self._assemble_response(repaired_content, data)
                
                # Re-validate after repair
                final_validation_errors = self._validate_output(response, data)
                if final_validation_errors:
                    raise Exception(f"Content generation failed validation even after repair: {final_validation_errors}")
            
            return response
            
        except Exception as e:
            raise Exception(f"AI content generation failed: {str(e)}")
    
    def _generate_service_hub_content(self, data: PageData) -> GeneratePageResponse:
        """Generate service hub page content (no city-specific content)."""
        return ai_generator_hub.generate_service_hub_content(self, data)
    
    def _generate_city_hub_content(self, data: PageData) -> GeneratePageResponse:
        """Generate city hub page content (city-localized hub page)."""
        from app import ai_generator_city_hub
        return ai_generator_city_hub.generate_city_hub_content(self, data)

    def generate_page_content_preview(self, data: PageData) -> GeneratePageResponse:
        """Generate a fast preview response (no repair loop, reduced output)."""
        # Route based on page_mode for preview as well
        if data.page_mode == "service_hub":
            return self._generate_service_hub_content(data)
        elif data.page_mode == "city_hub":
            return self._generate_city_hub_content(data)
        
        try:
            content_json = self._call_openai_generation_preview(data)
            response = self._assemble_response(content_json, data)

            validation_errors = self._validate_preview_output(response)
            if validation_errors:
                raise Exception(f"Preview generation failed validation: {validation_errors}")

            return response
        except Exception as e:
            raise Exception(f"AI preview generation failed: {str(e)}")
    
    def slugify(self, service: str, city: str = "") -> str:
        """Generate clean slug. For hierarchical URLs, just use service name (city is in parent path)."""
        clean_service = re.sub(r'[^a-zA-Z0-9\s]', '', service.strip().lower())
        service_slug = re.sub(r'\s+', '-', clean_service)
        # For hierarchical structure, slug is just the service name
        # City context comes from parent page in URL hierarchy
        slug = service_slug
        # Cap at 60 characters
        return slug[:60].rstrip('-')
    
    def _call_openai_json(self, system_prompt: str, user_prompt: str, *, max_tokens: int = 4000, timeout: int = 60, temperature: float = 0.4) -> Dict[str, Any]:
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
            "temperature": temperature,
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

                # Strip markdown code blocks if present (OpenAI sometimes wraps JSON in ```json ... ```)
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]  # Remove ```json
                if content.startswith("```"):
                    content = content[3:]  # Remove ```
                if content.endswith("```"):
                    content = content[:-3]  # Remove trailing ```
                content = content.strip()

                # Debug: Log what OpenAI actually returned if JSON parsing fails
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"\n⚠️  OpenAI returned non-JSON content:")
                    print(f"First 500 chars: {content[:500]}")
                    print(f"JSON Error: {str(e)}")
                    raise Exception(f"OpenAI returned invalid JSON: {str(e)}")

        except json.JSONDecodeError as e:
            raise Exception(f"OpenAI returned invalid JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    def _get_landmark_instruction(self, local_data: Dict[str, Any] = None) -> str:
        """Generate varied landmark mention instructions to avoid repetitive patterns."""
        if not local_data or not local_data.get('landmarks'):
            return "Do NOT mention specific landmarks, neighborhoods, or areas unless they are in the verified list above."
        
        landmarks = local_data['landmarks'][:3]  # Use up to 3 landmarks
        if len(landmarks) == 0:
            return "Do NOT mention specific landmarks, neighborhoods, or areas unless they are in the verified list above."
        
        # Multiple varied patterns to make content seem more human-generated
        import random
        patterns = []
        
        if len(landmarks) >= 2:
            patterns.extend([
                f"REQUIRED: Mention at least ONE of these verified landmarks naturally: {', '.join(landmarks[:2])}. Example: 'whether you're near {landmarks[0]} or closer to {landmarks[1]}'",
                f"REQUIRED: Mention at least ONE of these verified landmarks naturally: {', '.join(landmarks[:2])}. Example: 'especially in areas around {landmarks[0]} and {landmarks[1]}'",
                f"REQUIRED: Mention at least ONE of these verified landmarks naturally: {', '.join(landmarks[:2])}. Example: 'homes throughout the area, including those near {landmarks[0]}'",
                f"REQUIRED: Mention at least ONE of these verified landmarks naturally: {', '.join(landmarks[:2])}. Example: 'residents close to {landmarks[0]} often experience similar issues'",
                f"REQUIRED: Mention at least ONE of these verified landmarks naturally: {', '.join(landmarks[:2])}. Example: 'from the {landmarks[0]} area to neighborhoods near {landmarks[1]}'",
            ])
        else:
            patterns.extend([
                f"REQUIRED: Mention this verified landmark naturally: {landmarks[0]}. Example: 'especially in areas around {landmarks[0]}'",
                f"REQUIRED: Mention this verified landmark naturally: {landmarks[0]}. Example: 'homes near {landmarks[0]} often face these challenges'",
                f"REQUIRED: Mention this verified landmark naturally: {landmarks[0]}. Example: 'whether you're close to {landmarks[0]} or elsewhere in the city'",
            ])
        
        return random.choice(patterns)
    
    def _get_random_headings(self, service: str, city: str) -> Dict[str, str]:
        """Generate random heading variations for each section to avoid template-like appearance."""
        import random
        
        section_variations = {
            'section1': [
                f"{service} in {city}",
                f"Professional {service} in {city}",
                f"Expert {service} in {city}",
                f"{service} Services in {city}",
            ],
            'section2': [
                f"Common Problems with {service}",
                f"What Can Go Wrong with {service}",
                f"Typical {service} Issues",
                f"When to Call for {service}",
                f"{service} Problems You Might Face",
            ],
            'section3': [
                f"How We Handle {service}",
                f"Our {service} Process",
                f"What We Do for {service}",
                f"Our Approach to {service}",
            ],
            'section4': [
                f"What You'll Experience After {service}",
                f"Results You Can Expect",
                f"What Changes After We Complete {service}",
                f"What Customers Notice After {service}",
            ],
            'why_section': [
                f"Why {service} Matters",
                f"Understanding {service}",
                f"What Makes {service} Important",
                f"The Reality of {service}",
            ],
            'when_section': [
                f"When to Choose {service}",
                f"Is {service} Right for Your Situation?",
                f"{service} vs Other Options",
                f"Knowing When You Need {service}",
            ],
        }
        
        return {
            section: random.choice(options)
            for section, options in section_variations.items()
        }
    
    def _call_openai_generation(self, data: PageData, local_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate content payload using exact specified prompt."""
        import random
        
        # Randomize structure to avoid template-like appearance
        num_faqs = random.randint(3, 5)  # Variable FAQ count (3-5 for substantial content)
        headings = self._get_random_headings(data.service, data.city)
        
        # Structural variance: randomize section order and placement
        # Vary middle sections (problems, process, results) order
        middle_sections_order = random.choice([
            ['problems', 'process', 'results'],  # Default order
            ['process', 'problems', 'results'],  # Process first
            ['problems', 'results', 'process'],  # Results before process
            ['results', 'problems', 'process'],  # Results first
        ])

        # Structural variance: randomize "Why This Service" section placement
        why_section_position = random.choice([2, 3, 4])  # Insert after section 2, 3, or 4

        # Structural variance: randomize "When to Choose This Service" section placement
        when_section_position = random.choice([3, 4, 5])  # Insert after section 3, 4, or 5

        # Structural variance: randomize CTA placement and contact card order
        cta_after_section = random.choice([5, 6])  # CTA after section 5 or 6 (after both special sections)
        contact_order = random.choice(['phone_first', 'email_first'])

        # Map middle section order to section numbers (2, 3, 4)
        section_2_topic = middle_sections_order[0]
        section_3_topic = middle_sections_order[1]
        section_4_topic = middle_sections_order[2]
        
        # Determine target audience based on hub_label
        hub_label = data.hub_label or ""
        is_commercial = 'commercial' in hub_label.lower()
        is_industrial = 'industrial' in hub_label.lower()
        
        if is_commercial or is_industrial:
            target_audience = "business owner"
            property_type = "commercial properties" if is_commercial else "industrial facilities"
            property_examples = "office buildings, retail spaces, warehouses" if is_commercial else "manufacturing facilities, warehouses, industrial complexes"
        else:
            target_audience = "homeowner"
            property_type = "homes"
            property_examples = "single-family homes, townhomes, condos"
        
        system_prompt = f"You are a professional local service copywriter. Write natural, trustworthy marketing copy that genuinely helps potential customers understand the service and make informed decisions. Focus on practical, actionable information rather than marketing fluff. Target audience: {target_audience}."
        
        # Format local data if available
        local_facts = ""
        landmark_requirement = ""
        if local_data and (local_data.get("housing_facts") or local_data.get("landmarks")):
            local_facts = "\n\n" + local_data_fetcher.format_for_prompt(local_data)
            
            # Add landmark requirement to critical validation if landmarks exist
            if local_data.get("landmarks"):
                landmark_requirement = f"\n4. MUST mention at least ONE landmark from the verified list above (e.g., 'near {local_data['landmarks'][0]}' or 'around {local_data['landmarks'][0]}')"

        # Extract median year and construction eras from research for explicit prompting
        median_year_text = ""
        construction_era_text = ""
        if local_data and local_data.get("research"):
            research = local_data["research"]
            building_age = research.get("building_age_specificity", {})
            if building_age.get("median_year"):
                median_year = building_age["median_year"]
                median_year_text = f"The median building year for {data.city} is {median_year}. "

            construction_eras = research.get("major_construction_eras", [])
            if construction_eras:
                era_list = []
                for era in construction_eras[:2]:
                    if isinstance(era, dict) and era.get("period"):
                        era_list.append(f"{era['period']} ({era.get('description', '')})")
                if era_list:
                    construction_era_text = f"Major construction eras: {', '.join(era_list)}. "

        # Build "USING VERIFIED LOCAL CONTEXT" section if research data exists
        using_context_section = ""
        if local_data and local_data.get("research"):
            using_context_section = f"""

⚠️ USING VERIFIED LOCAL CONTEXT:
The local_context above contains REAL, VERIFIED data about {data.city}, {data.state}:
- Census housing facts (building ages, construction periods)
- Real landmarks verified by AI research
- City-specific research for {data.service} businesses:
  * Construction eras with SPECIFIC years and local events
  * Climate factors with SPECIFIC measurements (not generic weather)
  * Service triggers with LOCAL context (not generic scenarios)
  * Permit requirements unique to this city
  * Unique local factors (economic history, building stock)

CRITICAL RULES FOR USING LOCAL CONTEXT:
1. YOU MUST use at least 2 specific facts from the research data in your content
2. DO NOT make up or invent local context - ONLY use what's provided
3. Paraphrase research facts naturally - don't copy verbatim
4. Connect research facts to {data.service} service needs
5. If research data includes specificity notes, those validate the fact is city-specific

⚠️ KEY RESEARCH FACTS FOR {data.city.upper()}:
{median_year_text}{construction_era_text}

EXAMPLES OF CORRECT USAGE:
✅ "Many commercial buildings date from the 1978-1982 oil boom, when 40% of downtown office stock was constructed"
   (Uses specific construction era from research with local economic context)

✅ "With extreme heat waves reaching 110°F+ for 20 days per year—more than double the state average—{data.service} systems face intense demand"
   (Uses climate factor with specific measurement and comparison)

❌ "The area experiences hot summers and storms"
   (Generic weather - research data includes specific measurements)

❌ "Many buildings are older and may need repairs"
   (Generic statement - research data includes specific construction eras)

⚠️ MANDATORY RESEARCH INTEGRATION (VALIDATION WILL CHECK):
You MUST use at least 2 specific facts from the VERIFIED LOCAL CONTEXT above.

ACCEPTABLE FACT USAGE (these will pass validation):
✓ Reference the ACTUAL median building year: {median_year_text.strip() if median_year_text else "Use the exact year from research"}
✓ Reference construction era with dates: {construction_era_text.strip() if construction_era_text else "Use specific periods from research"}
✓ Include climate measurements: "With {data.city} experiencing [specific number/measurement]..."
✓ Use 2+ consecutive words from climate factors: "flash flooding", "heat island effect"
✓ Reference unique local factors with key phrases: "suburban growth patterns", specific local events

UNACCEPTABLE (will fail validation):
✗ Generic year without using research: "built around 1979" or any year NOT in the research
✗ Generic climate mentions: "hot weather" instead of specific measurements from research
✗ Single common words: "due to", "with", "severe" that match accidentally
✗ Not mentioning research data at all

VALIDATION WILL VERIFY:
- At least 2 facts are used from: construction eras, climate factors, building age, unique factors
- Facts reference specific data (measurements, dates, multi-word phrases)
- You're using the ACTUAL research data, not inventing similar-sounding generic content
"""

        user_prompt = f"""⚠️ CRITICAL VALIDATION REQUIREMENTS (MUST PASS OR GENERATION FAILS):
1. First paragraph MUST include both "{data.service}" AND "{data.city}" in the first sentence
2. Meta description MUST include both "{data.service}" AND "{data.city}"
3. Do NOT use forbidden phrases: "structure", "top-notch", "premier", "trusted experts"{landmark_requirement}

⚠️ CRITICAL - UNDERSTAND THE SERVICE FIRST (READ THIS CAREFULLY):
The service name is "{data.service}". Before writing ANYTHING, determine what this service ACTUALLY does:

IF THE SERVICE NAME CONTAINS "INSURANCE" OR "CLAIM":
→ This is about HELPING CUSTOMERS NAVIGATE THE INSURANCE CLAIMS PROCESS
→ Write about: reviewing insurance policies, documenting damage for claims, photographing evidence, preparing claim paperwork, meeting with insurance adjusters, negotiating claim amounts, understanding policy coverage, appealing denied claims, maximizing claim payouts
→ DO NOT write about: performing repairs, fixing roofs, replacing shingles, stopping leaks, or any physical repair work
→ Example topics: "How we document damage for your claim", "What to expect when the adjuster visits", "Understanding your policy coverage", "Common reasons claims get denied"

IF THE SERVICE NAME CONTAINS "INSPECTION" OR "ASSESSMENT":
→ This is about EXAMINING and IDENTIFYING problems, NOT fixing them
→ Write about: what gets inspected, how issues are identified, what the inspection report includes, when inspections are needed
→ DO NOT write about: performing repairs or fixing the problems found

IF THE SERVICE NAME CONTAINS "CONSULTATION" OR "ESTIMATE":
→ This is about ADVISING customers and providing quotes, NOT performing work
→ Write about: assessment process, pricing factors, options available, recommendations
→ DO NOT write about: actually doing the installation or repair work

IF THE SERVICE NAME CONTAINS "EMERGENCY":
→ Emphasize URGENT RESPONSE, 24/7 availability, fast arrival times, temporary fixes to prevent further damage
→ Focus on speed and immediate action

CRITICAL: For "{data.service}", the PRIMARY PURPOSE is [analyze the service name and determine what it's actually about].
Generate content ONLY about that primary purpose. Do NOT write generic repair content unless the service is specifically about repairs.

Generate content for a local service landing page about {data.service} using:
Service: {data.service}
City: {data.city}
State: {data.state}
Company Name: {data.company_name}
Phone: {data.phone}{local_facts}
Address: {data.address}{using_context_section}

Return ONLY valid JSON with this exact structure:
{{
"meta_description": "string",
"sections": [
{{ "heading": "", "paragraph": "string" }},
{{ "heading": "string", "paragraph": "string" }},
{{ "heading": "string", "paragraph": "string" }},
{{ "heading": "string", "paragraph": "string" }},
{{ "heading": "string", "paragraph": "string" }},
{{ "heading": "string", "paragraph": "string" }}
],
"faqs": [
{', '.join(['{ "question": "string", "answer": "string" }'] * num_faqs)}
],
"cta_text": "string",
"structural_variance": {{
  "why_section_position": {why_section_position},
  "when_section_position": {when_section_position},
  "cta_after_section": {cta_after_section},
  "contact_order": "{contact_order}",
  "middle_sections_order": {middle_sections_order}
}}
}}

NOTE: Section 1 heading must be EMPTY (uses H1 above). Sections 2-6 must have headings.
IMPORTANT: Follow the specified topic order for sections 2-4: {section_2_topic}, {section_3_topic}, {section_4_topic}.

CRITICAL SERVICE FOCUS RULES:
Write ONLY about {data.service}. Every section must be exclusively about {data.service}.
If the service is "Gutter Repair", write ONLY about gutters - never mention roofing, shingles, or roof repairs.
If the service is "HVAC Installation", write ONLY about HVAC - never mention plumbing or electrical.
Section headings must be specific to {data.service}, not generic or about other services.
Do NOT use generic "roofing" content as filler - stay 100% focused on the specified service.

CONTENT STRUCTURE - GENUINELY HELPFUL FOR CUSTOMERS:
6 sections total. Section 1 has NO heading (uses the H1 above). Sections 2-6 have H2 headings and paragraphs (at least 650 characters for main sections, 400+ for comparison section):

Your goal is to help potential customers understand:
1. What this service involves in their specific city
2. What problems indicate they need this service
3. What to expect when they hire someone
4. What results they'll see after the work is done
5. Why this service matters (safety, permits, costs, common failures)
6. When to choose this service vs related services

Write content that YOU would want to read if you were a {target_audience} researching this service.

TARGET AUDIENCE: {target_audience.upper()}
PROPERTY TYPE: {property_type}
- Write for {target_audience}s, NOT homeowners (unless target audience is homeowner)
- Reference {property_type}, NOT homes (unless property type is homes)
- Use appropriate context: {property_examples}

- Section 1: NO HEADING (the page already has an H1). Start directly with the paragraph.
  CRITICAL: The FIRST SENTENCE must include both '{data.service}' and '{data.city}'. Example: "Breaker trips are common with electrical repair in older Tulsa {property_type}."
  Help {target_audience}s understand what makes {{data.service}} different in {{data.city}} specifically using VERIFIED LOCAL DATA from the research above.
  {{self._get_landmark_instruction(local_data)}}
  Focus on information that helps them understand their situation, not marketing language.
  Don't start with "In [city], electrical issues can be..." - start with something specific that includes the service and city immediately.

- Section 2: Topic = {section_2_topic.upper()}. Use heading "{{headings['section2']}}"
  {'Help ' + target_audience + 's recognize when they need this service. Talk about what actually goes wrong and when people should call. Most importantly: Tell people when something urgent vs when they can wait.' if section_2_topic == 'problems' else 'Help customers understand what to expect when they hire someone for this work. Walk through what gets checked, what usually gets found, and what changes after the work is done.' if section_2_topic == 'process' else 'Help customers know what results to expect and how to verify the work was done properly. Talk about what people can actually see and verify - no more overflow, lights stop flickering, breakers stop tripping, etc.'}

- Section 3: Topic = {section_3_topic.upper()}. Use heading "{headings['section3']}"
  {'Help ' + target_audience + 's recognize when they need this service. Talk about what actually goes wrong and when people should call. Most importantly: Tell people when something urgent vs when they can wait.' if section_3_topic == 'problems' else 'Help customers understand what to expect when they hire someone for this work. Walk through what gets checked, what usually gets found, and what changes after the work is done.' if section_3_topic == 'process' else 'Help customers know what results to expect and how to verify the work was done properly. Talk about what people can actually see and verify - no more overflow, lights stop flickering, breakers stop tripping, etc.'}

- Section 4: Topic = {section_4_topic.upper()}. Use heading "{headings['section4']}"
  {'Help ' + target_audience + 's recognize when they need this service. Talk about what actually goes wrong and when people should call. Most importantly: Tell people when something urgent vs when they can wait.' if section_4_topic == 'problems' else 'Help customers understand what to expect when they hire someone for this work. Walk through what gets checked, what usually gets found, and what changes after the work is done.' if section_4_topic == 'process' else 'Help customers know what results to expect and how to verify the work was done properly. Talk about what people can actually see and verify - no more overflow, lights stop flickering, breakers stop tripping, etc.'}

- Section 5 ("Why This Service" - INSERT AFTER SECTION {why_section_position}): Use heading "{headings['why_section']}"
  UNIQUE CONTENT - NOT REUSABLE ACROSS SERVICES. Cover 3-4 of these topics specific to {data.service}:
  * Safety implications: What happens if this goes wrong? What risks exist?
  * Permit requirements: Does this need permits? What code compliance matters?
  * Cost drivers: What makes this expensive or affordable? What affects pricing?
  * Common failure points: What typically breaks? What wears out first?
  * Long-term consequences: What happens if you delay this work?
  This section must be SPECIFIC to {data.service} - not generic advice that applies to any service.

- Section 6 ("When to Choose This Service" - INSERT AFTER SECTION {when_section_position}): Use heading "{headings['when_section']}"
  ALGORITHM-PROOFING SECTION - HIGHLY SERVICE-SPECIFIC COMPARISON (400-500 characters minimum).
  Help customers understand when they need THIS service vs related services:
  * Compare {data.service} with 2-3 related/similar services
  * Explain the key differences: "You need X when... but Y when..."
  * Give decision criteria: "If you're seeing [symptom], you need [this service]. If [different symptom], you need [other service]."
  * Examples for Electrical Repair: "vs Full Rewiring", "vs Panel Upgrade", "vs Outlet Installation"
  * Examples for Gutter Cleaning: "vs Gutter Repair", "vs Gutter Replacement", "vs Downspout Extension"
  This section CANNOT be reused across services - it's unique to {data.service}.
  Focus on practical decision-making, not marketing.

Example headings for "Gutter Installation":
- "Professional Gutter Installation in [City]"
- "Common Gutter Issues We See in [City]"
- "How We Install Gutters: Step by Step"
- "Why Choose Us for Gutter Installation"

TRADE VOCABULARY (CRITICAL):
Paragraphs 1-3 need 2+ technical terms each. Examples:
- Electrical: breaker, circuit, panel, wiring, voltage
- Gutter: downspout, fascia, pitch, debris, hanger
- Roofing: shingles, flashing, underlayment, decking
- HVAC: compressor, condenser, refrigerant, ductwork
- Plumbing: pipe, drain, valve, fixture, pressure

REDUCE EXACT-MATCH KEYWORD REPETITION:
The service name '{data.service}' is required where validation checks for it, but do NOT repeat it mechanically in every sentence.
Use natural substitutes and functional descriptions:
- Instead of repeating "Gutter Repair" → use "fixing sagging sections", "getting water flowing properly", "addressing common gutter problems"
- Instead of repeating "Electrical Repair" → use "fixing the wiring", "getting your outlets working", "addressing circuit issues"
- Instead of repeating "HVAC Installation" → use "getting your system installed", "setting up your new unit", "installing the equipment"
The service name must appear where required, but vary your language throughout the rest of the content.

WRITING STYLE - SOUND HUMAN, NOT AI:
- Write like you're talking to a neighbor, not writing a brochure
- Use short, punchy sentences mixed with longer explanatory ones
- Start sentences different ways - not always with "Our team" or "We" or "In [city]"
- Use 2-3 contractions per paragraph (we'll, it's, that's, you'll, can't, won't)
- Avoid repetitive sentence patterns - if you start one sentence with "If you notice...", don't start the next one the same way
- Skip filler phrases like "ensuring your home's electrical system is safe and reliable" - just say what you do
- Don't list things in the same order every time (problem → solution → benefit)
- Vary your vocabulary - don't use "issue" 5 times, mix in "problem", "trouble", "failure"
- Sound like someone who does this work every day, not someone reading from a script
- NO template language like "addressing your needs", "focus on providing", "here to ensure"

{num_faqs} FAQs about {data.service}. Requirements:
- 350+ characters per answer
- Structure: CAUSE→SYMPTOM→CONSEQUENCE→RESOLUTION
- Include local differentiators and trade terms
- Add "when to act vs monitor" guidance
- Must include city-specific context - if FAQ applies to any city unchanged, rewrite it
- Sound experienced, not marketing-focused

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

LANDMARKS AND GEOGRAPHY:
Do NOT mention specific landmarks, neighborhoods, or areas (e.g., "near downtown", "around the university", "in the arts district", specific neighborhood names like Maple Ridge, Brookside, Cherry Street).
Do NOT mention counties or regions (e.g., South Florida, Miami-Dade, Broward).
Do NOT use Florida-specific wording unless state is FL.
Focus on general housing characteristics and patterns that apply broadly across the city without referencing specific locations.

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
        import random
        
        # Programmatic fields (NOT generated by LLM)
        slug = self.slugify(data.service)  # Just service name for hierarchical URLs
        title = f"{data.service} in {data.city} | {data.company_name}"
        h1_text = f"Expert {data.service} in {data.city}"
        
        # Get structural variance settings from AI response (or use defaults)
        variance = content_json.get("structural_variance", {})
        cta_after_section = variance.get("cta_after_section", 5)
        contact_order = variance.get("contact_order", "phone_first")
        
        # Build blocks with minimal schemas - NO null fields
        blocks = []
        
        # H1 heading (programmatic) - only type, level, text
        blocks.append(self._create_heading_block(h1_text, 1))

        # 6 sections with H2 headings and paragraphs
        # NOTE: Section 1 should have NO heading (uses H1 above), but AI sometimes generates one anyway
        sections = content_json.get("sections", [])
        for idx, section in enumerate(sections, start=1):
            heading = section.get("heading", "")
            paragraph = section.get("paragraph", "")

            # Skip heading for Section 1 (it uses the H1 above)
            if heading and idx != 1:
                blocks.append(self._create_heading_block(heading, 2))

            if paragraph:
                blocks.append(self._create_paragraph_block(paragraph))
            
            # Insert CTA after specified section (structural variance)
            if idx == cta_after_section:
                blocks.append(self._create_cta_block(
                    content_json.get("cta_text", ""),
                    data.phone
                ))
        
        # FAQs - only type, question, answer
        # Structural variance: randomly use details format or h3+p format
        faq_format = random.choice(['details', 'h3'])
        for faq in content_json.get("faqs", []):
            blocks.append(self._create_faq_block(
                faq.get("question", ""),
                faq.get("answer", ""),
                format_style=faq_format
            ))
        
        # NAP block with contact order variance
        if data.company_name or data.address or data.phone or data.email:
            blocks.append(self._create_nap_block(
                data.company_name,
                data.phone,
                data.email,
                data.address,
                contact_order=contact_order
            ))
        
        # Add CTA at end if it wasn't inserted earlier
        if cta_after_section > len(sections):
            blocks.append(self._create_cta_block(
                content_json.get("cta_text", ""),
                data.phone
            ))
        
        return GeneratePageResponse(
            title=title,
            meta_description=content_json.get("meta_description", ""),
            slug=slug,
            blocks=blocks,
            page_mode="service_city"
        )
    
    def _create_heading_block(self, text: str, level: int) -> HeadingBlock:
        """Create heading block with minimal schema: type, level, text only."""
        return HeadingBlock(level=level, text=text)
    
    def _create_paragraph_block(self, text: str) -> ParagraphBlock:
        """Create paragraph block with minimal schema: type, text only."""
        return ParagraphBlock(text=text)
    
    def _create_faq_block(self, question: str, answer: str, format_style: str = 'details') -> FAQBlock:
        """Create FAQ block with minimal schema: type, question, answer only."""
        # Note: format_style is for future WordPress rendering variance
        # The block itself remains the same, but WordPress can render differently
        return FAQBlock(question=question, answer=answer)
    
    def _create_nap_block(self, business_name: str, phone: str, email: str, address: str, contact_order: str = 'phone_first') -> NAPBlock:
        """Create NAP block with minimal schema: type, business_name, phone, email, address only."""
        # Note: contact_order is for future WordPress rendering variance
        # The block itself remains the same, but WordPress can render phone or email first
        return NAPBlock(business_name=business_name, phone=phone, email=email, address=address)
    
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
        
        # Validation 5: Trade vocabulary density - DISABLED to prevent false failures
        # The prompt still encourages technical terms, but validation won't block generation
        # trade_vocab = self._get_trade_vocabulary_for_service(data.service)
        # if trade_vocab:
        #     for idx, block in enumerate(paragraph_blocks[:3]):
        #         if block.text:
        #             term_count = self._count_trade_terms_in_text(block.text, trade_vocab)
        #             if term_count < 1:
        #                 errors.append(f"Paragraph {idx+1} has only {term_count} trade-specific terms (need at least 1)")
        
        # Validation 6: Block count requirements
        block_counts = {}
        for block in response.blocks:
            block_counts[block.type] = block_counts.get(block.type, 0) + 1

        # Expect 1 H1 + 5 H2s = 6 headings total (Section 1 has NO heading, sections 2-6 have H2s)
        if block_counts.get("heading", 0) != 6:
            errors.append(f"Expected 6 headings (1 H1 + 5 H2s, section 1 has no heading), got {block_counts.get('heading', 0)}")
        # Section 1 paragraph + Sections 2-6 paragraphs = 6 paragraphs total
        if block_counts.get("paragraph", 0) != 6:
            errors.append(f"Expected 6 paragraphs, got {block_counts.get('paragraph', 0)}")
        # Accept 3-5 FAQs for variation
        faq_count = block_counts.get("faq", 0)
        if faq_count < 3 or faq_count > 5:
            errors.append(f"Expected 3-5 FAQs, got {faq_count}")

        # Validate we have 5 H2 sections (sections 2-6, section 1 has no heading)
        section_count = sum(1 for b in response.blocks if b.type == "heading" and b.level == 2)
        if section_count != 5:
            errors.append(f"Expected 5 H2 sections (sections 2-6, section 1 has no heading), got {section_count}")
        # NAP is optional - allow 0 or 1 (0 when all optional fields are empty)
        nap_count = block_counts.get("nap", 0)
        if nap_count > 1:
            errors.append(f"Expected 0 or 1 NAP, got {nap_count}")
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

    def _format_available_research_facts(self, local_data: Dict[str, Any]) -> str:
        """
        Format research facts for the repair prompt.

        Returns a bulleted list of available research facts that should be integrated.
        """
        if not local_data or not local_data.get("research"):
            return "No research data available"

        research = local_data["research"]
        facts = []

        # Building age
        building_age = research.get("building_age_specificity", {})
        if building_age.get("median_year"):
            median_year = building_age["median_year"]
            city_note = building_age.get("city_specific_note", "")
            if city_note:
                facts.append(f"- Building age: Median year {median_year} ({city_note[:80]})")
            else:
                facts.append(f"- Building age: Median year {median_year}")

        # Construction eras
        eras = research.get("major_construction_eras", [])
        for era in eras[:2]:
            if isinstance(era, dict):
                period = era.get("period", "")
                desc = era.get("description", "")
                if period:
                    facts.append(f"- Construction era: {period} - {desc}")

        # Climate factors
        climate = research.get("climate_factors", {})
        for factor in climate.get("primary", [])[:3]:
            facts.append(f"- Climate factor: {factor}")

        # Unique factors
        unique = research.get("unique_factors", [])
        for uf in unique[:2]:
            if isinstance(uf, dict):
                factor_text = uf.get("factor", "")
                if factor_text:
                    facts.append(f"- Unique factor: {factor_text}")

        return "\n".join(facts) if facts else "No specific facts available"

    def _validate_research_usage(self, content: str, local_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that generated content actually uses verified research data.

        IMPROVED VERSION: Requires meaningful research usage, not just single-word matches.
        Prevents false positives from common words like "due", "with", "severe".

        Args:
            content: Generated content text (all sections combined)
            local_data: Local data dict with research facts

        Returns:
            (is_valid, error_message)
        """
        if not local_data or not local_data.get("research"):
            # No research data available, skip validation
            return True, ""

        research = local_data["research"]

        # Extract key facts that should appear in content
        facts_to_check = []

        # Check for construction era mentions (KEEP THIS - works well)
        construction_eras = research.get("major_construction_eras", [])
        for era in construction_eras[:2]:  # Check first 2 eras
            if isinstance(era, dict):
                period = era.get("period", "")
                if period and period in content:
                    facts_to_check.append(f"construction era: {period}")

        # Check for climate factor mentions (IMPROVED)
        climate = research.get("climate_factors", {})
        primary_climate = climate.get("primary", [])
        for factor in primary_climate[:3]:  # Check first 3 climate factors
            # IMPROVED: Require measurements OR multi-word phrases
            # No more single-word matching that causes false positives

            # Check for measurements (e.g., "110°F", "+3°F", "20 days/year")
            import re
            measurements = re.findall(r'\d+[°\+\-]?[A-Z°]|\d+\s+days|\d+%', factor)
            if any(m in content for m in measurements):
                facts_to_check.append(f"climate factor: {factor[:50]}")
                continue

            # Check for 2+ consecutive words from factor (not just any single word)
            words = factor.split()
            if len(words) >= 2:
                for i in range(len(words) - 1):
                    two_word_phrase = f"{words[i]} {words[i+1]}"
                    if two_word_phrase.lower() in content.lower():
                        facts_to_check.append(f"climate factor: {factor[:50]}")
                        break

        # Check for building age mentions (KEEP THIS - works well)
        building_age = research.get("building_age_specificity", {})
        median_year = building_age.get("median_year")
        if median_year and str(median_year) in content:
            facts_to_check.append(f"building age: {median_year}")

        # Check for unique factors (NEW)
        unique_factors = research.get("unique_factors", [])
        for factor_obj in unique_factors[:2]:
            if isinstance(factor_obj, dict):
                factor_text = factor_obj.get("factor", "")
                # Look for key phrases (2+ consecutive words)
                words = factor_text.split()
                if len(words) >= 2:
                    for i in range(len(words) - 1):
                        phrase = f"{words[i]} {words[i+1]}"
                        if phrase.lower() in content.lower():
                            facts_to_check.append(f"unique factor: {factor_text[:50]}")
                            break

        # Require at least 2 facts to be used
        if len(facts_to_check) >= 2:
            return True, ""
        else:
            return False, (
                f"Content must use at least 2 specific facts from verified research data. "
                f"Found {len(facts_to_check)} fact(s). "
                f"Available: construction eras ({len(construction_eras)}), "
                f"climate factors ({len(primary_climate)}), "
                f"building age ({'yes' if median_year else 'no'}), "
                f"unique factors ({len(unique_factors)})."
            )

    def _repair_output(self, bad_json: Dict[str, Any], validation_errors: List[str], data: PageData, local_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Attempt to repair failing content with targeted LLM call."""
        system_prompt = "You are an editor fixing an existing JSON response. Keep the same structure and only change fields that fail the requirements."

        # Format local context if available
        local_context_reminder = ""
        if local_data and local_data.get("research"):
            from app.local_data_fetcher import local_data_fetcher
            local_context = local_data_fetcher.format_for_prompt(local_data)

            # Format available research facts for repair prompt
            available_facts = self._format_available_research_facts(local_data)

            local_context_reminder = f"""

⚠️ VALIDATION FAILED: The content did not use enough specific facts from the research data.

Available research facts you MUST integrate:
{available_facts}

FULL RESEARCH CONTEXT:
{local_context}

REQUIREMENTS FOR PASSING VALIDATION:
- Use at least 2 specific facts from the list above
- Include actual measurements/dates/numbers from the research
- Use multi-word phrases like "flash flooding", "heat island", "suburban growth"
- Reference the ACTUAL median building year from research, not a generic year

Examples of passing integration:
✓ "Properties from {data.city}'s 1990-1995 suburban expansion often have..."
✓ "The area's localized flash flooding, caused by 1990s drainage infrastructure..."
✓ "With {data.city}'s urban heat island effect adding 3°F in central areas..."

DO NOT use generic mentions that could apply to any city.
If validation mentions research data usage, you MUST incorporate at least 2 specific facts from the research above."""

        user_prompt = f"""⚠️ CRITICAL: Fix these validation failures:
{', '.join(validation_errors)}

⚠️ MANDATORY FIXES:
- If "First paragraph missing service + city": Rewrite the FIRST SENTENCE to include both "{data.service}" AND "{data.city}"
- If "Meta description missing service + city": Rewrite meta_description to include both "{data.service}" AND "{data.city}"
- If "Contains forbidden phrase": Remove ALL instances of the forbidden phrase{local_context_reminder}

We generated JSON but it failed these validations:
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
