"""
FastAPI application main module.
Defines API endpoints and application configuration.
"""

from fastapi import FastAPI, HTTPException, Query
from app.models import (
    GeneratePageRequest,
    HealthResponse,
    GeneratePageResponse,
    BulkJobCreateRequest,
    BulkJobCreateResponse,
    BulkJobStatusResponse,
    BulkJobResultsResponse,
    BulkJobResultItem,
    BulkJobAckRequest,
    BulkJobAckResponse,
    BulkJobCancelRequest,
)
from app.supabase_client import supabase_client
from app.ai_generator import ai_generator


def _canonical_key(service: str, city: str, state: str) -> str:
    return f"{service.strip().lower()}|{city.strip().lower()}|{state.strip().lower()}"


def _require_active_license(license_key: str) -> dict:
    license_data = supabase_client.get_license_by_key(license_key)
    if not license_data:
        raise HTTPException(status_code=403, detail="License key not found")
    if license_data.get("status") != "active":
        raise HTTPException(status_code=403, detail="License is not active")
    return license_data

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
    license_data = _require_active_license(request.license_key)

    # Preview mode: fast generation, no credits deducted, no usage logs
    if getattr(request, "preview", False):
        license_id = license_data.get("id")
        print(f"/generate-page PREVIEW mode: license_id={license_id} service={request.data.service} city={request.data.city} state={request.data.state}")
        try:
            page_content = ai_generator.generate_page_content_preview(request.data)
            return page_content
        except Exception as e:
            print(f"AI preview generation error for license {license_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"AI preview generation failed: {str(e)}"
            )
    
    # Check if credits remaining
    credits_remaining = license_data.get("credits_remaining", 0)
    if credits_remaining <= 0:
        raise HTTPException(
            status_code=402,
            detail="No credits remaining"
        )
    
    license_id = license_data.get("id")
    print(f"/generate-page FULL mode: license_id={license_id} service={request.data.service} city={request.data.city} state={request.data.state}")
    
    try:
        # Generate AI-powered content with strict validation
        # Validation failures will raise exceptions BEFORE credit deduction
        page_content = ai_generator.generate_page_content(request.data)
        
        # Only deduct credit if content generation and validation succeeded
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
            "title": page_content.title,
            "slug": page_content.slug
        }
        
        usage_logged = supabase_client.log_usage(
            license_id=license_id,
            action="ai_page_generation_success",
            details=usage_details
        )
        
        if not usage_logged:
            print(f"Warning: Failed to log usage for license {license_id}")
        
        return page_content
        
    except Exception as e:
        # Log the validation/generation error for debugging
        print(f"AI generation/validation error for license {license_id}: {str(e)}")
        
        # Log failed attempt (no credit deducted)
        supabase_client.log_usage(
            license_id=license_id,
            action="ai_page_generation_failed",
            details={"error": str(e), "service": request.data.service, "city": request.data.city}
        )
        
        # Return descriptive error - validation failures return HTTP 500
        raise HTTPException(
            status_code=500,
            detail=f"AI content generation failed: {str(e)}"
        )


@app.post("/bulk-jobs", response_model=BulkJobCreateResponse)
async def create_bulk_job(request: BulkJobCreateRequest):
    _require_active_license(request.license_key)
    total_items = len(request.items)
    if total_items <= 0:
        raise HTTPException(status_code=400, detail="No items provided")

    job = supabase_client.create_bulk_job(
        license_key=request.license_key,
        site_url=request.site_url,
        job_name=request.job_name,
        total_items=total_items,
    )
    if not job or not job.get("id"):
        raise HTTPException(status_code=500, detail="Failed to create bulk job")

    job_id = job["id"]
    items_payload: list[dict] = []
    for idx, item in enumerate(request.items):
        items_payload.append(
            {
                "job_id": job_id,
                "idx": idx,
                "service": item.service,
                "city": item.city,
                "state": item.state,
                "company_name": item.company_name,
                "phone": item.phone,
                "address": item.address,
                "canonical_key": _canonical_key(item.service, item.city, item.state),
                "status": "pending",
                "attempts": 0,
            }
        )

    ok = supabase_client.insert_bulk_job_items(items=items_payload)
    if not ok:
        supabase_client.cancel_bulk_job(job_id=job_id)
        raise HTTPException(status_code=500, detail="Failed to insert bulk job items")

    return BulkJobCreateResponse(job_id=str(job_id), total_items=total_items)


@app.get("/bulk-jobs/{job_id}", response_model=BulkJobStatusResponse)
async def get_bulk_job_status(job_id: str, license_key: str = Query(...)):
    _require_active_license(license_key)
    job = supabase_client.get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("license_key") != license_key:
        raise HTTPException(status_code=403, detail="Job does not belong to license")

    counters = supabase_client.recompute_bulk_job_counters(job_id=job_id) or {}
    return BulkJobStatusResponse(
        job_id=str(job_id),
        status=str(counters.get("status") or job.get("status") or ""),
        total_items=int(counters.get("total_items") or job.get("total_items") or 0),
        processed=int(counters.get("processed") or job.get("processed") or 0),
        completed=int(counters.get("completed") or job.get("completed") or 0),
        failed=int(counters.get("failed") or job.get("failed") or 0),
    )


@app.get("/bulk-jobs/{job_id}/results", response_model=BulkJobResultsResponse)
async def get_bulk_job_results(
    job_id: str,
    license_key: str = Query(...),
    status: str = Query("completed"),
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
):
    _require_active_license(license_key)
    job = supabase_client.get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("license_key") != license_key:
        raise HTTPException(status_code=403, detail="Job does not belong to license")

    cursor_idx = int(cursor) if cursor is not None and str(cursor).isdigit() else None
    rows = supabase_client.get_bulk_job_results(job_id=job_id, status=status, cursor_idx=cursor_idx, limit=limit)
    items: list[BulkJobResultItem] = []
    next_cursor: str | None = None
    for r in rows:
        if r.get("result_json") is None:
            continue
        items.append(
            BulkJobResultItem(
                item_id=str(r.get("id")),
                idx=int(r.get("idx") or 0),
                canonical_key=str(r.get("canonical_key") or ""),
                result_json=r.get("result_json") or {},
            )
        )
        next_cursor = str(int(r.get("idx") or 0))
    return BulkJobResultsResponse(items=items, next_cursor=next_cursor)


@app.post("/bulk-jobs/{job_id}/ack", response_model=BulkJobAckResponse)
async def ack_bulk_job_results(job_id: str, request: BulkJobAckRequest):
    _require_active_license(request.license_key)
    job = supabase_client.get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("license_key") != request.license_key:
        raise HTTPException(status_code=403, detail="Job does not belong to license")
    imported = supabase_client.mark_bulk_items_imported(job_id=job_id, item_ids=request.imported_item_ids)
    supabase_client.recompute_bulk_job_counters(job_id=job_id)
    return BulkJobAckResponse(job_id=str(job_id), imported_count=int(imported))


@app.post("/bulk-jobs/{job_id}/cancel")
async def cancel_bulk_job(job_id: str, request: BulkJobCancelRequest):
    _require_active_license(request.license_key)
    job = supabase_client.get_bulk_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("license_key") != request.license_key:
        raise HTTPException(status_code=403, detail="Job does not belong to license")
    ok = supabase_client.cancel_bulk_job(job_id=job_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to cancel job")
    return {"job_id": str(job_id), "status": "canceled"}
