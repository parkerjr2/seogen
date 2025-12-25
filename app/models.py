"""
Pydantic models for request and response validation.
Defines the data structures used by the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Union, Optional

class PageData(BaseModel):
    """Data model for page generation parameters."""
    # Mode selection
    page_mode: str = Field(default="service_city", description="Page mode: 'service_city', 'service_hub', or 'city_hub'")
    
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
    
    # City Hub mode fields (combines hub + city)
    city_slug: str = Field(default="", description="City slug (e.g., 'tulsa-ok')")

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

class ListBlock(BaseModel):
    """List block with minimal schema."""
    type: str = "list"
    items: List[str]

# Union type for all block types
PageBlock = Union[HeadingBlock, ParagraphBlock, FAQBlock, NAPBlock, CTABlock, ListBlock]

class GeneratePageResponse(BaseModel):
    """Response model for the /generate-page endpoint."""
    title: str
    meta_description: str
    slug: str
    blocks: List[PageBlock]


class BulkJobItem(BaseModel):
    """Individual item in a bulk job - supports all page modes."""
    # All fields optional with defaults to support different page modes
    page_mode: str = Field(default="service_city", description="Page mode")
    service: str = Field(default="", description="Service name")
    city: str = Field(default="", description="City name")
    state: str = Field(default="", description="State abbreviation")
    company_name: str = Field(default="", description="Company name")
    phone: str = Field(default="", description="Phone number")
    email: str = Field(default="", description="Email address")
    address: str = Field(default="", description="Address")
    vertical: str = Field(default="", description="Business vertical")
    business_name: str = Field(default="", description="Business name")
    cta_text: str = Field(default="Request a Free Estimate", description="CTA text")
    service_area_label: str = Field(default="", description="Service area label")
    hub_key: str = Field(default="", description="Hub key for service_hub mode")
    hub_label: str = Field(default="", description="Hub label for service_hub mode")
    hub_slug: str = Field(default="", description="Hub slug for service_hub mode")


class BulkJobCreateRequest(BaseModel):
    """Request model for creating a bulk job."""
    license_key: str
    site_url: Optional[str] = None
    job_name: Optional[str] = None
    items: List[BulkJobItem]


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
    service: str = ""
    city: str = ""
    state: str = ""
    page_mode: str = ""
    hub_key: str = ""
    hub_label: str = ""
    hub_slug: str = ""
    city_slug: str = ""
    vertical: str = ""
    business_name: str = ""
    cta_text: str = ""
    service_area_label: str = ""


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
    """Response model for license validation."""
    valid: bool
    status: str | None = None
    page_limit: int | None = None
    pages_used: int | None = None
    pages_remaining: int | None = None
    monthly_limit: int | None = None
    monthly_used: int | None = None
    monthly_remaining: int | None = None
    # WordPress-expected field names (for backward compatibility)
    monthly_generation_limit: int | None = None
    total_pages_generated: int | None = None
    pages_generated_this_month: int | None = None
    pages_remaining_capacity: int | None = None
    pages_remaining_this_month: int | None = None

class SiteRegisterRequest(BaseModel):
    """Request model for site registration."""
    site_url: str
    license_key: str
    secret_key: str
    plugin_version: str | None = None
    wordpress_version: str | None = None

class SiteRegisterResponse(BaseModel):
    """Response model for site registration."""
    success: bool
    message: str | None = None
    license_status: str | None = None
    expires_at: str | None = None
