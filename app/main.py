"""
FastAPI application main module.
Defines API endpoints and application configuration.
"""

from fastapi import FastAPI, HTTPException
from app.models import GeneratePageRequest, HealthResponse, GeneratePageResponse, PageBlock
from app.supabase_client import supabase_client
from app.ai_generator import ai_generator

# Create FastAPI application instance
app = FastAPI(
    title="SEOgen API",
    description="Phase 3 AI-powered API for license validation and SEO-optimized page generation",
    version="3.0.0"
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
    Generate AI-powered, SEO-optimized page content for roofing services.
    
    Args:
        request: Contains license_key and page data (service, city, company info)
        
    Returns:
        AI-generated page content with title, meta description, and structured blocks
        
    Raises:
        HTTPException: 403 if license not found or inactive
        HTTPException: 402 if no credits remaining
        HTTPException: 500 if AI generation fails
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
    
    license_id = license_data.get("id")
    
    try:
        # Generate AI-powered content using OpenAI
        # This enforces all SEO requirements and validates content structure
        page_content = ai_generator.generate_page_content(request.data)
        
        # Deduct one credit from the license
        credit_deducted = supabase_client.deduct_credit(license_id)
        if not credit_deducted:
            # Log the error but don't fail the request since content was generated
            print(f"Warning: Failed to deduct credit for license {license_id}")
        
        # Log usage for analytics and tracking
        usage_details = {
            "service": request.data.service,
            "city": request.data.city,
            "state": request.data.state,
            "company_name": request.data.company_name,
            "content_blocks": len(page_content.blocks),
            "title": page_content.title
        }
        
        usage_logged = supabase_client.log_usage(
            license_id=license_id,
            action="ai_page_generation",
            details=usage_details
        )
        
        if not usage_logged:
            print(f"Warning: Failed to log usage for license {license_id}")
        
        return page_content
        
    except Exception as e:
        # Log the error for debugging
        print(f"AI generation error for license {license_id}: {str(e)}")
        
        # Return descriptive error to help with debugging
        raise HTTPException(
            status_code=500,
            detail=f"AI content generation failed: {str(e)}"
        )
