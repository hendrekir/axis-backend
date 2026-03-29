"""
Reddit service — fetches posts from subscribed communities.

Uses Reddit's OAuth API. Community preferences learned via apprentice filter.
"""

import logging
import os

import httpx

logger = logging.getLogger("axis.reddit")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = "Axis/1.0"
REDDIT_API_BASE = "https://oauth.reddit.com"


async def _get_app_token() -> str | None:
    """Get a Reddit application-only OAuth token."""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": REDDIT_USER_AGENT},
        )
        if resp.status_code != 200:
            logger.warning("Reddit token fetch failed: %s", resp.text[:200])
            return None

        return resp.json().get("access_token")


async def fetch_subreddit_posts(
    subreddit: str, sort: str = "hot", limit: int = 5
) -> list[dict]:
    """Fetch top posts from a subreddit."""
    token = await _get_app_token()
    if not token:
        return []

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{REDDIT_API_BASE}/r/{subreddit}/{sort}",
            params={"limit": limit},
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": REDDIT_USER_AGENT,
            },
        )
        if resp.status_code != 200:
            logger.warning("Reddit fetch for r/%s failed: %s", subreddit, resp.text[:200])
            return []

        posts = resp.json().get("data", {}).get("children", [])
        return [
            {
                "id": p["data"]["id"],
                "subreddit": subreddit,
                "title": p["data"].get("title", ""),
                "score": p["data"].get("score", 0),
                "num_comments": p["data"].get("num_comments", 0),
                "url": f"https://reddit.com{p['data'].get('permalink', '')}",
                "selftext": (p["data"].get("selftext") or "")[:300],
                "is_self": p["data"].get("is_self", False),
                "created_utc": p["data"].get("created_utc", 0),
            }
            for p in posts
            if p.get("kind") == "t3"
        ]


async def fetch_multiple_subreddits(
    subreddits: list[str], sort: str = "hot", per_sub: int = 3
) -> list[dict]:
    """Fetch posts from multiple subreddits, sorted by score."""
    all_posts = []
    for sub in subreddits:
        posts = await fetch_subreddit_posts(sub, sort=sort, limit=per_sub)
        all_posts.extend(posts)

    all_posts.sort(key=lambda p: p["score"], reverse=True)
    return all_posts


async def search_reddit(query: str, sort: str = "relevance", limit: int = 5) -> list[dict]:
    """Search Reddit for posts matching a query."""
    token = await _get_app_token()
    if not token:
        return []

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{REDDIT_API_BASE}/search",
            params={"q": query, "sort": sort, "limit": limit, "type": "link"},
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": REDDIT_USER_AGENT,
            },
        )
        if resp.status_code != 200:
            return []

        posts = resp.json().get("data", {}).get("children", [])
        return [
            {
                "id": p["data"]["id"],
                "subreddit": p["data"].get("subreddit", ""),
                "title": p["data"].get("title", ""),
                "score": p["data"].get("score", 0),
                "num_comments": p["data"].get("num_comments", 0),
                "url": f"https://reddit.com{p['data'].get('permalink', '')}",
                "selftext": (p["data"].get("selftext") or "")[:300],
            }
            for p in posts
            if p.get("kind") == "t3"
        ]
