import os
import datetime
import math
import ast
import operator
import requests
import re

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None

from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

load_dotenv()

# ============================================================
# TAVILY CLIENT INITIALIZATION
# ============================================================
tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None


# ============================================================
# 🌦️ WEATHER TOOLS
# ============================================================
@tool
def get_weather(city: str) -> str:
    """Get current weather conditions (temperature, humidity, description, wind) for a given city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    # Try OpenWeatherMap first if API key is provided
    if api_key and len(api_key.strip()) > 5:
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key.strip()}&units=metric"
            response = requests.get(url, timeout=3.5)
            data = response.json()
            
            if str(data.get("cod")) == "200":
                temp = data["main"]["temp"]
                feels_like = data["main"].get("feels_like", temp)
                humidity = data["main"].get("humidity", "N/A")
                desc = data["weather"][0]["description"]
                wind_speed = data.get("wind", {}).get("speed", "N/A")
                country = data.get("sys", {}).get("country", "")
                
                return (
                    f"Weather in {city.title()} ({country}):\n"
                    f"- Condition: {desc.capitalize()}\n"
                    f"- Temperature: {temp}°C (Feels like {feels_like}°C)\n"
                    f"- Humidity: {humidity}%\n"
                    f"- Wind Speed: {wind_speed} m/s"
                )
        except Exception:
            pass  # Fallback below
            
    # Fallback using open weather API (wttr.in)
    try:
        url = f"https://wttr.in/{requests.utils.quote(city)}?format=j1"
        resp = requests.get(url, timeout=8, headers={"User-Agent": "curl/7.68.0"})
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current_condition", [{}])[0]
            temp_c = current.get("temp_C", "N/A")
            feels_like = current.get("FeelsLikeC", temp_c)
            desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
            humidity = current.get("humidity", "N/A")
            wind = current.get("windspeedKmph", "N/A")
            
            return (
                f"Weather in {city.title()}:\n"
                f"- Condition: {desc}\n"
                f"- Temperature: {temp_c}°C (Feels like {feels_like}°C)\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind: {wind} km/h"
            )
    except Exception as e:
        return f"Could not fetch weather for {city}: {str(e)}"

    return f"Unable to fetch weather for {city}. Please check the city name or API keys."


@tool
def get_forecast(city: str) -> str:
    """Get upcoming multi-day weather forecast for a city."""
    try:
        url = f"https://wttr.in/{requests.utils.quote(city)}?format=j1"
        resp = requests.get(url, timeout=8, headers={"User-Agent": "curl/7.68.0"})
        if resp.status_code == 200:
            data = resp.json()
            weather_days = data.get("weather", [])[:3]
            out = [f"3-Day Forecast for {city.title()}:"]
            for day in weather_days:
                date = day.get("date", "N/A")
                max_t = day.get("maxtempC", "N/A")
                min_t = day.get("mintempC", "N/A")
                hourly = day.get("hourly", [{}])
                desc = hourly[len(hourly)//2].get("weatherDesc", [{}])[0].get("value", "Clear")
                out.append(f"• {date}: {desc} | Min: {min_t}°C, Max: {max_t}°C")
            return "\n".join(out)
    except Exception as e:
        return f"Could not retrieve forecast for {city}: {str(e)}"
    return f"Unable to fetch forecast for {city}."


# ============================================================
# 📰 NEWS TOOL (TAVILY)
# ============================================================
@tool
def get_news(city: str) -> str:
    """Get latest top news headlines and summary about a specific city or region."""
    if not tavily:
        return "TAVILY_API_KEY is not configured in .env."
    try:
        response = tavily.search(
            query=f"latest news headlines {city}",
            search_depth="basic",
            max_results=4
        )
        results = response.get("results", [])
        if not results:
            return f"No news found for {city}."
        
        news_list = []
        for r in results:
            title = r.get("title", "No title")
            url = r.get("url", "")
            snippet = r.get("content", "")[:200]
            news_list.append(f"📰 {title}\n🔗 {url}\n📝 {snippet}...")
        
        return f"Latest news for {city.title()}:\n\n" + "\n\n".join(news_list)
    except Exception as e:
        return f"Error retrieving news for {city}: {str(e)}"


# ============================================================
# 🔍 WEB SEARCH TOOL
# ============================================================
@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on any topic. Returns Titles, URLs, and snippets."""
    if not tavily:
        return "TAVILY_API_KEY is not configured in .env."
    try:
        results = tavily.search(query=query, max_results=5)
        out = []
        for r in results.get("results", []):
            out.append(
                f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
            )
        return "\n----\n".join(out) if out else "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"


