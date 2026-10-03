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
