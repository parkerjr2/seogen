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
    
    def deduct_credit(self, license_id: str) -> bool:
        """
        Deduct one credit from a license and return success status.
        
        Args:
            license_id: The license ID to deduct credit from
            
        Returns:
            True if credit deducted successfully, False otherwise
        """
        try:
            with httpx.Client() as client:
                # Update credits_remaining by decrementing by 1
                response = client.patch(
                    f"{self.url}/rest/v1/licenses?id=eq.{license_id}",
                    headers=self.headers,
                    json={"credits_remaining": "credits_remaining - 1"},
                    timeout=10
                )
                
                return response.status_code == 204  # Supabase returns 204 for successful updates
                
        except Exception as e:
            print(f"Error deducting credit: {e}")
            return False

    def deduct_credit_safe(self, license_id: str, current_credits: int) -> bool:
        """Best-effort credit deduction with optimistic concurrency."""
        try:
            new_credits = max(0, int(current_credits) - 1)
            response = self._request(
                "PATCH",
                f"/rest/v1/licenses?id=eq.{license_id}&credits_remaining=eq.{int(current_credits)}",
                json={"credits_remaining": new_credits},
                timeout=10,
            )
            return response.status_code == 204
        except Exception as e:
            print(f"Error deducting credit safely: {e}")
            return False
    
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
        params: dict[str, str] = {
            "job_id": f"eq.{job_id}",
            # Fetch completed and failed items that haven't been imported yet
            "status": f"in.(completed,failed)",
            "select": "id,idx,canonical_key,status,attempts,result_json,error",
            "order": "idx.asc",
            "limit": str(int(limit)),
        }
        # Don't use cursor - fetch ALL unimported items regardless of idx
        # This ensures items that completed out of order aren't skipped
        # The cursor was causing items with lower idx to be missed if they completed after higher idx items
        
        try:
            resp = self._request("GET", "/rest/v1/bulk_job_items", params=params, timeout=15)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data if isinstance(data, list) else []
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
                # Don't overwrite "failed" status
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