# ============================================================
# 📄 WEB SCRAPER / DEEP READER TOOL
# ============================================================
@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean, readable text content from a given web page URL."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        if HAS_BS4 and BeautifulSoup:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
        else:
            # Simple regex fallback if bs4 is not available
            cleaned = re.sub(r'<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>', '', resp.text, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
            text = ' '.join(cleaned.split())
        return text[:3500] if text else "Page contained no readable text."
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"


# ============================================================
# 📚 WIKIPEDIA / KNOWLEDGE TOOL
# ============================================================
@tool
def search_wikipedia(topic: str) -> str:
    """Search Wikipedia for encyclopedic summaries, history, or factual information about a person, place, or concept."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}"
        resp = requests.get(url, timeout=8, headers={"User-Agent": "ResearchAssistant/1.0"})
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", topic)
            extract = data.get("extract", "No summary available.")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            return f"**{title} (Wikipedia)**:\n{extract}\n\nRead more: {page_url}"
        return f"No Wikipedia article found for '{topic}'."
    except Exception as e:
        return f"Error fetching Wikipedia data: {str(e)}"


# ============================================================
# 🏛️ CITY ATTRACTIONS & PLACES TOOL
# ============================================================
@tool
def get_city_places(city: str) -> str:
    """Find top tourist attractions, landmarks, and things to do in a city."""
    if not tavily:
        return f"Searching places requires TAVILY_API_KEY."
    try:
        response = tavily.search(
            query=f"top tourist attractions things to do places to visit in {city}",
            search_depth="basic",
            max_results=4
        )
        results = response.get("results", [])
        if not results:
            return f"No attractions found for {city}."
        
        places = []
        for r in results:
            places.append(f"📍 {r.get('title')}\n{r.get('content')[:220]}...\n🔗 {r.get('url')}")
        return f"Top Places & Attractions in {city.title()}:\n\n" + "\n\n".join(places)
    except Exception as e:
        return f"Error finding places in {city}: {str(e)}"


# ============================================================
# 🕒 TIME & DATE TOOL
# ============================================================
@tool
def get_current_time(timezone_or_city: str = "UTC") -> str:
    """Get current date and time. Accepts optional city or timezone name."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return (
        f"Current UTC Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"Day of Week: {now_utc.strftime('%A')}"
    )


# ============================================================
# 🧮 MATH CALCULATOR TOOL
# ============================================================
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}

def _eval_expr(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_expr(node.left)
        right = _eval_expr(node.right)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported operator: {op_type}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_expr(node.operand)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported operator: {op_type}")
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        func_name = node.func.id
        args = [_eval_expr(a) for a in node.args]
        math_funcs = {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan, "log": math.log, "abs": abs}
        if func_name in math_funcs:
            return math_funcs[func_name](*args)
        raise ValueError(f"Unsupported function: {func_name}")
    raise ValueError(f"Unsupported expression: {type(node)}")

@tool
def calculate(expression: str) -> str:
    """Safely calculate mathematical expressions (e.g., '15 * 240 / 3.5', 'sqrt(144) + 2^5')."""
    try:
        clean_expr = expression.replace("^", "**")
        tree = ast.parse(clean_expr, mode="eval")
        result = _eval_expr(tree.body)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculation error for '{expression}': {str(e)}"
