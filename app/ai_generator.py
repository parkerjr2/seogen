"""
AI content generation module for SEO-optimized roofing service pages.
Handles OpenAI API integration and content validation.
"""

import json
import re
from typing import Dict, Any
from openai import OpenAI
from app.config import settings
from app.models import PageData, GeneratePageResponse, PageBlock

class AIContentGenerator:
    """Handles AI-powered content generation with SEO optimization."""
    
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
        Generate SEO-optimized page content for roofing services.
        
        Args:
            data: Page generation parameters (service, city, company info)
            
        Returns:
            Complete page content with title, meta description, and blocks
            
        Raises:
            Exception: If OpenAI API fails or content validation fails
        """
        # Ensure OpenAI client is initialized
        self._ensure_client()
        
        # Create deterministic prompt that enforces SEO rules
        prompt = self._build_seo_prompt(data)
        
        try:
            # Call OpenAI API with structured output
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SEO content writer specializing in local roofing services. You must follow all SEO requirements exactly and return ONLY valid JSON with no additional text or formatting."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=3000
            )
            
            # Parse and validate the response
            content_json = json.loads(response.choices[0].message.content)
            page_response = self._validate_and_structure_content(content_json, data)
            
            return page_response
            
        except Exception as e:
            raise Exception(f"AI content generation failed: {str(e)}")
    
    def _build_seo_prompt(self, data: PageData) -> str:
        """
        Build deterministic prompt that enforces all SEO requirements.
        
        Args:
            data: Page generation parameters
            
        Returns:
            Structured prompt with SEO rules and requirements
        """
        return f"""
Generate SEO-optimized content for a roofing service page. Return ONLY valid JSON.

BUSINESS INFO:
- Service: {data.service}
- City: {data.city}
- State: {data.state}
- Company: {data.company_name}
- Phone: {data.phone}
- Address: {data.address}

MANDATORY SEO RULES:
1. Page title MUST include "{data.service}" and "{data.city}" near the beginning
2. Meta description MUST include "{data.service}" and "{data.city}" naturally
3. URL slug MUST be clean and keyword-focused (lowercase, hyphens only)
4. Exactly ONE H1 heading that includes "{data.service}" and "{data.city}"
5. First paragraph MUST mention "{data.service}" and "{data.city}" within first 100 words
6. Use natural keyword variations (e.g., "{data.city} roofing", "roofing contractors in {data.city}")
7. Content MUST be 100% unique - no templated phrases
8. Total content MUST be at least 300 words across all blocks
9. Include at least ONE FAQ about the service in {data.city}
10. Include NAP (business name, address, phone) as structured content
11. Include at least ONE CTA referencing {data.city} with phone number

REQUIRED JSON STRUCTURE:
{{
  "title": "Page title with service + city",
  "meta_description": "Meta description with service + city (150-160 chars)",
  "slug": "service-city-slug",
  "blocks": [
    {{"type": "heading", "level": 1, "text": "H1 with service + city"}},
    {{"type": "paragraph", "text": "Opening paragraph mentioning service + city early. Must be 100-150 words with detailed introduction to the service and company."}},
    {{"type": "paragraph", "text": "Service details and benefits paragraph. Must be 100-150 words explaining what makes your service unique, materials used, and quality guarantees."}},
    {{"type": "paragraph", "text": "Process explanation and why choose us. Must be 80-120 words detailing the step-by-step repair process and local expertise."}},
    {{"type": "paragraph", "text": "Additional service information covering emergency services, warranties, and local knowledge. Must be 60-100 words."}},
    {{"type": "faq", "question": "FAQ question about service costs, timeline, or process in city", "answer": "Comprehensive detailed answer that provides real value to customers. Must be 80-120 words with specific information."}},
    {{"type": "nap", "business_name": "{data.company_name}", "address": "{data.address}", "phone": "{data.phone}"}},
    {{"type": "cta", "text": "CTA text mentioning city", "phone": "{data.phone}"}}
  ]
}}

CONTENT RULES:
- Write for humans first, search engines second
- NO keyword stuffing
- NO HTML, markdown, or inline styles
- NO fake reviews or testimonials
- Reference {data.city} and surrounding area naturally
- Explain the service, benefits, and repair process clearly
- Make content engaging and informative
- CRITICAL: MINIMUM 400 WORDS TOTAL across all paragraph and FAQ answer blocks
- Each paragraph must be substantial and informative, not brief summaries
- Include detailed explanations of materials, processes, and local expertise
- FAQ answer must be comprehensive and valuable to customers
- Write in a professional but approachable tone
- Use specific details about roofing techniques and local considerations

