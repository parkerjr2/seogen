"""
Configuration management for the FastAPI application.
Handles environment variables and application settings.

For Railway deployment:
- Environment variables are set in Railway dashboard
- .env file is used for local development only
- Never commit .env file to version control
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (local development)
# Railway will use environment variables set in dashboard
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_secret_key = os.getenv("SUPABASE_SECRET_KEY")
        
        # Stripe configuration
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        # OpenAI configuration (optional for future AI features)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Validate required environment variables
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.supabase_secret_key:
            raise ValueError("SUPABASE_SECRET_KEY environment variable is required")
        if not self.stripe_webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET environment variable is required")

# Global settings instance
settings = Settings()
