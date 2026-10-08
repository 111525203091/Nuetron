"""
JARVIS Web Skills — Search, Weather, News, Wikipedia
"""

import requests
import urllib.parse
import webbrowser
from typing import Optional
from core.config import WEATHER_API_KEY, WOLFRAM_APP_ID
from core.logger import log


class WebSkills:
    """Web-based information retrieval skills."""

    # ─── Web Search ───────────────────────────────────────────────────────────

    @staticmethod
    def search_web(query: str, open_browser: bool = False) -> str:
        """
        Perform a web search via DuckDuckGo Instant Answers API.
        Optionally open the browser for the full search.
        """
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_redirect": 1,
                "no_html": 1,
                "skip_disambig": 1
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            results = []

            # Abstract / summary
            if data.get("Abstract"):
                results.append(f"Summary: {data['Abstract']}")
                if data.get("AbstractURL"):
                    results.append(f"Source: {data['AbstractURL']}")

            # Answer
            if data.get("Answer"):
                results.append(f"Direct Answer: {data['Answer']}")

            # Definition
            if data.get("Definition"):
                results.append(f"Definition: {data['Definition']}")

            # Related topics
            if data.get("RelatedTopics"):
                results.append("\nRelated:")
                for topic in data["RelatedTopics"][:3]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append(f"  • {topic['Text'][:200]}")

            if not results:
                results.append(f"No instant answer found for '{query}'.")
                results.append(f"Search URL: https://www.google.com/search?q={urllib.parse.quote(query)}")

            if open_browser:
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
                results.append("Opened browser with search results.")

            return "\n".join(results)

        except Exception as e:
            log.error("Web search error: %s", str(e))
            if open_browser:
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return f"Search error: {str(e)}"

    @staticmethod
    def open_url(url: str) -> str:
        """Open a URL in the default browser."""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return f"Opened: {url}"
        except Exception as e:
            return f"Could not open URL: {str(e)}"

    # ─── Wikipedia ────────────────────────────────────────────────────────────

    @staticmethod
    def wikipedia_search(query: str, sentences: int = 3) -> str:
        """Search Wikipedia via official high-speed REST API (instant)."""
        try:
            q = urllib.parse.quote(query.strip().replace(" ", "_"))
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}"
            res = requests.get(url, timeout=3.5, headers={"User-Agent": "JARVIS-Assistant/2.0 (Windows NT 10.0; Win64; x64)"})
            if res.status_code == 200:
                data = res.json()
                title = data.get("title", query)
                extract = data.get("extract", "No summary available.")
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                return f"**{title}**\n\n{extract}\n\n*Reference:* {page_url}"
            else:
                return f"No Wikipedia entry found for '{query}'."
        except Exception as e:
            return f"Wikipedia lookup error: {str(e)}"

    # ─── Weather ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_weather(city: str = "London") -> str:
        """Fetch current weather for a city using OpenWeatherMap."""
        if not WEATHER_API_KEY:
            # Fallback: try wttr.in which needs no API key
            return WebSkills._get_weather_wttr(city)

        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": WEATHER_API_KEY,
                "units": "metric"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("cod") != 200:
                return f"Weather error: {data.get('message', 'Unknown error')}"

            weather = data["weather"][0]
            main = data["main"]
            wind = data.get("wind", {})

            return (
                f"Weather in {data['name']}, {data['sys']['country']}:\n"
                f"Condition: {weather['description'].capitalize()}\n"
                f"Temperature: {main['temp']:.1f}°C (Feels like: {main['feels_like']:.1f}°C)\n"
                f"Humidity: {main['humidity']}%\n"
                f"Wind: {wind.get('speed', 0):.1f} m/s\n"
                f"Min/Max: {main['temp_min']:.1f}°C / {main['temp_max']:.1f}°C"
            )
        except Exception as e:
            log.error("Weather error: %s", str(e))
            return WebSkills._get_weather_wttr(city)

    @staticmethod
    def _get_weather_wttr(city: str) -> str:
        """Fast weather lookup via Open-Meteo API (instant, free, no key needed)."""
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
            geo_res = requests.get(geo_url, timeout=3).json()
            if not geo_res.get("results"):
                return f"Unable to locate coordinates for '{city}'."
            loc = geo_res["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]
            name, country = loc.get("name", city), loc.get("country", "")

            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            w_res = requests.get(w_url, timeout=3).json()
            cw = w_res.get("current_weather", {})
            temp = cw.get("temperature", "?")
            wind = cw.get("windspeed", "?")
            code = cw.get("weathercode", 0)

            w_codes = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Foggy", 51: "Light drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow", 95: "Thunderstorm"}
            condition = w_codes.get(code, "Clear")

            return (
                f"Weather in {name}, {country}:\n"
                f"• Condition: {condition}\n"
                f"• Temperature: {temp}°C\n"
                f"• Wind Speed: {wind} km/h"
            )
        except Exception as e:
            return f"Weather service temporarily unavailable: {str(e)}"

    # ─── News ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_news(topic: str = "", count: int = 5) -> str:
        """Fetch latest news headlines using NewsAPI or RSS."""
        try:
            # Use HackerNews API as a free fallback
            if not topic or topic.lower() in ["tech", "technology", "hacker news"]:
                url = "https://hacker-news.firebaseio.com/v0/topstories.json"
                response = requests.get(url, timeout=4)
                story_ids = response.json()[:count]

                headlines = []
                for sid in story_ids:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                    story = requests.get(story_url, timeout=3).json()
                    if story:
                        headlines.append(f"• {story.get('title', 'N/A')}")
                        if story.get("url"):
                            headlines.append(f"  {story['url']}")

                return f"Top Hacker News Stories:\n" + "\n".join(headlines)
            else:
                # Use Google News RSS
                query = urllib.parse.quote(topic)
                url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
                response = requests.get(url, timeout=4)
                from xml.etree import ElementTree as ET
                root = ET.fromstring(response.content)
                items = root.findall(".//item")[:count]

                headlines = [f"News about '{topic}':"]
                for item in items:
                    title = item.findtext("title", "No title")
                    link = item.findtext("link", "")
                    headlines.append(f"• {title}")
                    if link:
                        headlines.append(f"  {link}")

                return "\n".join(headlines)

        except Exception as e:
            log.error("News error: %s", str(e))
            return f"Could not fetch news: {str(e)}"

    # ─── IP & Connectivity ────────────────────────────────────────────────────

    @staticmethod
    def get_public_ip() -> str:
        """Get the public IP address instantly."""
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=2.5)
            ip = response.json().get("ip", "Unknown")
            return f"Public IP Address: {ip}"
        except Exception as e:
            return f"IP lookup error: {str(e)}"
            return f"IP lookup error: {str(e)}"

    @staticmethod
    def check_internet() -> str:
        """Check internet connectivity."""
        try:
            requests.get("https://www.google.com", timeout=5)
            return "Internet connection: Online ✓"
        except Exception:
            return "Internet connection: Offline ✗"

    # ─── WolframAlpha ─────────────────────────────────────────────────────────

    @staticmethod
    def wolfram_query(query: str) -> str:
        """Query WolframAlpha for computational answers."""
        if not WOLFRAM_APP_ID:
            return "WolframAlpha App ID not configured. Add WOLFRAM_APP_ID to .env"
        try:
            import wolframalpha
            client = wolframalpha.Client(WOLFRAM_APP_ID)
            res = client.query(query)

            answers = []
            for pod in res.pods:
                if pod.title in ["Result", "Solution", "Exact result", "Decimal approximation"]:
                    for sub in pod.subpods:
                        if sub.plaintext:
                            answers.append(f"{pod.title}: {sub.plaintext}")

            return "\n".join(answers) if answers else "No computational result found."
        except Exception as e:
            return f"WolframAlpha error: {str(e)}"

    # ─── Location Detection & Setting ──────────────────────────────────────────

    _cached_location = None

    @classmethod
    def update_gps_location(cls, lat: float, lon: float) -> dict:
        """Update user's location via precise GPS/browser coordinates using reverse geocoding."""
        try:
            url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=en"
            r = requests.get(url, timeout=5)
            data = r.json()
            city = data.get("city") or data.get("locality") or data.get("principalSubdivision") or "Unknown City"
            region = data.get("principalSubdivision") or ""
            country = data.get("countryName") or ""
            postcode = data.get("postcode") or ""

            cls._cached_location = {
                "ok": True,
                "city": city,
                "region": region,
                "country": country,
                "lat": lat,
                "lon": lon,
                "postcode": postcode,
                "source": "Browser GPS / Device Sensor",
            }
            log.info("Location updated via GPS coordinates: %s, %s, %s", city, region, country)
            return cls._cached_location
        except Exception as e:
            log.error("GPS reverse geocoding failed: %s", str(e))
            return {"ok": False, "error": str(e)}

    @classmethod
    def set_custom_location(cls, place: str) -> str:
        """Manually set and persist the user's location to any city or region."""
        try:
            city, region, country, lat, lon, timezone = place, "", "", 0.0, 0.0, ""

            # 1. Primary: Nominatim OpenStreetMap (supports all city aliases, regions, languages)
            try:
                headers = {"User-Agent": "ULTRON-Assistant/2.0"}
                nom_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(place)}&format=json&limit=1"
                nom_res = requests.get(nom_url, headers=headers, timeout=4).json()
                if nom_res and len(nom_res) > 0:
                    item = nom_res[0]
                    display = item.get("display_name", place)
                    parts = [p.strip() for p in display.split(",")]
                    city = parts[0] if parts else place
                    country = parts[-1] if len(parts) > 1 else ""
                    region = parts[-2] if len(parts) > 2 else ""
                    lat = float(item.get("lat", 0))
                    lon = float(item.get("lon", 0))
            except Exception:
                pass

            # 2. Fallback: Open-Meteo geocoding
            if not lat and not lon:
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(place)}&count=1&language=en&format=json"
                geo_res = requests.get(geo_url, timeout=4).json()
                if geo_res.get("results"):
                    loc = geo_res["results"][0]
                    city = loc.get("name", place)
                    region = loc.get("admin1", "")
                    country = loc.get("country", "")
                    lat = float(loc.get("latitude", 0))
                    lon = float(loc.get("longitude", 0))
                    timezone = loc.get("timezone", "")

            if not lat and not lon:
                return f"Could not find coordinates for location '{place}', {OWNER_NAME}. Please check the spelling."

            cls._cached_location = {
                "ok": True,
                "city": city,
                "region": region,
                "country": country,
                "lat": lat,
                "lon": lon,
                "timezone": timezone or "Local",
                "source": "Manual User Configuration",
            }
            return (
                f"📍 Location successfully updated to **{city}**, {region} ({country})!\n"
                f"• Coordinates: {lat:.4f}°N, {lon:.4f}°E\n"
                f"All weather and local queries will now reflect this location."
            )
        except Exception as e:
            return f"Failed to set location: {str(e)}"

    @classmethod
    def get_location(cls) -> dict:
        """
        Get user's location using highest available precision:
        1. Browser GPS (if sent by client)
        2. Manually configured city
        3. IP Geolocation fallback
        """
        if cls._cached_location and cls._cached_location.get("ok"):
            return cls._cached_location

        try:
            r = requests.get("http://ip-api.com/json/?fields=status,message,country,regionName,city,lat,lon,timezone,isp,query", timeout=4)
            data = r.json()
            if data.get("status") == "success":
                cls._cached_location = {
                    "ok": True,
                    "ip": data.get("query", ""),
                    "city": data.get("city", ""),
                    "region": data.get("regionName", ""),
                    "country": data.get("country", ""),
                    "lat": data.get("lat", 0),
                    "lon": data.get("lon", 0),
                    "timezone": data.get("timezone", ""),
                    "isp": data.get("isp", ""),
                    "source": "IP Geolocation",
                }
                return cls._cached_location
            return {"ok": False, "error": data.get("message", "Unknown error")}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @classmethod
    def get_location_string(cls) -> str:
        """Return a formatted location string for the user."""
        loc = cls.get_location()
        if not loc.get("ok"):
            return f"Location unavailable: {loc.get('error', 'Unknown error')}"
        src = loc.get("source", "Detected")
        return (
            f"📍 Current Location ({src}):\n"
            f"  • City: {loc.get('city')}, {loc.get('region')}\n"
            f"  • Country: {loc.get('country')}\n"
            f"  • Coordinates: {loc.get('lat')}°N, {loc.get('lon')}°E\n"
            f"  • Source: {src}\n\n"
            f"💡 *Tip: To change this, say: 'set my location to [your city]'*"
        )

    @classmethod
    def get_local_weather(cls) -> str:
        """Get weather for the user's current detected location."""
        loc = cls.get_location()
        if not loc.get("ok"):
            return f"Could not auto-detect location: {loc.get('error')}"
        city = loc.get("city", "")
        if not city:
            return "Could not determine your city."
        result = cls.get_weather(city)
        return result

    # ─── Fetch URL Content ─────────────────────────────────────────────────────

    @staticmethod
    def fetch_url(url: str, max_chars: int = 3000) -> str:
        """
        Fetch plain text content from any URL.
        Strips HTML tags and returns clean readable text.
        """
        try:
            import urllib.request as _req
            import html
            import re as _re

            # Ensure URL has scheme
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            req = _req.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ULTRON/1.0",
                "Accept": "text/html,application/xhtml+xml,*/*",
            })
            with _req.urlopen(req, timeout=8) as response:
                raw = response.read().decode("utf-8", errors="ignore")

            # Strip HTML tags
            clean = _re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=_re.DOTALL | _re.IGNORECASE)
            clean = _re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=_re.DOTALL | _re.IGNORECASE)
            clean = _re.sub(r"<[^>]+>", " ", clean)
            clean = html.unescape(clean)
            clean = _re.sub(r"\s{2,}", " ", clean).strip()

            if len(clean) > max_chars:
                clean = clean[:max_chars] + f"\n\n...[truncated — {len(clean)} total chars]"

            return f"**Content from** `{url}`:\n\n{clean}"
        except Exception as e:
            return f"Could not fetch URL '{url}': {str(e)}"
