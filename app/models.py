"""
Pydantic models for request and response validation.
Defines the data structures used by the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Union

class PageData(BaseModel):
    """Data model for page generation parameters."""
    service: str = Field(..., description="Service type (e.g., 'Roof Repair')")
    city: str = Field(..., description="City name (e.g., 'Austin')")
    state: str = Field(..., description="State abbreviation (e.g., 'TX')")
    company_name: str = Field(..., description="Company name")
    phone: str = Field(..., description="Phone number")
    address: str = Field(..., description="Full address")

class GeneratePageRequest(BaseModel):
    """Request model for the /generate-page endpoint."""
    license_key: str
    data: PageData

class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""
    status: str

# Minimal schema block types - no null fields
class HeadingBlock(BaseModel):
    """Heading block with minimal schema."""
    type: str = "heading"
    level: int
    text: str

class ParagraphBlock(BaseModel):
    """Paragraph block with minimal schema."""
    type: str = "paragraph"
    text: str

class FAQBlock(BaseModel):
    """FAQ block with minimal schema."""
    type: str = "faq"
    question: str
    answer: str

class NAPBlock(BaseModel):
    """NAP (Name, Address, Phone) block with minimal schema."""
    type: str = "nap"
    business_name: str
    address: str
    phone: str

class CTABlock(BaseModel):
    """CTA (Call to Action) block with minimal schema."""
    type: str = "cta"
    text: str
    phone: str

# Union type for all block types
PageBlock = Union[HeadingBlock, ParagraphBlock, FAQBlock, NAPBlock, CTABlock]

class GeneratePageResponse(BaseModel):
    """Response model for the /generate-page endpoint."""
    title: str
    meta_description: str
    slug: str
    blocks: List[PageBlock]
