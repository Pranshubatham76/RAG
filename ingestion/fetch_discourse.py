"""
Fetch Discourse posts from API.

Purpose: Download 500+ posts from Discourse API
Input: None (uses DISCOURSE_URL, DISCOURSE_API_KEY from .env)
Output: Python list of raw JSON posts
Returns to: ingest_pipeline.py
"""
import os
import logging
import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configuration from environment
DISCOURSE_BASE_URL = os.getenv("DISCOURSE_BASE_URL")
DISCOURSE_API_KEY = os.getenv("DISCOURSE_API_KEY")
DISCOURSE_API_USERNAME = os.getenv("DISCOURSE_API_USERNAME")
DISCOURSE_CATEGORY = os.getenv("DISCOURSE_CATEGORY", "reading-club")
MIN_POSTS = int(os.getenv("DISCOURSE_MIN_POSTS", "500"))
RATE_LIMIT = float(os.getenv("DISCOURSE_RATE_LIMIT_PER_SECOND", "2"))
TIMEOUT = int(os.getenv("DISCOURSE_TIMEOUT_SECONDS", "30"))
MAX_RETRIES = int(os.getenv("DISCOURSE_MAX_RETRIES", "3"))

# Optional: Save raw data for debugging
BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "ingestion" / "sample_data"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def _get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Internal helper: Send GET request to Discourse API with retry logic.
    
    Args:
        endpoint: API endpoint (e.g., "/t/123.json")
        params: Query parameters
        
    Returns:
        JSON response as dict
        
    Raises:
        RuntimeError: If all retries fail
    """
    if not DISCOURSE_BASE_URL or not DISCOURSE_API_KEY:
        raise ValueError("DISCOURSE_BASE_URL and DISCOURSE_API_KEY must be set")
    
    headers = {
        "Api-Key": DISCOURSE_API_KEY,
        "Api-Username": DISCOURSE_API_USERNAME or "system",
    }
    
    url = f"{DISCOURSE_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    
    # Retry logic with exponential backoff
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                url=url,
                headers=headers,
                params=params,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                retry_after = int(response.headers.get("Retry-After", attempt * 2))
                logger.warning(f"Rate limited. Waiting {retry_after}s before retry {attempt}/{MAX_RETRIES}")
                time.sleep(retry_after)
                continue
            else:
                logger.warning(
                    f"Request failed with status {response.status_code}, "
                    f"retrying ({attempt}/{MAX_RETRIES})..."
                )
                
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout, retrying ({attempt}/{MAX_RETRIES})...")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error: {e}, retrying ({attempt}/{MAX_RETRIES})...")
        
        # Exponential backoff
        time.sleep(min(1 + attempt, 10))
    
    raise RuntimeError(f"Failed to fetch {endpoint} after {MAX_RETRIES} retries")


def fetch_discourse_posts(
    category: Optional[str] = None,
    category_slug: Optional[str] = None,
    min_posts: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch posts from Discourse API.
    
    Returns a flat list of posts with enriched metadata:
    [
        {
            "id": 123,
            "topic_id": 12,
            "content": "<p>Hello world...</p>",
            "created_at": "...",
            "url": "...",
            "title": "...",
            "slug": "...",
            ...
        },
        ...
    ]
    
    Args:
        category_slug: Category to fetch from (defaults to DISCOURSE_CATEGORY)
        min_posts: Minimum number of posts to fetch (defaults to MIN_POSTS)
        
    Returns:
        List of post dictionaries
    """
    # Support both 'category' and 'category_slug' for compatibility
    category_slug = category or category_slug or DISCOURSE_CATEGORY
    min_posts = min_posts or MIN_POSTS
    
    logger.info(f"Starting fetch: category={category_slug}, min_posts={min_posts}")
    
    collected_posts: List[Dict[str, Any]] = []
    seen_post_ids: set = set()
    page = 0
    
    while len(collected_posts) < min_posts:
        endpoint = f"/c/{category_slug}/l/latest.json"
        params = {"page": page}
        
        try:
            data = _get(endpoint, params=params)
            topic_list = data.get("topic_list", {}).get("topics", [])
            
            if not topic_list:
                logger.info("No more topics found, stopping")
                break
            
            # Fetch full details for each topic
            for topic_summary in topic_list:
                topic_id = topic_summary.get("id")
                if not topic_id:
                    continue
                
                try:
                    topic_json = _get(f"/t/{topic_id}.json")
                except Exception as e:
                    logger.exception(f"Error fetching topic {topic_id}: {e}")
                    continue
                
                posts = topic_json.get("post_stream", {}).get("posts", [])
                topic_title = topic_json.get("title", "")
                topic_slug = topic_json.get("slug", "")
                base_url = DISCOURSE_BASE_URL.rstrip('/')
                
                # Enrich each post with topic metadata
                for post in posts:
                    post_id = post.get("id")
                    if not post_id or str(post_id) in seen_post_ids:
                        continue
                    
                    seen_post_ids.add(str(post_id))
                    
                    # Build enriched post record
                    enriched_post = {
                        "id": post_id,
                        "topic_id": topic_id,
                        "post_number": post.get("post_number", 0),
                        "content": post.get("cooked") or post.get("raw") or "",
                        "created_at": post.get("created_at", ""),
                        "updated_at": post.get("updated_at", ""),
                        "username": post.get("username", ""),
                        "name": post.get("name", ""),
                        "title": topic_title,
                        "slug": topic_slug,
                        "url": f"{base_url}/t/{topic_slug}/{topic_id}/{post.get('post_number', 1)}",
                        # Keep raw post data for reference
                        "raw_post": post
                    }
                    
                    collected_posts.append(enriched_post)
                    
                    if len(collected_posts) >= min_posts:
                        break
                
                if len(collected_posts) >= min_posts:
                    break
            
            page += 1
            
            # Rate limiting
            time.sleep(1.0 / RATE_LIMIT)
            
        except Exception as e:
            logger.exception(f"Error fetching page {page}: {e}")
            break
    
    # Optional: Save raw data for debugging
    if collected_posts:
        out_file = SAMPLE_DIR / f"discourse_raw_{int(time.time())}.json"
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(collected_posts, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved raw data to {out_file}")
        except Exception as e:
            logger.warning(f"Failed to save raw data: {e}")
    
    logger.info(
        f"Fetched {len(collected_posts)} posts from {category_slug} "
        f"(target was {min_posts})"
    )
    
    return collected_posts


# Alias for backward compatibility
fetch_topics = fetch_discourse_posts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    posts = fetch_discourse_posts()
    print(f"Fetched {len(posts)} posts")
