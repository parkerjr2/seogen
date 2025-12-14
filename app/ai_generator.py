"""
AI content generation module for SEO-optimized roofing service pages.
Handles OpenAI API integration with strict validation and content hardening.
"""

import json
import re
from typing import Dict, Any, List
from openai import OpenAI
from app.config import settings
from app.models import PageData, GeneratePageResponse, PageBlock

class AIContentGenerator:
    """Handles AI-powered content generation with strict SEO validation and meta-language prevention."""
    
    # Forbidden meta-language phrases that must never appear in content
    FORBIDDEN_PHRASES = [
        "first 100 words", "this page", "this article", "we want to", "in this section",
        "seo", "keyword", "word count", "structure", "writing rules", "content requirements",
        "mandatory", "exactly one h1", "call to action", "business information"
    ]
    
    def __init__(self):
        """Initialize OpenAI client with API key from settings."""
        self.client = None
        self._api_key = settings.openai_api_key
    
    def _ensure_client(self):
        """Lazy initialization of OpenAI client when needed."""
        if self.client is None:
            if not self._api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.client = OpenAI(api_key=self._api_key)
    
    def generate_page_content(self, data: PageData) -> GeneratePageResponse:
        """
        Generate SEO-optimized page content for roofing services with strict validation.
        
        Args:
            data: Page generation parameters (service, city, company info)
            
        Returns:
            Complete page content with title, meta description, and blocks
            
        Raises:
            Exception: If OpenAI API fails or content validation fails
        """
        # Ensure OpenAI client is initialized
        self._ensure_client()
        
        # Create the exact specified prompt
        user_prompt = self._build_exact_prompt(data)
        
        try:
            # Call OpenAI API with the exact system and user prompts
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional local SEO copywriter writing high-quality landing pages for roofing companies. Your writing must sound natural, human, and trustworthy."
                    },
                    {
                        "role": "user", 
                        "content": user_prompt
                    }
                ],
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=3000
            )
            
            # Parse the JSON response
            content_json = json.loads(response.choices[0].message.content)
            
            # Validate content before processing
            self._validate_content_quality(content_json, data)
            
            # Generate programmatic slug (LLM must not generate this)
            slug = self._generate_slug(data.service, data.city)
            
            # Structure and clean the response
            page_response = self._structure_clean_response(content_json, slug, data)
            
            return page_response
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"AI content generation failed: {str(e)}")
    
    def _build_exact_prompt(self, data: PageData) -> str:
        """
        Build the exact prompt as specified in requirements - no modifications allowed.
        
        Args:
            data: Page generation parameters
            
        Returns:
            The exact user prompt as specified
        """
        return f"""Write a local service landing page for a roofing company using the following inputs:
Service: {data.service}
City: {data.city}
State: {data.state}
Company Name: {data.company_name}
Phone Number: {data.phone}
Business Address: {data.address}

CONTENT REQUIREMENTS (MANDATORY)
Write at least 300 words of original content.
The page title must include the service and city near the beginning.
Write exactly one H1 heading that includes the service and city.
The first paragraph must mention the service and city naturally.
Describe the service, benefits, and repair process clearly.
Include one FAQ relevant to the service.
Include a clear call to action referencing the city and phone number.
Include the business name, address, and phone number exactly as provided.

STRICT RULES (DO NOT VIOLATE)
Do NOT mention SEO, keywords, word counts, structure, or writing rules.
Do NOT say "this page", "this article", or "first 100 words".
Do NOT use HTML, markdown, bullet points, or formatting.
Do NOT repeat phrases excessively.
Do NOT invent reviews, awards, or certifications.

OUTPUT FORMAT
Return ONLY valid JSON using the structure below.
Do NOT include explanations, comments, or extra text.
{{
  "title": "string",
  "meta_description": "string",
  "blocks": [
    {{ "type": "heading", "level": 1, "text": "string" }},
    {{ "type": "paragraph", "text": "string" }},
    {{ "type": "paragraph", "text": "string" }},
    {{ "type": "paragraph", "text": "string" }},
    {{ "type": "faq", "question": "string", "answer": "string" }},
    {{ "type": "nap", "business_name": "string", "address": "string", "phone": "string" }},
    {{ "type": "cta", "text": "string", "phone": "string" }}
  ]
}}"""
    
    def _generate_slug(self, service: str, city: str) -> str:
        """
        Generate programmatic slug as {service}-{city} (lowercase, hyphenated, trimmed).
        LLM must NOT generate this - it's deterministic.
        
        Args:
            service: Service name
            city: City name
            
        Returns:
            Clean slug in format: service-city
        """
        # Clean and normalize inputs
        clean_service = re.sub(r'[^a-zA-Z0-9\s]', '', service.strip().lower())
        clean_city = re.sub(r'[^a-zA-Z0-9\s]', '', city.strip().lower())
        
        # Replace spaces with hyphens
        service_slug = re.sub(r'\s+', '-', clean_service)
        city_slug = re.sub(r'\s+', '-', clean_city)
        
        return f"{service_slug}-{city_slug}"
    
    def _validate_content_quality(self, content_json: Dict[str, Any], data: PageData) -> None:
        """
        Validate content quality and reject if validation fails.
        This prevents credit deduction for invalid content.
        
        Args:
            content_json: Raw JSON response from LLM
            data: Original page data for validation
            
        Raises:
            Exception: If content fails any validation check
        """
        # Check for forbidden meta-language phrases
        self._check_meta_language_leaks(content_json)
        
        # Validate required fields exist
        required_fields = ["title", "meta_description", "blocks"]
        for field in required_fields:
            if field not in content_json:
                raise Exception(f"Missing required field: {field}")
        
        # Validate blocks structure and requirements
        self._validate_required_blocks(content_json["blocks"], data)
        
        # Validate SEO placement rules
        self._validate_seo_placement(content_json, data)
        
        # Validate word count requirement
        self._validate_word_count(content_json["blocks"])
    
    def _check_meta_language_leaks(self, content_json: Dict[str, Any]) -> None:
        """
        Check for forbidden meta-language phrases in all text content.
        
        Args:
            content_json: JSON content to check
            
        Raises:
            Exception: If forbidden phrases are found
        """
        # Collect all text content for checking
        all_text = []
        all_text.append(content_json.get("title", ""))
        all_text.append(content_json.get("meta_description", ""))
        
        for block in content_json.get("blocks", []):
            if "text" in block and block["text"]:
                all_text.append(block["text"])
            if "question" in block and block["question"]:
                all_text.append(block["question"])
            if "answer" in block and block["answer"]:
                all_text.append(block["answer"])
        
        # Check for forbidden phrases (case insensitive)
        combined_text = " ".join(all_text).lower()
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase.lower() in combined_text:
                raise Exception(f"Content contains forbidden meta-language: '{phrase}'")
    
    def _validate_required_blocks(self, blocks: List[Dict], data: PageData) -> None:
        """
        Validate that all required block types are present with correct counts.
        
        Args:
            blocks: List of content blocks
            data: Page data for validation
            
        Raises:
            Exception: If required blocks are missing or counts are wrong
        """
        block_counts = {}
        for block in blocks:
            block_type = block.get("type", "")
            block_counts[block_type] = block_counts.get(block_type, 0) + 1
        
        # Validate exact requirements
        if block_counts.get("heading", 0) != 1:
            raise Exception("Must have exactly one H1 heading block")
        
        if block_counts.get("paragraph", 0) < 3:
            raise Exception("Must have at least 3 paragraph blocks")
        
        if block_counts.get("faq", 0) < 1:
            raise Exception("Must have at least 1 FAQ block")
        
        if block_counts.get("cta", 0) != 1:
            raise Exception("Must have exactly 1 CTA block")
        
        if block_counts.get("nap", 0) != 1:
            raise Exception("Must have exactly 1 NAP block")
        
        # Validate H1 contains service + city
        h1_block = next((b for b in blocks if b.get("type") == "heading"), None)
        if h1_block:
            h1_text = h1_block.get("text", "").lower()
            if not (data.service.lower() in h1_text and data.city.lower() in h1_text):
                raise Exception("H1 heading must include both service and city")
    
    def _validate_seo_placement(self, content_json: Dict[str, Any], data: PageData) -> None:
        """
        Validate SEO placement rules are followed.
        
        Args:
            content_json: JSON content to validate
            data: Page data for validation
            
        Raises:
            Exception: If SEO placement rules are violated
        """
        # Validate title includes service + city near beginning
        title = content_json.get("title", "").lower()
        if not (data.service.lower() in title and data.city.lower() in title):
            raise Exception("Title must include both service and city")
        
        # Validate meta description includes service + city
        meta_desc = content_json.get("meta_description", "").lower()
        if not (data.service.lower() in meta_desc and data.city.lower() in meta_desc):
            raise Exception("Meta description must include both service and city")
        
        # Validate first paragraph mentions service + city within first 100 words
        blocks = content_json.get("blocks", [])
        first_paragraph = next((b for b in blocks if b.get("type") == "paragraph"), None)
        if first_paragraph:
            paragraph_text = first_paragraph.get("text", "")
            words = paragraph_text.split()
            first_100_words = " ".join(words[:100]).lower()
            
            if not (data.service.lower() in first_100_words and data.city.lower() in first_100_words):
                raise Exception("First paragraph must mention service and city within first 100 words")
    
    def _validate_word_count(self, blocks: List[Dict]) -> None:
        """
        Validate total word count meets minimum requirement.
        
        Args:
            blocks: List of content blocks
            
        Raises:
            Exception: If word count is insufficient
        """
        total_words = 0
        
        for block in blocks:
            # Count words in text content blocks
            if block.get("type") in ["paragraph", "faq"]:
                text_content = block.get("text", "") + " " + block.get("answer", "")
                total_words += len(text_content.split())
        
        if total_words < 300:
            raise Exception(f"Content must be at least 300 words, got {total_words}")
    
    def _structure_clean_response(self, content_json: Dict[str, Any], slug: str, data: PageData) -> GeneratePageResponse:
        """
        Structure the validated content into clean response with minimal schema.
        
        Args:
            content_json: Validated JSON response from LLM
            slug: Programmatically generated slug
            data: Original page data
            
        Returns:
            Clean structured page response with no null fields
        """
        # Clean and structure blocks with minimal schema per type
        clean_blocks = []
        
        for block_data in content_json["blocks"]:
            block_type = block_data.get("type", "")
            
            # Create minimal schema based on block type - no null fields allowed
            if block_type == "heading":
                clean_block = PageBlock(
                    type="heading",
                    level=block_data.get("level", 1),
                    text=block_data.get("text", "")
                )
            elif block_type == "paragraph":
                clean_block = PageBlock(
                    type="paragraph",
                    text=block_data.get("text", "")
                )
            elif block_type == "faq":
                clean_block = PageBlock(
                    type="faq",
                    question=block_data.get("question", ""),
                    answer=block_data.get("answer", "")
                )
            elif block_type == "cta":
                clean_block = PageBlock(
                    type="cta",
                    text=block_data.get("text", ""),
                    phone=block_data.get("phone", "")
                )
            elif block_type == "nap":
                clean_block = PageBlock(
                    type="nap",
                    business_name=block_data.get("business_name", ""),
                    address=block_data.get("address", ""),
                    phone=block_data.get("phone", "")
                )
            else:
                # Skip unknown block types
                continue
            
            clean_blocks.append(clean_block)
        
        return GeneratePageResponse(
            title=content_json["title"],
            meta_description=content_json["meta_description"],
            slug=slug,  # Use programmatically generated slug, not LLM slug
            blocks=clean_blocks
        )

# Global AI generator instance
ai_generator = AIContentGenerator()
