"""
Supabase client configuration and database operations.
Centralizes all database interactions for the application.
"""

import httpx
from app.config import settings


def _chunk_list(values: list, chunk_size: int) -> list[list]:
    out: list[list] = []
    for i in range(0, len(values), chunk_size):
        out.append(values[i : i + chunk_size])
    return out

class SupabaseClient:
    """HTTP-based Supabase client for reliable database operations."""
    
    def __init__(self):
        """Initialize Supabase client with configuration from settings."""
        # Use Supabase secret key for full read/write access to the database
        # This key should never be exposed to frontend/public code
        self.url = settings.supabase_url
        self.headers = {
            "apikey": settings.supabase_secret_key,
            "Authorization": f"Bearer {settings.supabase_secret_key}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str, *, params: dict | None = None, json: dict | list | None = None, extra_headers: dict | None = None, timeout: int = 15) -> httpx.Response:
        url = f"{self.url}{path}"
        headers = dict(self.headers)
        if extra_headers:
            headers.update(extra_headers)
        with httpx.Client() as client:
            return client.request(method, url, params=params, headers=headers, json=json, timeout=timeout)
    
    def get_license_by_key(self, license_key: str) -> dict | None:
        """
        Retrieve license information by license key using HTTP API.
        
        Args:
            license_key: The license key to look up
            
        Returns:
            License data as dict if found, None if not found
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.url}/rest/v1/licenses?license_key=eq.{license_key}&select=*",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Return first result if found, None if no results
                    if data and len(data) > 0:
                        return data[0]
                    return None
                else:
                    # Log the error in a real application
                    print(f"HTTP Error {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            # Log the error in a real application
            print(f"Error querying license: {e}")
            return None
    
    def check_can_generate(self, license_id: str) -> tuple[bool, str, dict]:
        """
        Check if license can generate more pages based on dual limits:
        1. Total pages must be < page_limit (capacity)
        2. Pages generated this month must be < monthly_generation_limit
        
        Args:
            license_id: The license ID to check
            
        Returns:
            Tuple of (can_generate: bool, reason: str, stats: dict)
        """
        try:
            # Get license data
            response = self._request(
                "GET",
                f"/rest/v1/licenses?id=eq.{license_id}&select=*",
                timeout=10
            )
            if response.status_code != 200:
                return False, "License not found", {}
            
            licenses = response.json()
            if not licenses:
                return False, "License not found", {}
            
            license_data = licenses[0]
            page_limit = int(license_data.get("page_limit", 500))
            monthly_limit = int(license_data.get("monthly_generation_limit", 500))
            period_start = license_data.get("current_period_start")
            
            # Count total pages generated (all time)
            total_response = self._request(
                "GET",
                f"/rest/v1/usage_logs?license_id=eq.{license_id}&action=in.(ai_page_generation_success,bulk_item_generation_success)&select=id",
                timeout=10
            )
            total_pages = len(total_response.json()) if total_response.status_code == 200 else 0
            
            # Count pages generated this period
            period_response = self._request(
                "GET",
                f"/rest/v1/usage_logs?license_id=eq.{license_id}&action=in.(ai_page_generation_success,bulk_item_generation_success)&created_at=gte.{period_start}&select=id",
                timeout=10
            )
            period_pages = len(period_response.json()) if period_response.status_code == 200 else 0
            
            stats = {
                "total_pages": total_pages,
                "page_limit": page_limit,
                "pages_remaining_capacity": page_limit - total_pages,
                "period_pages": period_pages,
                "monthly_limit": monthly_limit,
                "pages_remaining_this_month": monthly_limit - period_pages
            }
            
            # Check both limits
            if total_pages >= page_limit:
                return False, f"Page limit reached ({total_pages}/{page_limit}). Delete pages to generate more.", stats
            
            if period_pages >= monthly_limit:
                return False, f"Monthly generation limit reached ({period_pages}/{monthly_limit}). Resets next month.", stats
            
            return True, "Can generate", stats
            
        except Exception as e:
            print(f"Error checking generation limits: {e}")
            return False, f"Error: {str(e)}", {}
    
    # DEPRECATED: Keep for backward compatibility but no longer used
    def deduct_credit(self, license_id: str) -> bool:
        """DEPRECATED: Credits are now tracked via usage_logs, not deducted from balance."""
        # No-op: we now track via usage_logs instead of deducting
        return True

    def deduct_credit_safe(self, license_id: str, current_credits: int) -> bool:
        """DEPRECATED: Credits are now tracked via usage_logs, not deducted from balance."""
        # No-op: we now track via usage_logs instead of deducting
        return True
    
    def log_usage(self, license_id: str, action: str, details: dict = None) -> bool:
        """
        Log usage to the usage_logs table for tracking and analytics.
        
        Args:
            license_id: The license ID that performed the action
            action: The action performed (e.g., 'page_generation')
            details: Optional additional details about the usage
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            with httpx.Client() as client:
                log_data = {
                    "license_id": license_id,
                    "action": action,
                    "details": details or {},
                    "created_at": "now()"  # Supabase function for current timestamp
                }
                
                response = client.post(
                    f"{self.url}/rest/v1/usage_logs",
                    headers=self.headers,
                    json=log_data,
                    timeout=10
                )
                
                return response.status_code == 201  # Supabase returns 201 for successful inserts
                
        except Exception as e:
            print(f"Error logging usage: {e}")
            return False

    def create_bulk_job(self, *, license_key: str, site_url: str | None, job_name: str | None, total_items: int) -> dict | None:
        payload = {
            "license_key": license_key,
            "site_url": site_url,
            "job_name": job_name,
            "status": "running",
            "total_items": int(total_items),
            "processed": 0,
            "completed": 0,
            "failed": 0,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        resp = self._request(
            "POST",
            "/rest/v1/bulk_jobs",
            json=payload,
            extra_headers={"Prefer": "return=representation"},
            timeout=15,
        )
        if resp.status_code != 201:
            raise RuntimeError(f"create_bulk_job HTTP {resp.status_code}: {resp.text}")
        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
        return None

    def insert_bulk_job_items(self, *, items: list[dict]) -> bool:
        if not items:
            return True
        resp = self._request(
            "POST",
            "/rest/v1/bulk_job_items",
            json=items,
            extra_headers={"Prefer": "return=minimal"},
            timeout=30,
        )
        if resp.status_code not in (201, 204):
            raise RuntimeError(f"insert_bulk_job_items HTTP {resp.status_code}: {resp.text}")
        return True

    def get_bulk_job(self, job_id: str) -> dict | None:
        job_id = str(job_id)
        try:
            resp = self._request(
                "GET",
                "/rest/v1/bulk_jobs",
                params={"id": f"eq.{job_id}", "select": "*"},
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0]
            return None
        except Exception:
            return None

    def cancel_bulk_job(self, *, job_id: str) -> bool:
        try:
            resp = self._request(
                "PATCH",
                "/rest/v1/bulk_jobs",
                params={"id": f"eq.{job_id}"},
                json={"status": "canceled"},
                timeout=10,
            )
            return resp.status_code == 204
        except Exception:
            return False

    def get_bulk_job_results(self, *, job_id: str, status: str = "completed", cursor_idx: int | None = None, limit: int = 20) -> list[dict]:
        # Fetch completed/failed items that haven't been imported yet
        # For efficiency with large jobs, we use the cursor but ALSO check for any
        # items before the cursor that might have completed out of order
        
        try:
            # First, get items after the cursor (normal progression)
            params_after: dict[str, str] = {
                "job_id": f"eq.{job_id}",
                "status": f"in.(completed,failed)",
                "select": "id,idx,canonical_key,status,attempts,result_json,error",
                "order": "idx.asc",
                "limit": str(int(limit)),
            }
            if cursor_idx is not None:
                params_after["idx"] = f"gt.{cursor_idx}"
            
            resp = self._request("GET", "/rest/v1/bulk_job_items", params=params_after, timeout=15)
            if resp.status_code != 200:
                return []
            items_after = resp.json() if resp.status_code == 200 else []
            items_after = items_after if isinstance(items_after, list) else []
            
            # Also check for any completed items BEFORE the cursor (out-of-order completions)
            # Only do this if we have a cursor and didn't get a full batch
            items_before = []
            if cursor_idx is not None and len(items_after) < limit:
                params_before: dict[str, str] = {
                    "job_id": f"eq.{job_id}",
                    "status": f"in.(completed,failed)",
                    "idx": f"lt.{cursor_idx}",
                    "select": "id,idx,canonical_key,status,attempts,result_json,error",
                    "order": "idx.asc",
                    "limit": str(int(limit - len(items_after))),
                }
                resp_before = self._request("GET", "/rest/v1/bulk_job_items", params=params_before, timeout=15)
                if resp_before.status_code == 200:
                    items_before = resp_before.json()
                    items_before = items_before if isinstance(items_before, list) else []
            
            # Combine and sort by idx
            all_items = items_before + items_after
            all_items.sort(key=lambda x: x.get('idx', 0))
            return all_items[:limit]
            
        except Exception:
            return []

    def mark_bulk_items_imported(self, *, job_id: str, item_ids: list[str]) -> int:
        if not item_ids:
            return 0
        imported = 0
        try:
            for chunk in _chunk_list(item_ids, 100):
                ids = ",".join(chunk)
                # Only mark as imported if status is "completed"
                # Items with status="failed" should remain failed - they weren't actually imported
                resp = self._request(
                    "PATCH",
                    "/rest/v1/bulk_job_items",
                    params={"job_id": f"eq.{job_id}", "id": f"in.({ids})", "status": "eq.completed"},
                    json={"status": "imported"},
                    timeout=20,
                )
                if resp.status_code == 204:
                    imported += len(chunk)
            return imported
        except Exception as e:
            print(f"Error acking imported items: {e}")
            return imported

    def list_pending_bulk_items(self, *, limit: int = 5) -> list[dict]:
        params = {
            "status": "in.(pending,running)",
            "select": "id,job_id,idx,service,city,state,company_name,phone,email,address,canonical_key,attempts",
            "order": "created_at.asc,idx.asc",
            "limit": str(int(limit)),
        }
        try:
            resp = self._request("GET", "/rest/v1/bulk_job_items", params=params, timeout=15)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def try_claim_bulk_item(self, *, item_id: str, attempts: int) -> bool:
        try:
            resp = self._request(
                "PATCH",
                "/rest/v1/bulk_job_items",
                params={"id": f"eq.{item_id}", "status": "eq.pending"},
                json={"status": "running", "attempts": int(attempts) + 1},
                timeout=10,
            )
            return resp.status_code == 204
        except Exception:
            return False

    def update_bulk_item_result(self, *, item_id: str, status: str, result_json: dict | None = None, error: str | None = None) -> bool:
        payload: dict = {"status": status}
        if result_json is not None:
            payload["result_json"] = result_json
        if error is not None:
            payload["error"] = error
        try:
            resp = self._request(
                "PATCH",
                "/rest/v1/bulk_job_items",
                params={"id": f"eq.{item_id}"},
                json=payload,
                timeout=30,
            )
            return resp.status_code == 204
        except Exception:
            return False

    def recompute_bulk_job_counters(self, *, job_id: str) -> dict | None:
        try:
            items_resp = self._request(
                "GET",
                "/rest/v1/bulk_job_items",
                params={"job_id": f"eq.{job_id}", "select": "status"},
                timeout=30,
            )
            if items_resp.status_code != 200:
                return None
            statuses = items_resp.json()
            if not isinstance(statuses, list):
                return None

            processed = 0
            completed = 0
            failed = 0
            for row in statuses:
                s = (row.get("status") or "").lower()
                if s in ("completed", "failed", "imported"):
                    processed += 1
                if s in ("completed", "imported"):
                    completed += 1
                if s == "failed":
                    failed += 1

            job = self.get_bulk_job(job_id)
            total_items = int(job.get("total_items", 0)) if job else 0
            current_status = (job.get("status") if job else "")

            new_status = None
            if current_status not in ("canceled", "failed"):
                if total_items > 0 and (completed + failed) >= total_items:
                    new_status = "complete"
                else:
                    new_status = "running"

            payload: dict = {"processed": processed, "completed": completed, "failed": failed}
            if new_status:
                payload["status"] = new_status

            patch = self._request(
                "PATCH",
                "/rest/v1/bulk_jobs",
                params={"id": f"eq.{job_id}"},
                json=payload,
                timeout=15,
            )
            if patch.status_code != 204:
                return None

            payload["total_items"] = total_items
            payload["status"] = new_status or current_status
            return payload
        except Exception as e:
            print(f"Error recomputing bulk counters: {e}")
            return None

# Global Supabase client instance
supabase_client = SupabaseClient()
