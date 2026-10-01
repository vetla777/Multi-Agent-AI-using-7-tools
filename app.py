import streamlit as st
import time
import os
import datetime
from dotenv import load_dotenv

# LangChain Agents & Tools
from agents import (
    build_city_agent,
    build_search_agent,
    build_reader_agent,
    writer_chain,
    critic_chain
)
from tools import (
    get_weather,
    get_forecast,
    get_news,
    get_city_places,
    search_wikipedia,
    calculate,
    get_current_time,
    web_search
)

load_dotenv()

# ==============================================================================
# 🌟 STREAMLIT PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Nexus AI · Multi-Agent & City Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# 🎨 ULTRA-PREMIUM MODERN THEME & CSS
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@700;800&display=swap');

/* Global Font & Theme */
html, body, [class*="css"], .stMarkdown, p, div {
    font-family: 'Outfit', sans-serif;
    color: #e4e7eb;
}

.stApp {
    background-color: #07090e;
    background-image:
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(244, 63, 94, 0.10) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(14, 165, 233, 0.08) 0px, transparent 60%);
    background-attachment: fixed;
}

/* Hide Streamlit default elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3.5rem;
    max-width: 1320px;
}

/* ── Hero Banner ── */
.nexus-hero {
    text-align: center;
    padding: 1.8rem 1rem 1.4rem;
    margin-bottom: 1.5rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
}

.nexus-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 25%; right: 25%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.8), rgba(244, 63, 94, 0.8), transparent);
}

.nexus-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.2);
    padding: 0.3rem 0.9rem;
    border-radius: 9999px;
    margin-bottom: 0.7rem;
}

.nexus-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.2rem, 4vw, 3.4rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #ffffff;
    margin: 0 0 0.4rem;
    line-height: 1.1;
}

.nexus-title span {
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #f43f5e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.nexus-desc {
    font-size: 0.95rem;
    color: #94a3b8;
    max-width: 640px;
    margin: 0 auto;
    line-height: 1.5;
}

/* ── Glass Cards ── */
.glass-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, border-color 0.2s;
}
.glass-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
}

.card-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #f8fafc;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.8rem;
}

/* ── Tool Pill Tag ── */
.tool-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #a5b4fc;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}

