"""
Weather service — fetches current weather via OpenWeather API.

Falls back gracefully if OPENWEATHER_API_KEY is not set.
Free tier: openweathermap.org/api
"""

import logging
import os

import httpx

logger = logging.getLogger("axis.weather")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


async def get_weather(city_name: str) -> dict | None:
    """Get current weather for a city. Returns None if API key not set or on error.

    Returns: { temp_c, condition, rain_chance, description }
    """
    if not OPENWEATHER_API_KEY:
        return None

    if not city_name or len(city_name.strip()) < 2:
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Geocode city name to coordinates
            geo_resp = await client.get(GEO_URL, params={
                "q": city_name,
                "limit": 1,
                "appid": OPENWEATHER_API_KEY,
            })
            if geo_resp.status_code != 200:
                logger.warning("Geocoding failed for '%s': %s", city_name, geo_resp.status_code)
                return None

            locations = geo_resp.json()
            if not locations:
                logger.debug("No geocoding result for '%s'", city_name)
                return None

            lat = locations[0]["lat"]
            lon = locations[0]["lon"]

            # Fetch current weather
            weather_resp = await client.get(WEATHER_URL, params={
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            })
            if weather_resp.status_code != 200:
                logger.warning("Weather API failed for '%s': %s", city_name, weather_resp.status_code)
                return None

            data = weather_resp.json()
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            rain = data.get("rain", {})

            return {
                "temp_c": round(main.get("temp", 0)),
                "condition": weather.get("main", "Unknown"),
                "description": weather.get("description", ""),
                "rain_chance": rain.get("1h", 0) > 0,
                "city": city_name,
            }

    except Exception as e:
        logger.warning("Weather fetch failed for '%s': %s", city_name, e)
        return None
