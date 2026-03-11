#!/usr/bin/env python3
"""
RAM Tool: Geo-location & Maps
Search Google Maps, get directions, find places.
"""

import subprocess
import json
import urllib.parse
from typing import Optional


def open_google_maps(query: str) -> dict:
    """Open Google Maps in browser with a query"""
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/maps/search/{encoded}"
    try:
        # Try to open in browser
        result = subprocess.run(
            ["xdg-open", url],
            capture_output=True, text=True, timeout=5
        )
        return {"success": True, "url": url, "query": query}
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


def get_directions(origin: str, destination: str, mode: str = "driving") -> dict:
    """
    Get directions URL and open in browser.
    mode: driving | walking | bicycling | transit
    """
    modes = {"driving": "driving", "walking": "walking",
              "bicycling": "bicycling", "transit": "transit"}
    travel_mode = modes.get(mode, "driving")

    origin_enc = urllib.parse.quote(origin)
    dest_enc = urllib.parse.quote(destination)
    url = (f"https://www.google.com/maps/dir/{origin_enc}/{dest_enc}"
           f"/?travelmode={travel_mode}")

    try:
        subprocess.run(["xdg-open", url], capture_output=True, timeout=5)
        return {
            "success": True,
            "url": url,
            "origin": origin,
            "destination": destination,
            "mode": travel_mode
        }
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


def get_current_location() -> dict:
    """Try to get approximate location via IP geolocation"""
    try:
        import urllib.request
        with urllib.request.urlopen("https://ipinfo.io/json", timeout=5) as resp:
            data = json.loads(resp.read())
        return {
            "success": True,
            "ip": data.get("ip"),
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country"),
            "coordinates": data.get("loc"),
            "timezone": data.get("timezone"),
            "org": data.get("org"),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_nearby(place_type: str, location: Optional[str] = None) -> dict:
    """Search for nearby places on Google Maps"""
    if not location:
        loc_info = get_current_location()
        location = loc_info.get("city", "") + " " + loc_info.get("region", "")

    query = f"{place_type} near {location.strip()}"
    return open_google_maps(query)


if __name__ == "__main__":
    loc = get_current_location()
    print(f"Location: {loc.get('city')}, {loc.get('region')}, {loc.get('country')}")
    print(f"Coordinates: {loc.get('coordinates')}")
