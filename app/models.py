"""
Pydantic models for request and response validation.
Defines the data structures used by the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Union

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

class PageBlock(BaseModel):
    """Individual content block in a generated page."""
    type: str
    text: Optional[str] = None
    level: Optional[int] = None  # For heading blocks
    question: Optional[str] = None  # For FAQ blocks
    answer: Optional[str] = None  # For FAQ blocks
    business_name: Optional[str] = None  # For NAP blocks
    address: Optional[str] = None  # For NAP blocks
    phone: Optional[str] = None  # For NAP and CTA blocks

class GeneratePageResponse(BaseModel):
    """Response model for the /generate-page endpoint."""
    title: str
    meta_description: str
    slug: str
    blocks: List[PageBlock]
