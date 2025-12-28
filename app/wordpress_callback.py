"""
WordPress Callback Module
Handles secure backend-to-WordPress callbacks for auto-import
"""

import hashlib
import hmac
import time
import httpx
import asyncio
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def generate_hmac_signature(
    body: str,
    secret: str,
    timestamp: Optional[int] = None
) -> Tuple[str, str, str]:
    """
    Generate HMAC signature for WordPress callback
    
    Args:
        body: Request body as string
        secret: Callback secret shared with WordPress
        timestamp: Unix timestamp (defaults to current time)
    
    Returns:
        Tuple of (timestamp, body_hash, signature)
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    # Compute body hash
    body_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    
    # Compute HMAC signature
    message = f"{timestamp}.{body_hash}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return str(timestamp), body_hash, signature


async def push_to_wordpress(
    wordpress_rest_url: str,
    callback_secret: str,
    license_key: str,
    job_id: str,
    item_index: int,
    result_json: Dict[str, Any],
    item_metadata: Dict[str, Any],
    max_retries: int = 3,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Push completed page to WordPress REST API with retry logic
    
    Args:
        wordpress_rest_url: WordPress REST API base URL (e.g., https://example.com/wp-json/seogen/v1/)
        callback_secret: Shared secret for HMAC signing
        license_key: License key for verification
        job_id: Bulk job ID
        item_index: Item index in job
        result_json: Generated page content
        item_metadata: Item metadata (service, city, state, etc.)
        max_retries: Maximum retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Dict with success status, post_id, and error info
    """
    endpoint = wordpress_rest_url.rstrip('/') + '/import-page'
    
    payload = {
        "license_key": license_key,
        "job_id": job_id,
        "item_index": item_index,
        "result_json": result_json,
        "item_metadata": item_metadata
    }
    
    # Serialize payload
    import json
    body = json.dumps(payload)
    
    # Generate HMAC signature
    timestamp, body_hash, signature = generate_hmac_signature(body, callback_secret)
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SEOgen-Backend/1.0 (Bulk Page Generator)",
        "X-Seogen-Timestamp": timestamp,
        "X-Seogen-Body-SHA256": body_hash,
        "X-Seogen-Signature": signature,
        "X-Seogen-Signature-Version": "1"
    }
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    content=body,
                    headers=headers,
                    timeout=timeout
                )
                
                # Phase 1: Detect WAF/CAPTCHA blocks (HTML responses on error codes)
                # Only check for WAF if we got an error status code (4xx, 5xx)
                if response.status_code >= 400:
                    content_type = response.headers.get("content-type", "").lower()
                    is_html = "text/html" in content_type or response.text.strip().startswith("<html")
                    
                    if is_html:
                        # Check for WAF/CAPTCHA signatures
                        response_lower = response.text.lower()
                        is_waf_blocked = (
                            "sgcaptcha" in response_lower or
                            ".well-known/sgcaptcha" in response_lower or
                            "captcha" in response_lower or
                            "cloudflare" in response_lower and "challenge" in response_lower or
                            "access denied" in response_lower or
                            "forbidden" in response_lower and "firewall" in response_lower
                        )
                        
                        if is_waf_blocked:
                            last_error = f"WAF/CAPTCHA blocked (HTTP {response.status_code})"
                            logger.error(f"WordPress callback blocked by WAF/CAPTCHA - stopping retries")
                            return {
                                "success": False,
                                "error": last_error,
                                "blocked_by_waf": True,
                                "attempts": attempt + 1
                            }
                
                # Success cases
                if response.status_code in (200, 202):
                    # 200 OK or 202 Accepted (async operation)
                    try:
                        data = response.json()
                        return {
                            "success": True,
                            "post_id": data.get("post_id"),
                            "title": data.get("title"),
                            "already_imported": data.get("already_imported", False),
                            "attempts": attempt + 1
                        }
                    except Exception:
                        # If JSON parsing fails but status is success, still return success
                        return {
                            "success": True,
                            "attempts": attempt + 1
                        }
                
                # Already imported (idempotent)
                elif response.status_code == 409 and "already" in response.text.lower():
                    # This is actually success - page already exists
                    return {
                        "success": True,
                        "already_imported": True,
                        "attempts": attempt + 1
                    }
                
                # Lock held by another process (concurrent import)
                elif response.status_code == 500 and "lock held" in response.text.lower():
                    # Another process is importing this item - treat as success
                    logger.info(f"WordPress import lock held - item being imported by another process")
                    return {
                        "success": True,
                        "already_imported": False,
                        "lock_held": True,
                        "attempts": attempt + 1
                    }
                
                # Retryable errors
                elif response.status_code in (429, 500, 502, 503, 504):
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(f"WordPress callback failed (attempt {attempt + 1}/{max_retries}): {last_error}")
                    
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        backoff = (2 ** attempt) + (time.time() % 1)  # 1s, 2s, 4s + jitter
                        await asyncio.sleep(backoff)
                        continue
                
                # Non-retryable errors
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"WordPress callback failed (non-retryable): {last_error}")
                    return {
                        "success": False,
                        "error": last_error,
                        "attempts": attempt + 1
                    }
        
        except httpx.TimeoutException as e:
            last_error = f"Timeout: {str(e)}"
            logger.warning(f"WordPress callback timeout (attempt {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                backoff = (2 ** attempt) + (time.time() % 1)
                await asyncio.sleep(backoff)
                continue
        
        except httpx.NetworkError as e:
            last_error = f"Network error: {str(e)}"
            logger.warning(f"WordPress callback network error (attempt {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                backoff = (2 ** attempt) + (time.time() % 1)
                await asyncio.sleep(backoff)
                continue
        
        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            logger.error(f"WordPress callback unexpected error: {last_error}")
            return {
                "success": False,
                "error": last_error,
                "attempts": attempt + 1
            }
    
    # All retries exhausted
    return {
        "success": False,
        "error": last_error or "All retries exhausted",
        "attempts": max_retries
    }


async def ping_wordpress(
    wordpress_rest_url: str,
    callback_secret: str,
    license_key: str,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Ping WordPress to test connection and authentication
    
    Args:
        wordpress_rest_url: WordPress REST API base URL
        callback_secret: Shared secret for HMAC signing
        license_key: License key for verification
        timeout: Request timeout in seconds (default: 10)
    
    Returns:
        Dict with success status and site info
    """
    endpoint = wordpress_rest_url.rstrip('/') + '/ping'
    
    payload = {"license_key": license_key}
    
    import json
    body = json.dumps(payload)
    
    timestamp, body_hash, signature = generate_hmac_signature(body, callback_secret)
    
    headers = {
        "Content-Type": "application/json",
        "X-Seogen-Timestamp": timestamp,
        "X-Seogen-Body-SHA256": body_hash,
        "X-Seogen-Signature": signature,
        "X-Seogen-Signature-Version": "1"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                content=body,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "site_url": data.get("site_url"),
                    "rest_base_url": data.get("rest_base_url"),
                    "license_valid": data.get("license_valid", False)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
