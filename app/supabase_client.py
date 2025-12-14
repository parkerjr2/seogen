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

# Global Supabase client instance
supabase_client = SupabaseClient()
