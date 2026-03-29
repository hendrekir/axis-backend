"""
News service — Google News + RSS aggregation with topic filtering.

Feeds into triage for relevance scoring before reaching the user.
"""

import logging
import os
from xml.etree import ElementTree

import httpx

logger = logging.getLogger("axis.news")

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-AU&gl=AU&ceid=AU:en"
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


async def fetch_google_news(query: str, max_results: int = 10) -> list[dict]:
    """Fetch news via Google News RSS (no API key needed)."""
    url = GOOGLE_NEWS_RSS.format(query=query.replace(" ", "+"))

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            logger.warning("Google News RSS fetch failed for '%s': %s", query, resp.status_code)
            return []

    try:
        root = ElementTree.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []

        articles = []
        for item in channel.findall("item")[:max_results]:
            articles.append({
                "source": "google_news",
                "title": item.findtext("title", ""),
                "link": item.findtext("link", ""),
                "published": item.findtext("pubDate", ""),
                "description": (item.findtext("description") or "")[:300],
            })
        return articles

    except ElementTree.ParseError:
        logger.warning("Failed to parse Google News RSS for '%s'", query)
        return []


async def fetch_hacker_news(max_results: int = 10) -> list[dict]:
    """Fetch top Hacker News stories (free API, no auth)."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{HN_API_BASE}/topstories.json")
        if resp.status_code != 200:
            return []

        story_ids = resp.json()[:max_results]

        stories = []
        for story_id in story_ids:
            resp = await client.get(f"{HN_API_BASE}/item/{story_id}.json")
            if resp.status_code == 200:
                data = resp.json()
                if data and data.get("type") == "story":
                    stories.append({
                        "source": "hacker_news",
                        "title": data.get("title", ""),
                        "link": data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "score": data.get("score", 0),
                        "num_comments": data.get("descendants", 0),
                        "by": data.get("by", ""),
                    })

        return stories


async def fetch_news_for_topics(topics: list[str], per_topic: int = 5) -> list[dict]:
    """Fetch news across multiple topics, combine and sort by recency."""
    all_articles = []
    for topic in topics:
        articles = await fetch_google_news(topic, max_results=per_topic)
        all_articles.extend(articles)

    return all_articles


async def fetch_rss_feed(feed_url: str, max_results: int = 10) -> list[dict]:
    """Fetch articles from a generic RSS feed."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(feed_url)
        if resp.status_code != 200:
            logger.warning("RSS fetch failed for %s: %s", feed_url, resp.status_code)
            return []

    try:
        root = ElementTree.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            # Try Atom format
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)
            return [
                {
                    "source": "rss",
                    "title": e.findtext("atom:title", "", ns),
                    "link": e.find("atom:link", ns).get("href", "") if e.find("atom:link", ns) is not None else "",
                    "published": e.findtext("atom:published", "", ns) or e.findtext("atom:updated", "", ns),
                    "description": (e.findtext("atom:summary", "", ns) or "")[:300],
                }
                for e in entries[:max_results]
            ]

        return [
            {
                "source": "rss",
                "title": item.findtext("title", ""),
                "link": item.findtext("link", ""),
                "published": item.findtext("pubDate", ""),
                "description": (item.findtext("description") or "")[:300],
            }
            for item in channel.findall("item")[:max_results]
        ]

    except ElementTree.ParseError:
        logger.warning("Failed to parse RSS from %s", feed_url)
        return []
