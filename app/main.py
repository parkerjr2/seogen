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
    ValidateLicenseRequest,
    ValidateLicenseResponse,
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

@app.post("/validate-license", response_model=ValidateLicenseResponse)
async def validate_license(request: ValidateLicenseRequest):
    """
    Validate a license key and return its status and dual-limit credit information.
    
    Args:
        request: Contains license_key to validate
        
    Returns:
        License status, page limits, and usage statistics
        
    Raises:
        HTTPException: 403 if license not found
    """
    license_data = supabase_client.get_license_by_key(request.license_key)
    if not license_data:
        raise HTTPException(status_code=403, detail="License key not found")
    
    license_id = license_data.get("id")
    
    # Get dual-limit stats
    can_generate, reason, stats = supabase_client.check_can_generate(license_id)
    
    return ValidateLicenseResponse(
        status=license_data.get("status", "unknown"),
        credits_remaining=license_data.get("credits_remaining", 0),  # Deprecated
        page_limit=stats.get("page_limit", 500),
        monthly_generation_limit=stats.get("monthly_limit", 500),
        total_pages_generated=stats.get("total_pages", 0),
        pages_generated_this_month=stats.get("period_pages", 0),
        pages_remaining_capacity=stats.get("pages_remaining_capacity", 0),
        pages_remaining_this_month=stats.get("pages_remaining_this_month", 0),
        current_period_start=license_data.get("current_period_start", "")
    )

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
        api_key_id = license_data.get("id")
        page_mode = getattr(request.data, "page_mode", "service_city")
        if page_mode == "service_hub":
            hub_key = getattr(request.data, "hub_key", "")
            hub_label = getattr(request.data, "hub_label", "")
            print(f"/generate-page PREVIEW mode: api_key_id={api_key_id} page_mode={page_mode} hub_key={hub_key} hub_label={hub_label}")
        else:
            print(f"/generate-page PREVIEW mode: api_key_id={api_key_id} page_mode={page_mode} service={request.data.service} city={request.data.city} state={request.data.state}")
        try:
            page_content = ai_generator.generate_page_content(request.data)
            return page_content
        except Exception as e:
            print(f"AI preview generation error for api_key {api_key_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"AI preview generation failed: {str(e)}"
            )
    
    api_key_id = license_data.get("id")
    
    # Check if API key can generate more pages (dual-limit validation)
    can_generate, reason, stats = supabase_client.check_can_generate(api_key_id)
    if not can_generate:
        print(f"/generate-page BLOCKED: api_key_id={api_key_id} reason={reason} stats={stats}")
        raise HTTPException(
            status_code=402,
            detail=reason
        )
    
    page_mode = getattr(request.data, "page_mode", "service_city")
    if page_mode == "service_hub":
        hub_key = getattr(request.data, "hub_key", "")
        print(f"/generate-page FULL mode: api_key_id={api_key_id} page_mode={page_mode} hub_key={hub_key} stats={stats}")
    else:
        print(f"/generate-page FULL mode: api_key_id={api_key_id} page_mode={page_mode} service={request.data.service} city={request.data.city} state={request.data.state} stats={stats}")
    
    try:
        # Generate AI-powered content with strict validation
        page_content = ai_generator.generate_page_content(request.data)
        
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
            api_key_id=api_key_id,
            action="ai_page_generation_success",
            details=usage_details
        )
        
        if not usage_logged:
            print(f"Warning: Failed to log usage for api_key {api_key_id}")
        
        return page_content
        
    except Exception as e:
        # Log the validation/generation error for debugging
        print(f"AI generation/validation error for api_key {api_key_id}: {str(e)}")
        
        # Log failed attempt (no credit deducted)
        supabase_client.log_usage(
            api_key_id=api_key_id,
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
    print(f"[API /bulk-jobs POST] Received request: license_key={request.license_key[:8]}... site_url={request.site_url} job_name={request.job_name} items_count={len(request.items)}")
    _require_active_license(request.license_key)
    total_items = len(request.items)
    if not request.items:
        print(f"[API /bulk-jobs POST] ERROR: No items provided in request")
        raise HTTPException(status_code=400, detail="No items provided")
    print(f"[API /bulk-jobs POST] Creating bulk job with {len(request.items)} items")

    try:
        print(f"[API /bulk-jobs POST] Calling supabase_client.create_bulk_job")
        job = supabase_client.create_bulk_job(
            license_key=request.license_key,
            site_url=request.site_url or "",
            job_name=request.job_name or "",
            total_items=total_items,
        )
        print(f"[API /bulk-jobs POST] Created job_id={job['id']}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bulk job: {str(e)}")

    if not job or not job.get("id"):
        raise HTTPException(status_code=500, detail="Failed to create bulk job: Supabase returned no job id")

    job_id = job["id"]
    items_payload: list[dict] = []
    for idx, item in enumerate(request.items):
        print(f"[API /bulk-jobs POST] Inserting {len(request.items)} bulk job items")
        
        # Handle different page modes - service and city are optional for hub pages
        service = getattr(item, 'service', '') or ''
        city = getattr(item, 'city', '') or ''
        state = getattr(item, 'state', '') or ''
        
        items_payload.append(
            {
                "job_id": job_id,
                "idx": idx,
                "service": service,
                "city": city,
                "state": state,
                "company_name": item.company_name,
                "phone": item.phone,
                "email": item.email,
                "address": item.address,
                "canonical_key": _canonical_key(service, city, state),
                "status": "pending",
                "attempts": 0,
            }
        )
    try:
        print(f"[API /bulk-jobs POST] Calling supabase_client.insert_bulk_job_items")
        print(f"[API /bulk-jobs POST] DEBUG items_payload sample: {items_payload[0] if items_payload else 'empty'}")
        ok = supabase_client.insert_bulk_job_items(items=items_payload)
        print(f"[API /bulk-jobs POST] Successfully inserted items")
    except Exception as e:
        supabase_client.cancel_bulk_job(job_id=job_id)
        raise HTTPException(status_code=500, detail=f"Failed to insert bulk job items: {str(e)}")

    if not ok:
        supabase_client.cancel_bulk_job(job_id=job_id)
        raise HTTPException(status_code=500, detail="Failed to insert bulk job items: unknown error")

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
        item_status = str(r.get("status") or "")
        items.append(
            BulkJobResultItem(
                item_id=str(r.get("id")),
                idx=int(r.get("idx") or 0),
                canonical_key=str(r.get("canonical_key") or ""),
                status=item_status,
                attempts=int(r.get("attempts") or 0),
                result_json=r.get("result_json") if item_status == "completed" else None,
                error=str(r.get("error") or "") if item_status == "failed" and r.get("error") else None,
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


@app.post("/admin/reset-monthly-periods")
async def reset_monthly_periods(secret: str = Query(...)):
    """
    Admin endpoint to reset monthly generation periods.
    Called by external cron service (e.g., cron-job.org) once per month.
    
    Args:
        secret: Admin secret for authentication
        
    Returns:
        Success message if reset completed
        
    Raises:
        HTTPException: 403 if secret is invalid, 500 if reset fails
    """
    import os
    
    # Validate admin secret
    admin_secret = os.getenv("ADMIN_SECRET")
    if not admin_secret or secret != admin_secret:
        print(f"[ADMIN] Invalid secret attempt")
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    print(f"[ADMIN] Monthly period reset requested")
    
    try:
        # Call Supabase stored procedure to reset monthly periods
        response = supabase_client._request(
            "POST",
            "/rest/v1/rpc/reset_monthly_generation_periods",
            timeout=30
        )
        
        if response.status_code == 200 or response.status_code == 204:
            print(f"[ADMIN] Monthly periods reset successfully")
            return {
                "status": "success",
                "message": "Monthly generation periods reset successfully"
            }
        else:
            print(f"[ADMIN] Failed to reset: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reset periods: {response.status_code}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN] Error resetting periods: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
