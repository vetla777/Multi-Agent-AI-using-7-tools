import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from tools import (
    get_weather,
    get_forecast,
    get_news,
    web_search,
    scrape_url,
    search_wikipedia,
    get_city_places,
    get_current_time,
    calculate
)

load_dotenv()

# ============================================================
# 🧠 MODEL SETUP - GEMINI (3.5 Flash Lite — cheap, fast, low token)
# ============================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# thinking_budget is NOT supported on gemini-3.5-flash-lite or gemini-3.6-flash
primary_llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=GEMINI_API_KEY,
)

fallback_llm_1 = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    google_api_key=GEMINI_API_KEY,
)

fallback_llm_2 = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    google_api_key=GEMINI_API_KEY,
)

llm = primary_llm.with_fallbacks([fallback_llm_1, fallback_llm_2])


# ============================================================
# 🛡️ MIDDLEWARE: HUMAN APPROVAL & AUDIT LOGGING
# ============================================================
@wrap_tool_call
def human_approval_middleware(request, handler):
    """Ask for human confirmation in the terminal before executing a tool."""
    tool_name = request.tool_call["name"]
    tool_args = request.tool_call.get("args", {})
    
    print(f"\n[bold yellow]⚠️  Tool Call Request:[/bold yellow] [cyan]{tool_name}[/cyan]")
    print(f"   [dim]Arguments: {tool_args}[/dim]")
    confirm = input("   👉 Approve this tool call? (yes/no): ").strip().lower()

    if confirm not in ("yes", "y"):
        print("   [red]✖ Tool call denied by user.[/red]\n")
        return ToolMessage(
            content="Tool execution was denied by the human operator.",
            tool_call_id=request.tool_call["id"]
        )

    print("   [green]✔ Tool call approved.[/green]\n")
    return handler(request)


# ============================================================
# 🏙️ CITY & GENERAL ASSISTANT AGENT
# ============================================================
CITY_SYSTEM_PROMPT = """You are a fast, concise, and helpful City & Intelligence Assistant.
You have access to specialized tools for weather, news, places, Wikipedia, time, calculations, and web search.

Speed & Behavior Rules:
- Execute the SINGLE most relevant tool immediately without hesitation.
- Keep final answers direct, clear, and well-formatted with markdown. Do not repeat raw data unnecessarily.
"""

def build_city_agent(enable_human_approval: bool = False):
    """Builds an interactive City Agent equipped with weather, news, places, wiki, math & web tools."""
    tools = [
        get_weather,
        get_forecast,
        get_news,
        get_city_places,
        search_wikipedia,
        get_current_time,
        calculate,
        web_search
    ]
    
    middleware = [human_approval_middleware] if enable_human_approval else []
    
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=CITY_SYSTEM_PROMPT,
        middleware=middleware
    )


# ============================================================
# 🔍 1st AGENT - SEARCH AGENT
# ============================================================
def build_search_agent():
    """Gathers recent and reliable web search results on any topic."""
    return create_agent(
        model=llm,
        tools=[web_search, search_wikipedia]
    )


# ============================================================
# 📄 2nd AGENT - READER / SCRAPER AGENT
# ============================================================
def build_reader_agent():
    """Extracts and parses deep content from candidate URLs."""
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )


# ============================================================
# 📰 3rd AGENT - NEWS & INTELLIGENCE AGENT
# ============================================================
def build_news_agent():
    """Specialized agent for city news and real-time updates."""
    return create_agent(
        model=llm,
        tools=[get_news, web_search, scrape_url],
        system_prompt="You are a real-time news journalist agent. Provide concise, factual, and verified news digests."
    )


# ============================================================
# ✍️ WRITER CHAIN
# ============================================================
writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert research writer. "
        "Write clear, structured, and insightful reports."
    ),
    (
        "human",
        """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Executive Summary
- Key Findings (minimum 3 well-explained points)
- In-Depth Analysis
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual, and professional."""
    ),
])

writer_chain = (
    writer_prompt
    | llm
    | StrOutputParser()
)


# ============================================================
# 🧐 CRITIC CHAIN
# ============================================================
critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a sharp and constructive research critic. "
        "Be honest and specific."
    ),
    (
        "human",
        """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""
    ),
])

critic_chain = (
    critic_prompt
    | llm
    | StrOutputParser()
)
