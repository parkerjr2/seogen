"""
Supabase client configuration and database operations.
Centralizes all database interactions for the application.
"""

import httpx
from app.config import settings

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

# Global Supabase client instance
supabase_client = SupabaseClient()
