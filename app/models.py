"""
Pydantic models for request and response validation.
Defines the data structures used by the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Union, Optional

class PageData(BaseModel):
    """Data model for page generation parameters."""
    service: str = Field(..., description="Service type (e.g., 'Roof Repair')")
    city: str = Field(..., description="City name (e.g., 'Austin')")
    state: str = Field(default="", description="State abbreviation (e.g., 'TX') - optional for neighborhoods")
    company_name: str = Field(..., description="Company name")
    phone: str = Field(..., description="Phone number")
    address: str = Field(..., description="Full address")

class GeneratePageRequest(BaseModel):
    """Request model for the /generate-page endpoint."""
    license_key: str
    data: PageData
    preview: bool = False

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


class BulkJobItemInput(BaseModel):
    service: str
    city: str
    state: str = ""  # Optional - empty string for city/neighborhood-only entries
    company_name: str
    phone: str
    address: str


class BulkJobCreateRequest(BaseModel):
    license_key: str
    site_url: Optional[str] = None
    job_name: Optional[str] = None
    items: List[BulkJobItemInput]


class BulkJobCreateResponse(BaseModel):
    job_id: str
    total_items: int


class BulkJobStatusResponse(BaseModel):
    job_id: str
    status: str
    total_items: int
    processed: int
    completed: int
    failed: int


class BulkJobResultItem(BaseModel):
    item_id: str
    idx: int
    canonical_key: str
    status: str
    attempts: int = 0
    result_json: Optional[dict] = None
    error: Optional[str] = None


class BulkJobResultsResponse(BaseModel):
    items: List[BulkJobResultItem]
    next_cursor: Optional[str] = None


class BulkJobAckRequest(BaseModel):
    license_key: str
    imported_item_ids: List[str]


class BulkJobAckResponse(BaseModel):
    job_id: str
    imported_count: int


class BulkJobCancelRequest(BaseModel):
    license_key: str


class ValidateLicenseRequest(BaseModel):
    license_key: str


class ValidateLicenseResponse(BaseModel):
    status: str
    credits_remaining: int
