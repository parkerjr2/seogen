"""
Configuration management for the FastAPI application.
Handles environment variables and application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_secret_key = os.getenv("SUPABASE_SECRET_KEY")
        
        # Validate required environment variables
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.supabase_secret_key:
            raise ValueError("SUPABASE_SECRET_KEY environment variable is required")

# Global settings instance
settings = Settings()
