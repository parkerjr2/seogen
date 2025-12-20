"""
Pydantic models for request and response validation.
Defines the data structures used by the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Union, Optional

class PageData(BaseModel):
    """Data model for page generation parameters."""
    # Mode selection
    page_mode: str = Field(default="service_city", description="Page mode: 'service_city' or 'service_hub'")
    
    # Universal fields
    vertical: str = Field(default="", description="Business vertical (e.g., 'electrician', 'plumber', 'roofer')")
    business_name: str = Field(default="", description="Business name")
    phone: str = Field(default="", description="Phone number")
    cta_text: str = Field(default="Request a Free Estimate", description="Primary CTA text")
    service_area_label: str = Field(default="", description="Service area label (e.g., 'Tulsa Metro')")
    
    # Service+City mode fields
    service: str = Field(default="", description="Service type (e.g., 'Roof Repair')")
    city: str = Field(default="", description="City name (e.g., 'Austin')")
    state: str = Field(default="", description="State abbreviation (e.g., 'TX')")
    company_name: str = Field(default="", description="Company name (deprecated, use business_name)")
    email: str = Field(default="", description="Email address (optional)")
    address: str = Field(default="", description="Full address (optional)")
    
    # Service Hub mode fields
    hub_key: str = Field(default="", description="Hub key (e.g., 'residential', 'commercial')")
    hub_label: str = Field(default="", description="Hub label (e.g., 'Residential')")
    hub_slug: str = Field(default="", description="Hub slug (e.g., 'residential-services')")
    services_for_hub: List[dict] = Field(default_factory=list, description="List of services for hub page")

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
    """NAP (Name, Address, Phone, Email) block with minimal schema."""
    type: str = "nap"
    business_name: str
    phone: str
    email: str
    address: str

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
    company_name: str = ""  # Optional
    phone: str = ""  # Optional
    email: str = ""  # Optional
    address: str = ""  # Optional


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
    credits_remaining: int  # Deprecated - kept for backward compatibility
    page_limit: int
    monthly_generation_limit: int
    total_pages_generated: int
    pages_generated_this_month: int
    pages_remaining_capacity: int
    pages_remaining_this_month: int
    current_period_start: str