/* ── Pipeline Steps ── */
.step-node {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    position: relative;
    transition: all 0.25s ease;
}
.step-node.active {
    background: rgba(56, 189, 248, 0.08);
    border-color: rgba(56, 189, 248, 0.5);
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.15);
}
.step-node.done {
    background: rgba(16, 185, 129, 0.08);
    border-color: rgba(16, 185, 129, 0.4);
}
.step-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.step-name {
    font-weight: 600;
    font-size: 0.92rem;
    color: #f1f5f9;
}
.step-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
}
.status-wait { color: #64748b; }
.status-run  { color: #38bdf8; }
.status-done { color: #10b981; }

/* ── Chat Messages ── */
.chat-msg-user {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.15));
    border: 1px solid rgba(168, 85, 247, 0.3);
    border-radius: 14px 14px 2px 14px;
    padding: 0.9rem 1.2rem;
    margin: 0.6rem 0;
    margin-left: 20%;
    color: #f1f5f9;
}
.chat-msg-bot {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px 14px 14px 2px;
    padding: 1.1rem 1.3rem;
    margin: 0.6rem 0;
    margin-right: 15%;
    color: #e2e8f0;
    line-height: 1.6;
}

/* ── Custom Streamlit Controls ── */
.stButton > button {
    background: linear-gradient(135deg, #38bdf8, #818cf8) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Outfit', sans-serif !important;
    transition: all 0.2s !important;
}
.stSlider > div > div {
    color: #38bdf8 !important;
}
.stProgress > div > div > div > div {
    background-color: #38bdf8 !important;
}

/* Research pipeline area */
.pipeline-area {
    background: rgba(30, 41, 59, 0.3);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.2rem;
    margin-top: 1rem;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    color: #94a3b8;
    padding: 0.5rem 1rem;
    border-radius: 8px;
}
.stTabs [aria-selected="true"] {
    color: #38bdf8 !important;
    background: rgba(56, 189, 248, 0.08);
}

/* Quick prompt chips */
.chip-btn {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    margin: 0.2rem;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    font-size: 0.8rem;
    color: #cbd5e1;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 🧭 SIDEBAR STATUS & CONTROLS
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚡ **Nexus AI System**")
    st.caption("Multi-Agent Architecture & Tool Suite")

    st.markdown("---")
    st.markdown("#### 🛠️ **Active Tools**")
    tools_list = [
        ("🌦️ Live Weather", "OpenWeather / wttr.in"),
        ("📅 3-Day Forecast", "Multi-day predictive"),
        ("📰 Tavily News", "Live regional news"),
        ("🏛️ City Places", "Attractions & Landmarks"),
        ("📚 Wikipedia", "Direct Wiki knowledge"),
        ("🧮 Math Engine", "Safe AST Evaluator"),
        ("🔍 Web Search", "Tavily Multi-source"),
        ("📄 Deep Scraper", "DOM / Text extractor"),
    ]
    for name, desc in tools_list:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.35rem 0;font-size:0.83rem;">
            <span style="font-weight:500;color:#f1f5f9;">{name}</span>
            <span style="color:#64748b;font-size:0.75rem;">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🤖 **LLM Engine**")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    st.markdown(f"`{model_name}` (Google Gemini)")

    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_tavily = bool(os.getenv("TAVILY_API_KEY"))
    has_openweather = bool(os.getenv("OPENWEATHER_API_KEY"))

    st.markdown(f"• **Gemini Key**: {'🟢 Connected' if has_gemini else '🔴 Missing'}")
    st.markdown(f"• **Tavily Key**: {'🟢 Connected' if has_tavily else '🟡 Fallback'}")
    st.markdown(f"• **Weather Key**: {'🟢 Connected' if has_openweather else '🟢 Ready (wttr fallback)'}")

    if st.button("🧹 Clear Chat / Reset State", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pipeline_results = {}
        st.session_state.pipeline_running = False
        st.session_state.pipeline_done = False
        st.rerun()


# ==============================================================================
# 🚀 HERO HEADER
# ==============================================================================
st.markdown("""
<div class="nexus-hero">
    <div class="nexus-badge">⚡ MULTI-AGENT AI ECOSYSTEM</div>
    <h1 class="nexus-title">City Intelligence & <span>Deep Research</span></h1>
    <p class="nexus-desc">
        Interact with autonomous multi-tool agents for real-time weather, breaking city news,
        travel insights, calculations, or launch a full 4-agent autonomous deep research pipeline.
    </p>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 🗂️ MAIN NAVIGATION TABS
# ==============================================================================
tab_assistant, tab_research, tab_tools = st.tabs([
    "🏙️ City & Multi-Tool Assistant",
    "🔬 Deep Research Pipeline",
    "⚡ Direct Tool Playground"
])


def extract_text(content):
    """Safely extract plain text string from str or list of Content parts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif hasattr(item, "text"):
                parts.append(getattr(item, "text", ""))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


# ==============================================================================
# 🏙️ TAB 1: INTERACTIVE CITY & MULTI-TOOL AGENT
# ==============================================================================
with tab_assistant:
    st.markdown("#### 💬 **Chat with City & Multi-Tool Agent**")
    st.caption("Ask anything: city weather, live news, travel attractions, math calculations, Wikipedia facts, or general web inquiries.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "👋 Hello! I'm your **City & Intelligence Assistant**. I can check live weather, find breaking news, discover top places, calculate formulas, and look up facts. What would you like to explore today?"}
        ]

    # Quick Suggestion Chips
    col_chip1, col_chip2, col_chip3, col_chip4 = st.columns(4)
    with col_chip1:
        if st.button("🌦️ Weather in Mumbai", use_container_width=True):
            st.session_state.suggested_prompt = "What is the current weather and 3-day forecast for Mumbai?"
    with col_chip2:
        if st.button("📰 Latest News in London", use_container_width=True):
            st.session_state.suggested_prompt = "Get me the latest breaking news in London."
    with col_chip3:
        if st.button("📍 Places to visit in Tokyo", use_container_width=True):
            st.session_state.suggested_prompt = "What are the top attractions and places to visit in Tokyo?"
    with col_chip4:
        if st.button("🧮 Math: sqrt(144) * 25 + 50", use_container_width=True):
            st.session_state.suggested_prompt = "Calculate sqrt(144) * 25 + 50"

    # Display Chat History
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-msg-user"><b>You:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-msg-bot"><b>🤖 Assistant:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

    # Chat Input Box
    default_text = st.session_state.pop("suggested_prompt", "")
    user_chat_input = st.chat_input("Ask about weather, news, places, math, or web search...") or default_text

    if user_chat_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_chat_input})

        # Invoke City Agent
        with st.spinner("🤖 Agent is analyzing query & invoking tools..."):
            try:
                city_agent = build_city_agent(enable_human_approval=False)
                # Pass recent conversation context (last 4 turns for speed)
                formatted_messages = []
                for m in st.session_state.chat_history[-4:]:
                    formatted_messages.append({"role": m["role"], "content": m["content"]})

                response = city_agent.invoke({"messages": formatted_messages})
                raw_reply = response["messages"][-1].content
                bot_reply = extract_text(raw_reply)
                st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"⚠️ An error occurred while running the agent: {str(e)}"
                })
        st.rerun()


# ==============================================================================
# 🔬 TAB 2: MULTI-AGENT DEEP RESEARCH PIPELINE
# ==============================================================================
with tab_research:
    col_req, col_pipe = st.columns([5, 4])

    if "pipeline_results" not in st.session_state:
        st.session_state.pipeline_results = {}
    if "pipeline_running" not in st.session_state:
        st.session_state.pipeline_running = False
    if "pipeline_done" not in st.session_state:
        st.session_state.pipeline_done = False

    with col_req:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🔬 Deep Research Pipeline</div>', unsafe_allow_html=True)
        st.caption("Four autonomous AI agents collaborate in sequence: Search -> Deep Reader -> Report Writer -> Strict Critic.")

        research_topic = st.text_input(
            "Enter Research Topic",
            placeholder="e.g., Solid-state batteries breakthrough in 2026",
            key="research_topic_input"
        )

        start_research = st.button("🚀  Launch Multi-Agent Research", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin-bottom:1rem;">
            <span class="tool-tag">💡 Quick Topics:</span>
            <span class="tool-tag">Quantum Computing 2026</span>
            <span class="tool-tag">Renewable Grid Storage</span>
            <span class="tool-tag">Autonomous AI Agents</span>
        </div>
        """, unsafe_allow_html=True)

    with col_pipe:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">⚙️ Pipeline Progress</div>', unsafe_allow_html=True)

        p_res = st.session_state.pipeline_results

        def get_step_state(step_name):
            steps = ["search", "reader", "writer", "critic"]
            if step_name in p_res:
                return "done"
            if st.session_state.pipeline_running:
                for s_key in steps:
                    if s_key not in p_res:
                        return "active" if s_key == step_name else "waiting"
            return "waiting"

        def render_node(num, title, desc, state):
            status_labels = {"waiting": ("WAITING", "status-wait"), "active": ("● RUNNING", "status-run"), "done": ("✔ COMPLETE", "status-done")}
            label, css_class = status_labels.get(state, ("WAITING", "status-wait"))
            st.markdown(f"""
            <div class="step-node {state}">
                <div class="step-header">
                    <span class="step-name">{num}. {title}</span>
                    <span class="step-status {css_class}">{label}</span>
                </div>
                <div style="font-size:0.78rem;color:#94a3b8;margin-top:0.2rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        render_node("01", "Search Agent", "Searches web sources & Wikipedia", get_step_state("search"))
        render_node("02", "Reader Agent", "Scrapes and parses deep URL content", get_step_state("reader"))
        render_node("03", "Writer Chain", "Drafts detailed structured report", get_step_state("writer"))
        render_node("04", "Critic Chain", "Audits, scores & critiques the report", get_step_state("critic"))
        st.markdown('</div>', unsafe_allow_html=True)

    # Execute Research Pipeline
    if start_research:
        if not research_topic.strip():
            st.warning("Please enter a research topic first.")
        else:
            st.session_state.pipeline_results = {}
            st.session_state.pipeline_running = True
            st.session_state.pipeline_done = False
            st.rerun()

    if st.session_state.pipeline_running and not st.session_state.pipeline_done:
        topic_text = st.session_state.research_topic_input
        results = {}

        # 1. Search Agent
        with st.spinner("🔍 Step 1/4: Search Agent is gathering web intelligence..."):
            s_agent = build_search_agent()
            sr = s_agent.invoke({"messages": [("user", f"Gather comprehensive and recent research data for: {topic_text}")]})
            results["search"] = sr["messages"][-1].content
            st.session_state.pipeline_results = dict(results)

        # 2. Reader Agent
        with st.spinner("📄 Step 2/4: Reader Agent is extracting full article data..."):
            r_agent = build_reader_agent()
            rr = r_agent.invoke({
                "messages": [("user", f"Based on the following research results about '{topic_text}', pick the most relevant URL and extract deeper text:\n\n{results['search'][:1000]}")]
            })
            results["reader"] = rr["messages"][-1].content
            st.session_state.pipeline_results = dict(results)

        # 3. Writer Chain
        with st.spinner("✍️ Step 3/4: Writer Chain is synthesizing the final report..."):
            combined = f"SEARCH RESULTS:\n{results['search']}\n\nDEEP SCRAPED CONTENT:\n{results['reader']}"
            writer_input = {"topic": topic_text, "research": combined}
            wr = writer_chain.invoke(writer_input)
            results["writer"] = wr
            st.session_state.pipeline_results = dict(results)

        # 4. Critic Chain
        with st.spinner("🔎 Step 4/4: Critic Chain is auditing the report..."):
            critic_input = {"report": results["writer"]}
            cr = critic_chain.invoke(critic_input)
            results["critic"] = cr
            st.session_state.pipeline_results = dict(results)

        st.session_state.pipeline_running = False
        st.session_state.pipeline_done = True
        st.rerun()

    # Display pipeline results
    if st.session_state.pipeline_done:
        res = st.session_state.pipeline_results
        st.markdown("### 📋 Research Results")

        if "search" in res:
            with st.expander("🔍 Search Agent Output", expanded=True):
                st.markdown(res["search"])
        if "reader" in res:
            with st.expander("📄 Reader Agent Output", expanded=False):
                st.markdown(res["reader"])
        if "writer" in res:
            with st.expander("✍️ Writer Chain Report", expanded=True):
                st.markdown(res["writer"])
        if "critic" in res:
            with st.expander("🧐 Critic Chain Score", expanded=False):
                st.markdown(res["critic"])

    elif st.session_state.pipeline_running:
        st.info("Pipeline is running... please wait.")


# ==============================================================================
# ⚡ TAB 3: DIRECT TOOL PLAYGROUND
# ==============================================================================
with tab_tools:
    st.markdown("### ⚡ Direct Tool Playground")
    st.caption("Test individual tools directly without going through the agent.")

    tool_options = {
        "🌦️ Weather": "weather",
        "📅 Forecast": "forecast",
        "📰 News": "news",
        "🏛️ City Places": "places",
        "📚 Wikipedia": "wiki",
        "🧮 Math": "math",
        "🕒 Time": "time",
        "🔍 Web Search": "web",
    }

    selected_tool = st.selectbox("Choose a tool:", list(tool_options.keys()), key="playground_tool")
    tool_key = tool_options[selected_tool]

    if tool_key == "weather":
        city = st.text_input("🌆 City name:", value="Mumbai", key="pw_city")
        if st.button("Run Tool", key="pw_weather"):
            with st.spinner("Fetching weather..."):
                result = get_weather.invoke(city)
                st.success(result)

    elif tool_key == "forecast":
        city = st.text_input("🌆 City name:", value="Paris", key="pf_city")
        if st.button("Run Tool", key="pw_forecast"):
            with st.spinner("Fetching forecast..."):
                result = get_forecast.invoke(city)
                st.success(result)

    elif tool_key == "news":
        topic = st.text_input("📰 Topic / Location:", value="London", key="pn_topic")
        if st.button("Run Tool", key="pw_news"):
            with st.spinner("Fetching news..."):
                result = get_news.invoke(topic)
                st.success(result)

    elif tool_key == "places":
        city = st.text_input("📍 City:", value="Tokyo", key="pp_city")
        if st.button("Run Tool", key="pw_places"):
            with st.spinner("Finding places..."):
                result = get_city_places.invoke(city)
                st.success(result)

    elif tool_key == "wiki":
        query = st.text_input("📚 Wikipedia query:", value="Alan Turing", key="pwiki_query")
        if st.button("Run Tool", key="pw_wiki"):
            with st.spinner("Searching Wikipedia..."):
                result = search_wikipedia.invoke(query)
                st.success(result)

    elif tool_key == "math":
        expr = st.text_input("🧮 Expression:", value="sqrt(144) * 25 + 50", key="pmath_expr")
        if st.button("Run Tool", key="pw_math"):
            with st.spinner("Calculating..."):
                result = calculate.invoke(expr)
                st.success(result)

    elif tool_key == "time":
        if st.button("Run Tool", key="pw_time"):
            with st.spinner("Fetching time..."):
                result = get_current_time.invoke("UTC")
                st.success(result)

    elif tool_key == "web":
        query = st.text_input("🔍 Search query:", value="latest AI news 2026", key="pweb_query")
        if st.button("Run Tool", key="pw_web"):
            with st.spinner("Searching web..."):
                result = web_search.invoke(query)
                st.success(result)
