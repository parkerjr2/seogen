import random
import time
import os
import sys
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from app.supabase_client import supabase_client
from app.ai_generator import ai_generator
from app.models import PageData


MAX_ATTEMPTS = 3
BATCH_LIMIT = 5
CONCURRENT_WORKERS = 3  # Process 3 items simultaneously
IDLE_SLEEP_SECONDS = (2, 5)

# Get replica ID for logging
REPLICA_ID = os.getenv("RAILWAY_REPLICA_ID", "unknown")

def _log(msg: str) -> None:
    print(f"[SEOgen Worker][Replica:{REPLICA_ID}] {msg}")


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check endpoint for Railway."""
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass


def start_health_server():
    """Start health check server in background thread."""
    port = int(os.getenv('PORT', '8080'))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    _log(f"Health check server starting on port {port}")
    server.serve_forever()


async def _process_item_async(item: dict, executor: ThreadPoolExecutor) -> None:
    item_id = str(item.get("id"))
    job_id = str(item.get("job_id"))
    idx = item.get("idx")
    canonical_key = item.get("canonical_key")
    attempts = int(item.get("attempts") or 0)

    if attempts >= MAX_ATTEMPTS:
        _log(f"max attempts reached item_id={item_id} job_id={job_id} idx={idx}")
        supabase_client.update_bulk_item_result(
            item_id=item_id,
            status="failed",
            error="Max attempts exceeded",
        )
        return

    claimed = supabase_client.try_claim_bulk_item(item_id=item_id, attempts=attempts)
    if not claimed:
        _log(f"skipping item_id={item_id} (already claimed by another replica)")
        return

    job = supabase_client.get_bulk_job(job_id)
    if not job:
        supabase_client.update_bulk_item_result(item_id=item_id, status="failed", error="Job not found")
        return

    if (job.get("status") or "").lower() in ("canceled", "failed"):
        supabase_client.update_bulk_item_result(item_id=item_id, status="failed", error=f"Job status={job.get('status')}")
        return

    license_key = str(job.get("license_key") or "")
    license_data = supabase_client.get_license_by_key(license_key)
    if not license_data or license_data.get("status") != "active":
        supabase_client.update_bulk_item_result(item_id=item_id, status="failed", error="License not active")
        supabase_client.recompute_bulk_job_counters(job_id=job_id)
        return

    api_key_id = str(license_data.get("id"))
    
    # Check if API key can generate more pages (dual-limit validation)
    can_generate, reason, stats = supabase_client.check_can_generate(api_key_id)
    if not can_generate:
        _log(f"Cannot generate: {reason} - stats={stats}")
        supabase_client.update_bulk_item_result(item_id=item_id, status="failed", error=reason)
        supabase_client.recompute_bulk_job_counters(job_id=job_id)
        return

    try:
        # Extract all metadata fields from item
        page_mode = str(item.get("page_mode") or "service_city")
        
        _log(f"DEBUG item data: page_mode={page_mode} email='{item.get('email')}' phone='{item.get('phone')}' company=name='{item.get('company_name')}'")
        
        # Build PageData with all fields needed for different page modes
        data = PageData(
            page_mode=page_mode,
            service=str(item.get("service") or ""),
            city=str(item.get("city") or ""),
            state=str(item.get("state") or ""),
            company_name=str(item.get("company_name") or ""),
            phone=str(item.get("phone") or ""),
            email=str(item.get("email") or ""),
            address=str(item.get("address") or ""),
            hub_key=str(item.get("hub_key") or ""),
            hub_label=str(item.get("hub_label") or ""),
            hub_slug=str(item.get("hub_slug") or ""),
            city_slug=str(item.get("city_slug") or ""),
            vertical=str(item.get("vertical") or ""),
            business_name=str(item.get("business_name") or ""),
            cta_text=str(item.get("cta_text") or "Request a Free Estimate"),
            service_area_label=str(item.get("service_area_label") or ""),
        )
        
        _log(f"DEBUG PageData created: page_mode={data.page_mode} hub_key={data.hub_key} email='{data.email}' phone='{data.phone}' company='{data.company_name}'")

        _log(f"generating item_id={item_id} job_id={job_id} idx={idx} key={canonical_key}")
        # Run CPU-intensive AI generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, ai_generator.generate_page_content, data)
        
        # Save result_json immediately after successful generation
        result_data = result.model_dump()
        supabase_client.update_bulk_item_result(
            item_id=item_id,
            status="running",
            result_json=result_data,
        )

        # Log usage immediately after saving result - this ensures usage is tracked
        # even if subsequent operations fail (important for accurate billing/limits)
        usage_logged = supabase_client.log_usage(
            api_key_id=api_key_id,
            action="bulk_item_generation_success",
            details={
                "job_id": job_id,
                "item_id": item_id,
                "idx": idx,
                "canonical_key": canonical_key,
                "service": data.service,
                "city": data.city,
                "state": data.state,
                "title": result.title,
                "slug": result.slug,
            },
        )
        
        if not usage_logged:
            _log(f"WARNING: Failed to log usage for item_id={item_id}")

        # Mark as completed after all operations succeed
        supabase_client.update_bulk_item_result(
            item_id=item_id,
            status="completed",
        )

    except Exception as e:
        _log(f"error generating item_id={item_id} job_id={job_id} idx={idx} attempts={attempts} err={e}")
        # Retry logic: allow 1 retry (attempts 1 and 2), fail on attempt 2+
        if attempts < 2:
            _log(f"retrying item_id={item_id} (attempt {attempts + 1})")
            supabase_client.update_bulk_item_result(
                item_id=item_id,
                status="pending",
                error=f"Retry {attempts + 1}: {str(e)}",
            )
        else:
            _log(f"permanently failing item_id={item_id} after {attempts} attempts")
            supabase_client.update_bulk_item_result(
                item_id=item_id,
                status="failed",
                error=str(e),
            )
        try:
            supabase_client.log_usage(
                license_id=license_id,
                action="bulk_item_generation_failed",
                details={
                    "job_id": job_id,
                    "item_id": item_id,
                    "idx": idx,
                    "canonical_key": canonical_key,
                    "error": str(e),
                    "attempts": attempts,
                },
            )
        except Exception:
            pass

    supabase_client.recompute_bulk_job_counters(job_id=job_id)


async def main_async() -> None:
    _log("worker started")
    
    # Start health check server in background thread
    health_thread = Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    _log(f"argv={sys.argv}")
    _log(f"python={sys.version.splitlines()[0]}")
    _log(f"pid={os.getpid()}")
    _log(
        "env="
        + ",".join(
            [
                f"SUPABASE_URL={'set' if os.getenv('SUPABASE_URL') else 'missing'}",
                f"SUPABASE_SECRET_KEY={'set' if os.getenv('SUPABASE_SECRET_KEY') else 'missing'}",
                f"OPENAI_API_KEY={'set' if os.getenv('OPENAI_API_KEY') else 'missing'}",
            ]
        )
    )
    try:
        ps = subprocess.check_output(["ps", "aux"], text=True)
        ps_lines = "\n".join(ps.splitlines()[:25])
        _log("ps_aux_top=\n" + ps_lines)
    except Exception as e:
        _log(f"ps_aux_failed err={e}")

    last_heartbeat = 0.0
    # Create thread pool for CPU-intensive AI generation
    executor = ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS)
    
    try:
        while True:
            now = time.time()
            if now - last_heartbeat > 60:
                _log("heartbeat")
                last_heartbeat = now

            # Add small random delay to reduce collision probability between replicas
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            _log(f"polling limit={BATCH_LIMIT}")
            items = supabase_client.list_pending_bulk_items(limit=BATCH_LIMIT)
            _log(f"found {len(items)} pending items")
            if not items:
                await asyncio.sleep(random.randint(IDLE_SLEEP_SECONDS[0], IDLE_SLEEP_SECONDS[1]))
                continue

            _log(f"processing {len(items)} items in parallel (max {CONCURRENT_WORKERS} concurrent)")
            # Process items concurrently
            tasks = []
            for item in items:
                _log(f"queuing item_id={item.get('id')} job_id={item.get('job_id')} idx={item.get('idx')}")
                task = asyncio.create_task(_process_item_async(item, executor))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            _log(f"completed batch of {len(items)} items")
    finally:
        executor.shutdown(wait=True)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
