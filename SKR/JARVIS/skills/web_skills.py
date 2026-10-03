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
    def wikipedia_search(query: str, sentences: int = 5) -> str:
        """Search Wikipedia and return a summary."""
        try:
            import wikipedia
            wikipedia.set_lang("en")

            try:
                summary = wikipedia.summary(query, sentences=sentences, auto_suggest=True)
                page = wikipedia.page(query, auto_suggest=True)
                return f"Wikipedia: {page.title}\n\n{summary}\n\nURL: {page.url}"
            except wikipedia.exceptions.DisambiguationError as e:
                # Return first suggestion
                options = e.options[:5]
                return f"Ambiguous search. Did you mean one of these?\n" + "\n".join(f"  • {o}" for o in options)
            except wikipedia.exceptions.PageError:
                return f"No Wikipedia page found for '{query}'."

        except ImportError:
            return "Wikipedia module not installed. Run: pip install wikipedia"
        except Exception as e:
            log.error("Wikipedia error: %s", str(e))
            return f"Wikipedia error: {str(e)}"

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
        """Fallback weather from wttr.in (no API key needed)."""
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=4"
            response = requests.get(url, timeout=10, headers={"User-Agent": "JARVIS/1.0"})
            return f"Weather for {city}:\n{response.text.strip()}"
        except Exception as e:
            return f"Could not fetch weather: {str(e)}"

    # ─── News ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_news(topic: str = "", count: int = 5) -> str:
        """Fetch latest news headlines using NewsAPI or RSS."""
        try:
            # Use HackerNews API as a free fallback
            if not topic or topic.lower() in ["tech", "technology", "hacker news"]:
                url = "https://hacker-news.firebaseio.com/v0/topstories.json"
                response = requests.get(url, timeout=10)
                story_ids = response.json()[:count]

                headlines = []
                for sid in story_ids:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                    story = requests.get(story_url, timeout=5).json()
                    if story:
                        headlines.append(f"• {story.get('title', 'N/A')}")
                        if story.get("url"):
                            headlines.append(f"  {story['url']}")

                return f"Top Hacker News Stories:\n" + "\n".join(headlines)
            else:
                # Use Google News RSS
                query = urllib.parse.quote(topic)
                url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
                response = requests.get(url, timeout=10)
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
        """Get the public IP address."""
        try:
            response = requests.get("https://api.ipify.org?format=json", timeout=5)
            ip = response.json().get("ip", "Unknown")
            # Get geo info
            geo = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5).json()
            return (
                f"Public IP: {ip}\n"
                f"Location: {geo.get('city', '?')}, {geo.get('region', '?')}, {geo.get('country_name', '?')}\n"
                f"ISP: {geo.get('org', '?')}"
            )
        except Exception as e:
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
