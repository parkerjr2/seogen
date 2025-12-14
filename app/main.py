"""
FastAPI application main module.
Defines API endpoints and application configuration.
"""

from fastapi import FastAPI, HTTPException
from app.models import GeneratePageRequest, HealthResponse, GeneratePageResponse, PageBlock
from app.supabase_client import supabase_client

# Create FastAPI application instance
app = FastAPI(
    title="SEOgen API",
    description="Phase 2 MVP API for license validation and page generation",
    version="2.0.0"
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        Simple status response indicating API is operational
    """
    return HealthResponse(status="ok")

@app.post("/generate-page", response_model=GeneratePageResponse)
async def generate_page(request: GeneratePageRequest):
    """
    Generate a page based on license validation.
    
    Args:
        request: Contains the license_key to validate
        
    Returns:
        Generated page content with title and blocks
        
    Raises:
        HTTPException: 403 if license not found or inactive
        HTTPException: 402 if no credits remaining
    """
    # Look up license in Supabase
    license_data = supabase_client.get_license_by_key(request.license_key)
    
    # Check if license exists
    if not license_data:
        raise HTTPException(
            status_code=403,
            detail="License key not found"
        )
    
    # Check if license is active
    if license_data.get("status") != "active":
        raise HTTPException(
            status_code=403,
            detail="License is not active"
        )
    
    # Check if credits remaining
    credits_remaining = license_data.get("credits_remaining", 0)
    if credits_remaining <= 0:
        raise HTTPException(
            status_code=402,
            detail="No credits remaining"
        )
    
    # Return dummy page content for Phase 2
    return GeneratePageResponse(
        title="Test Roofing Service Page",
        blocks=[
            PageBlock(
                type="heading",
                text="Roof Repair in Dallas, TX"
            ),
            PageBlock(
                type="paragraph",
                text="This is placeholder content for Phase 2."
            )
        ]
    )
