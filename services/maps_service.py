"""
Google Maps service — travel time estimation via Distance Matrix API.
"""

import logging
import os

import httpx

logger = logging.getLogger("axis.maps")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


async def get_travel_time(
    origin_lat: float, origin_lng: float, destination: str
) -> int | None:
    """Return estimated drive time in minutes from origin to destination.

    Returns None if the API key is missing, the request fails,
    or no route is found.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.debug("GOOGLE_MAPS_API_KEY not set — skipping travel time")
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                DISTANCE_MATRIX_URL,
                params={
                    "origins": f"{origin_lat},{origin_lng}",
                    "destinations": destination,
                    "mode": "driving",
                    "departure_time": "now",
                    "key": GOOGLE_MAPS_API_KEY,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            logger.debug("No route found to %s: %s", destination, element.get("status"))
            return None

        # duration_in_traffic preferred, falls back to duration
        seconds = (
            element.get("duration_in_traffic", {}).get("value")
            or element["duration"]["value"]
        )
        return max(1, seconds // 60)

    except Exception as e:
        logger.warning("Travel time request failed: %s", e)
        return None
