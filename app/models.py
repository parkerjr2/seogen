"""
Pydantic models for request and response validation.
Defines the data structures used by the API endpoints.
"""

from pydantic import BaseModel
from typing import List

class GeneratePageRequest(BaseModel):
    """Request model for the /generate-page endpoint."""
    license_key: str

class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""
    status: str

class PageBlock(BaseModel):
    """Individual content block in a generated page."""
    type: str
    text: str

class GeneratePageResponse(BaseModel):
    """Response model for the /generate-page endpoint."""
    title: str
    blocks: List[PageBlock]
