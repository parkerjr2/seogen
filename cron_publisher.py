#!/usr/bin/env python3
"""
Railway Cron Job - Publish Scheduled WordPress Posts
Runs every minute to check all registered WordPress sites
and trigger publishing of ready posts
"""

import asyncio
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import app modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.supabase_client import SupabaseClient

# Load environment
load_dotenv()

# Initialize Supabase client
supabase_client = SupabaseClient()

async def publish_scheduled_posts():
    """Query Supabase and trigger publishing on all active WordPress sites"""

    print(f"[{datetime.now()}] Starting cron run...")

    # Get all active WordPress sites from api_keys table
    try:
        sites = supabase_client.get_cron_enabled_sites()
        print(f"Found {len(sites)} active WordPress sites")

    except Exception as e:
        print(f"Error querying Supabase: {e}")
        return

    # Call each WordPress site to publish ready posts
    async with httpx.AsyncClient() as client:
        for site in sites:
            try:
                # Call WordPress publish endpoint
                result = await client.post(
                    f"{site['wordpress_url']}/wp-json/seogen/v1/publish-scheduled",
                    params={'api_key': site['key']},
                    timeout=30
                )

                if result.status_code == 200:
                    data = result.json()
                    published = data.get('published', 0)
                    pending = data.get('pending', 0)

                    print(f"✓ {site['wordpress_url']}: Published {published} posts, {pending} pending")

                    # Update last_cron_run timestamp
                    supabase_client.update_last_cron_run(
                        api_key=site['key'],
                        timestamp=datetime.utcnow().isoformat()
                    )

                else:
                    print(f"✗ {site['wordpress_url']}: HTTP {result.status_code}")

            except httpx.TimeoutException:
                print(f"✗ {site['wordpress_url']}: Timeout")
            except Exception as e:
                print(f"✗ {site['wordpress_url']}: {e}")

    print(f"[{datetime.now()}] Cron run complete\n")

async def main():
    """Run cron job once (Railway will trigger every 5 minutes)"""
    try:
        await publish_scheduled_posts()
    except Exception as e:
        print(f"ERROR in cron job: {e}")

if __name__ == "__main__":
    print("Starting SEOgen Railway Cron Publisher...")
    asyncio.run(main())