CRITICAL WORD COUNT REQUIREMENT: 
- Paragraph 1: EXACTLY 130-160 words (detailed introduction)
- Paragraph 2: EXACTLY 130-160 words (comprehensive service details)
- Paragraph 3: EXACTLY 110-130 words (process and expertise)
- Paragraph 4: EXACTLY 90-110 words (additional services/warranties)
- FAQ Answer: EXACTLY 110-130 words (comprehensive answer)
- TOTAL MUST BE 570-690 words minimum

Do NOT generate short paragraphs. Each paragraph must be detailed, comprehensive, and meet the exact word count specified above.

Generate the JSON now:
"""
    
    def _validate_and_structure_content(self, content_json: Dict[str, Any], data: PageData) -> GeneratePageResponse:
        """
        Validate AI-generated content meets SEO requirements and structure it properly.
        
        Args:
            content_json: Raw JSON response from OpenAI
            data: Original page data for validation
            
        Returns:
            Validated and structured page response
            
        Raises:
            Exception: If content fails validation
        """
        # Validate required fields exist
        required_fields = ["title", "meta_description", "slug", "blocks"]
        for field in required_fields:
            if field not in content_json:
                raise Exception(f"Missing required field: {field}")
        
        # Validate title includes service + city
        title = content_json["title"]
        if not (data.service.lower() in title.lower() and data.city.lower() in title.lower()):
            raise Exception("Title must include both service and city")
        
        # Validate meta description includes service + city
        meta_desc = content_json["meta_description"]
        if not (data.service.lower() in meta_desc.lower() and data.city.lower() in meta_desc.lower()):
            raise Exception("Meta description must include both service and city")
        
        # Validate slug format (lowercase, hyphens only)
        slug = content_json["slug"]
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise Exception("Slug must be lowercase with hyphens only")
        
        # Validate blocks structure and content
        blocks = content_json["blocks"]
        self._validate_blocks(blocks, data)
        
        # Convert to Pydantic models
        page_blocks = []
        for block_data in blocks:
            page_blocks.append(PageBlock(**block_data))
        
        return GeneratePageResponse(
            title=title,
            meta_description=meta_desc,
            slug=slug,
            blocks=page_blocks
        )
    
    def _validate_blocks(self, blocks: list, data: PageData) -> None:
        """
        Validate that blocks meet SEO requirements.
        
        Args:
            blocks: List of content blocks
            data: Page data for validation
            
        Raises:
            Exception: If blocks fail validation
        """
        h1_count = 0
        has_faq = False
        has_nap = False
        has_cta = False
        total_words = 0
        first_paragraph_found = False
        
        for block in blocks:
            block_type = block.get("type", "")
            
            # Count H1 headings
            if block_type == "heading" and block.get("level") == 1:
                h1_count += 1
                h1_text = block.get("text", "")
                if not (data.service.lower() in h1_text.lower() and data.city.lower() in h1_text.lower()):
                    raise Exception("H1 must include both service and city")
            
            # Check first paragraph for service + city mention
            elif block_type == "paragraph" and not first_paragraph_found:
                first_paragraph_found = True
                paragraph_text = block.get("text", "")
                words = paragraph_text.split()
                if len(words) > 100:
                    first_100_words = " ".join(words[:100])
                else:
                    first_100_words = paragraph_text
                
                if not (data.service.lower() in first_100_words.lower() and data.city.lower() in first_100_words.lower()):
                    raise Exception("First paragraph must mention service and city within first 100 words")
            
            # Count words in text blocks
            if block_type in ["paragraph", "faq"]:
                text_content = block.get("text", "") + block.get("answer", "")
                total_words += len(text_content.split())
            
            # Check for required block types
            if block_type == "faq":
                has_faq = True
            elif block_type == "nap":
                has_nap = True
            elif block_type == "cta":
                has_cta = True
        
        # Validate requirements
        if h1_count != 1:
            raise Exception("Must have exactly one H1 heading")
        if not has_faq:
            raise Exception("Must include at least one FAQ block")
        if not has_nap:
            raise Exception("Must include NAP (business info) block")
        if not has_cta:
            raise Exception("Must include at least one CTA block")
        if total_words < 300:
            raise Exception(f"Content must be at least 300 words, got {total_words}")

# Global AI generator instance
ai_generator = AIContentGenerator()
