"""
YouTube service — fetches subscription videos, sends to Gemini for summarisation.

Uses YouTube Data API v3 for metadata + Gemini Flash-Lite for video content processing.
"""

import logging
import os

import httpx

from services.model_router import route

logger = logging.getLogger("axis.youtube")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

SUMMARISE_SYSTEM = """You are a video content analyst.
Summarise the YouTube video based on its title, description, and channel context.

Rules:
- One paragraph, max 80 words
- Lead with the key takeaway
- Note if it's a tutorial, news, entertainment, review, etc.
- Flag if it seems time-sensitive or actionable
"""


async def fetch_subscription_videos(
    access_token: str, max_results: int = 10
) -> list[dict]:
    """Fetch recent videos from a user's YouTube subscriptions via OAuth token."""
    async with httpx.AsyncClient(timeout=30) as client:
        # Get user's subscriptions
        resp = await client.get(
            f"{YOUTUBE_API_BASE}/subscriptions",
            params={
                "part": "snippet",
                "mine": "true",
                "maxResults": 20,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            logger.warning("YouTube subscriptions fetch failed: %s", resp.text[:200])
            return []

        subs = resp.json().get("items", [])
        channel_ids = [
            s["snippet"]["resourceId"]["channelId"]
            for s in subs
            if "resourceId" in s.get("snippet", {})
        ]

        if not channel_ids:
            return []

        # Get recent uploads from subscribed channels
        videos = []
        for channel_id in channel_ids[:10]:
            resp = await client.get(
                f"{YOUTUBE_API_BASE}/search",
                params={
                    "part": "snippet",
                    "channelId": channel_id,
                    "order": "date",
                    "type": "video",
                    "maxResults": 3,
                    "key": YOUTUBE_API_KEY,
                },
            )
            if resp.status_code == 200:
                for item in resp.json().get("items", []):
                    snippet = item.get("snippet", {})
                    videos.append({
                        "id": item["id"].get("videoId", ""),
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", ""),
                        "description": (snippet.get("description") or "")[:300],
                        "published_at": snippet.get("publishedAt", ""),
                        "url": f"https://youtube.com/watch?v={item['id'].get('videoId', '')}",
                    })

        # Sort by published date, return most recent
        videos.sort(key=lambda v: v["published_at"], reverse=True)
        return videos[:max_results]


async def fetch_trending_videos(region: str = "AU", max_results: int = 5) -> list[dict]:
    """Fetch trending videos for a region using API key (no OAuth needed)."""
    if not YOUTUBE_API_KEY:
        return []

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{YOUTUBE_API_BASE}/videos",
            params={
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": region,
                "maxResults": max_results,
                "key": YOUTUBE_API_KEY,
            },
        )
        if resp.status_code != 200:
            logger.warning("YouTube trending fetch failed: %s", resp.text[:200])
            return []

        return [
            {
                "id": item["id"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "description": (item["snippet"].get("description") or "")[:300],
                "published_at": item["snippet"]["publishedAt"],
                "views": item.get("statistics", {}).get("viewCount", "0"),
                "url": f"https://youtube.com/watch?v={item['id']}",
            }
            for item in resp.json().get("items", [])
        ]


async def summarise_video(video: dict) -> dict:
    """Summarise a video using Gemini Flash-Lite."""
    msg = (
        f"Title: {video['title']}\n"
        f"Channel: {video['channel']}\n"
        f"Description: {video['description']}\n"
        f"URL: {video['url']}"
    )

    result = await route(
        task_type="youtube_summary",
        system=SUMMARISE_SYSTEM,
        user_msg=msg,
    )

    return {
        **video,
        "summary": result["text"],
        "model": result["model"],
    }
