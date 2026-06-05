import streamlit as st
import sys, os
import markdown

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.guardrails.pii import check_pii
from src.guardrails.intent import get_intent

# Lazy import retriever to avoid PyTorch crash on import
_retriever = None
_llm_client = None

def get_retriever():
    global _retriever
    if _retriever is None:
        try:
            from src.retrieve.retriever import HybridRetriever
            _retriever = HybridRetriever()
        except Exception as e:
            st.error(f"Retriever failed to initialize: {e}")
            return None
    return _retriever

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        try:
            from src.llm.client import GroqClient
            _llm_client = GroqClient()
        except Exception as e:
            st.error(f"LLM Client failed to initialize: {e}")
            return None
    return _llm_client

def run_pipeline(query: str) -> dict:
    """Full pipeline: PII -> Intent -> Retrieve -> Generate"""
    # 1. PII
    blocked, msg = check_pii(query)
    if blocked:
        return {"answer_text": msg, "citation_url": None, "last_updated": None, "kind": "refusal"}

    # 2. Intent
    label, link = get_intent(query)
    if label == "advisory":
        return {
            "answer_text": "I am a facts-only assistant and cannot provide investment advice or recommendations. Please refer to the official SEBI guidelines for educational resources and investment guidance.",
            "citation_url": "https://investor.sebi.gov.in", "last_updated": None, "kind": "refusal"
        }
    if label == "out_of_scope":
        return {
            "answer_text": "This query is out of scope. I can only answer questions based on the specific mutual fund documents loaded in my knowledge base.",
            "citation_url": None, "last_updated": None, "kind": "refusal"
        }

    # 3. Retrieve
    retriever = get_retriever()
    if not retriever or not retriever.initialized:
        return {"answer_text": "The knowledge base is not yet initialized. Please run the ingestion pipeline first.", "citation_url": None, "last_updated": None, "kind": "refusal"}

    res = retriever.retrieve(query)
    if res["status"] == "need_clarification":
        return {"answer_text": res["message"], "citation_url": None, "last_updated": None, "kind": "refusal"}
    if res["status"] == "no_hit":
        return {"answer_text": res["message"], "citation_url": None, "last_updated": None, "kind": "refusal"}
    if res["status"] == "error":
        return {"answer_text": "System error: " + res["message"], "citation_url": None, "last_updated": None, "kind": "refusal"}

    chunks = res["chunks"]

    # 4. Generate
    llm = get_llm_client()
    if not llm or not llm.client:
        return {"answer_text": "GROQ_API_KEY is not configured. Please add it to your .env file.", "citation_url": None, "last_updated": None, "kind": "refusal"}

    from src.llm.prompt import build_system_prompt
    system_prompt = build_system_prompt(chunks)
    answer = llm.complete(system_prompt, query, temperature=0.0)

    primary = chunks[0]
    citation = primary.get("metadata", {}).get("source_url", "")
    doc_date = primary.get("metadata", {}).get("doc_as_on_date")
    fetched = primary.get("metadata", {}).get("fetched_date")
    last_updated = doc_date if doc_date and str(doc_date) != "nan" else fetched

    return {"answer_text": answer, "citation_url": citation, "last_updated": last_updated, "kind": "factual"}

# ─── Streamlit Page Config ───
st.set_page_config(
    page_title="ICICI Prudential Mutual Fund Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Design System CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Hanken+Grotesk:wght@600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

:root {
    --primary: #00d09c;
    --primary-container: #006c4f;
    --on-primary: #002116;
    --on-primary-container: #ffffff;
    --surface-gray: #1E1E1E;
    --background-white: #121212;
    --border-subtle: #333333;
    --text-main: #E0E0E0;
    --on-surface: #FFFFFF;
    --on-surface-variant: #A0A0A0;
    --error: #00d09c;
    --error-container: #003324;
}

/* --- Hide Streamlit defaults --- */
#MainMenu, footer {visibility: hidden;}
.stDeployButton {display: none !important;}

/* --- Global --- */
.stApp {
    background: var(--background-white) !important;
    font-family: 'Inter', sans-serif !important;
}

section[data-testid="stSidebar"] {
    background: var(--surface-gray) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Hanken Grotesk', sans-serif !important;
    color: var(--primary) !important;
}

/* --- Native Header Branding --- */
.brand-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-subtle);
}
.brand-header .icon {
    color: var(--primary);
    font-size: 32px;
}
.brand-header h1 {
    font-family: 'Hanken Grotesk', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: var(--primary);
    margin: 0;
    line-height: 1.2;
}

/* --- Disclaimer Banner --- */
.disclaimer-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 16px;
    background: var(--error-container);
    color: var(--error);
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 24px;
    border: 1px solid rgba(0, 208, 156, 0.15);
}
.disclaimer-banner .material-symbols-outlined {
    font-size: 18px;
}

/* --- Welcome Section --- */
.welcome-section {
    text-align: center;
    max-width: 720px;
    margin: 32px auto 40px;
}
.welcome-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, #59fdc5, #00d09c);
    border-radius: 50%;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px rgba(0, 208, 156, 0.25);
}
.welcome-icon .material-symbols-outlined {
    font-size: 32px;
    color: #002116;
    font-variation-settings: 'FILL' 1;
}
.welcome-section h1 {
    font-family: 'Hanken Grotesk', sans-serif;
    font-size: 42px;
    font-weight: 700;
    line-height: 50px;
    letter-spacing: -0.02em;
    color: var(--on-surface);
    margin: 0 0 16px;
}
.welcome-section p {
    font-size: 18px;
    line-height: 28px;
    color: var(--on-surface-variant);
    max-width: 560px;
    margin: 0 auto;
}

/* --- Example Cards --- */
.example-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    max-width: 900px;
    margin: 0 auto 40px;
}
@media (max-width: 768px) {
    .example-cards { grid-template-columns: 1fr; }
}
.example-card {
    background: var(--surface-gray);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 24px;
    height: 180px; /* Fixed height so boxes are uniform */
    cursor: pointer;
    display: flex;
    flex-direction: column;
    transition: all 0.25s ease;
}
.example-card:hover {
    border-color: var(--primary-container);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
}
.example-card h3 {
    margin: 16px 0 auto 0;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.4;
    color: var(--on-surface);
}
.example-card .card-icon {
    color: var(--primary);
    font-size: 24px;
    margin-bottom: 16px;
}
.example-card h3 {
    font-family: 'Hanken Grotesk', sans-serif;
    font-size: 17px;
    font-weight: 600;
    line-height: 1.35;
    color: var(--on-surface);
    margin: 0 0 auto;
    transition: color 0.2s;
}
.example-card:hover h3 { color: var(--primary); }
.example-card .ask-link {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--primary);
    font-size: 12px;
    font-weight: 600;
    margin-top: 16px;
}

/* --- Chat Messages --- */
.chat-user-msg {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 20px;
}
.chat-user-bubble {
    background: var(--primary);
    color: var(--on-primary);
    padding: 14px 20px;
    border-radius: 16px 16px 4px 16px;
    max-width: 70%;
    font-size: 16px;
    line-height: 24px;
    box-shadow: 0 4px 12px rgba(0, 108, 79, 0.15);
}
.chat-bot-msg {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 24px;
}
.chat-bot-avatar {
    width: 36px;
    height: 36px;
    min-width: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #59fdc5, #00d09c);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 2px;
}
.chat-bot-avatar .material-symbols-outlined {
    font-size: 20px;
    color: #002116;
    font-variation-settings: 'FILL' 1;
}
.chat-bot-bubble {
    background: var(--surface-gray);
    border: 1px solid var(--border-subtle);
    border-radius: 4px 16px 16px 16px;
    padding: 20px 24px;
    max-width: 75%;
    font-size: 16px;
    line-height: 26px;
    color: var(--text-main);
}
.chat-bot-bubble p {
    margin: 0 0 12px 0;
}
.chat-bot-bubble p:last-child {
    margin-bottom: 0;
}
.chat-bot-bubble ul, .chat-bot-bubble ol {
    margin: 0 0 12px 0;
    padding-left: 24px;
}
.chat-bot-bubble li {
    margin-bottom: 6px;
}
.chat-bot-bubble strong {
    color: var(--primary);
}
.chat-citation {
    margin-top: 16px;
    padding-top: 14px;
    border-top: 1px solid var(--border-subtle);
    font-size: 13px;
    color: var(--on-surface-variant);
    line-height: 20px;
}
.chat-citation a {
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
}
.chat-citation a:hover { text-decoration: underline; }
.chat-citation .last-updated {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
    color: #7C7E8C;
    font-size: 12px;
}

/* --- Refusal styling --- */
.refusal-bubble {
    background: var(--error-container) !important;
    color: var(--error) !important;
    border: 1px solid rgba(0, 208, 156, 0.2) !important;
}

/* --- Source Hub Cards --- */
.source-card {
    background: var(--surface-gray);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px; /* Creates vertical spacing between stacked cards */
    height: 220px; /* Enforce uniform size across all cards */
    display: flex;
    flex-direction: column;
    transition: all 0.25s ease;
}
.source-card:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}
.source-badge {
    display: inline-block;
    align-self: flex-start;
    padding: 4px 12px;
    border: 1px solid var(--primary-container);
    color: var(--primary);
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.source-card h3 {
    font-family: 'Hanken Grotesk', sans-serif;
    font-size: 20px;
    font-weight: 600;
    color: var(--on-surface);
    margin: 0 0 12px;
}
.source-card p {
    font-size: 14px;
    line-height: 22px;
    color: var(--on-surface-variant);
    margin: 0 0 auto 0;
}
.source-link {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--primary);
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    padding: 6px 0;
    transition: opacity 0.2s;
}
.source-link:hover { opacity: 0.7; }

/* --- Suggestion Chips --- */
.suggestion-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
    margin-top: 8px;
}
.suggestion-chip {
    padding: 6px 14px;
    background: rgba(0, 208, 156, 0.08);
    color: var(--primary);
    border: 1px solid rgba(0, 108, 79, 0.1);
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
    text-decoration: none;
}
.suggestion-chip:hover {
    background: rgba(0, 208, 156, 0.18);
}

/* Streamlit input overrides */
div[data-testid="stChatInput"] > div {
    border-color: var(--border-subtle) !important;
    border-radius: 16px !important;
    background: var(--surface-gray) !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--primary-container) !important;
    box-shadow: 0 0 0 3px rgba(0, 208, 156, 0.15) !important;
}

/* Hide streamlit chat avatars (we use custom ones) */
div[data-testid="stChatMessage"] > div:first-child {
    display: none !important;
}
</style>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"/>
""", unsafe_allow_html=True)

# ─── Native Brand Header ───
st.markdown("""
<div class="brand-header">
    <span class="material-symbols-outlined icon">account_balance</span>
    <h1>ICICI Prudential Document Assistant</h1>
</div>
""", unsafe_allow_html=True)

# ─── Navigation & Query Params ───
if "nav_radio" not in st.session_state:
    st.session_state["nav_radio"] = "🏠 Home"

params = st.query_params
q_param = params.get("q", "")

# Process URL navigation once
if "nav" in params:
    nav = params["nav"]
    if nav == "Chat":
        st.session_state["nav_radio"] = "💬 Chat"
    elif nav == "SourceHub":
        st.session_state["nav_radio"] = "📚 Source Hub"
    del st.query_params["nav"]

# ─── Sidebar ───
with st.sidebar:
    st.markdown("## ICICI Pru Assistant")
    st.caption("Facts-only Intelligence")
    st.divider()

    page = st.radio(
        "Navigation",
        ["🏠 Home", "💬 Chat", "📚 Source Hub"],
        key="nav_radio",
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("""
    <a href="https://www.icicipruamc.com" target="_blank" style="
        display: flex; align-items: center; justify-content: center; gap: 8px;
        background: #006c4f; color: white; padding: 12px 16px; border-radius: 12px;
        text-decoration: none; font-weight: 600; font-size: 14px; transition: opacity 0.2s;
    ">
        <span class="material-symbols-outlined" style="font-size:18px">description</span>
        Official Documents
    </a>
    """, unsafe_allow_html=True)

# ─── HOME PAGE ───
if page == "🏠 Home":
    # Clear query params if on home
    st.query_params.clear()
    
    # Disclaimer
    st.markdown("""
    <div class="disclaimer-banner">
        <span class="material-symbols-outlined">verified_user</span>
        FACTS-ONLY. NO INVESTMENT ADVICE.
    </div>
    """, unsafe_allow_html=True)

    # Welcome
    st.markdown("""
    <div class="welcome-section">
        <div class="welcome-icon">
            <span class="material-symbols-outlined">smart_toy</span>
        </div>
        <h1>Welcome to the ICICI Prudential Document Assistant</h1>
        <p>Your intelligent companion for extracting precise, factual information specifically from ICICI Prudential mutual fund documents loaded into this system.</p>
    </div>
    """, unsafe_allow_html=True)

    # Example Cards
    examples = [
        {"icon": "payments", "q": "What is the exit load for the Technology Fund?"},
        {"icon": "account_balance", "q": "Who manages the Bharat 22 FOF?"},
        {"icon": "lock_clock", "q": "What is the Minimum SIP Investment for Pharma Fund?"},
    ]

    import urllib.parse
    
    st.markdown('<div class="example-cards">', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, ex in enumerate(examples):
        with cols[i]:
            encoded_q = urllib.parse.quote(ex["q"])
            st.markdown(f"""
            <a href="/?nav=Chat&q={encoded_q}" target="_self" style="text-decoration: none; color: inherit; display: block; height: 100%;">
                <div class="example-card">
                    <span class="material-symbols-outlined card-icon">{ex["icon"]}</span>
                    <h3>{ex["q"]}</h3>
                    <div class="ask-link">Ask now <span class="material-symbols-outlined" style="font-size:14px">arrow_forward</span></div>
                </div>
            </a>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Trusted Intelligence banner
    st.markdown("""
    <div style="max-width:900px; margin:0 auto 40px; border-radius:20px; overflow:hidden; position:relative; height:160px;
        background: linear-gradient(135deg, #006c4f 0%, #00d09c 100%);">
        <div style="position:absolute; inset:0; display:flex; align-items:center; padding:0 40px;">
            <div>
                <h4 style="font-family:'Hanken Grotesk',sans-serif; font-size:24px; font-weight:600; color:white; margin:0 0 8px;">Trusted Intelligence</h4>
                <p style="color:rgba(255,255,255,0.9); font-size:14px; line-height:22px; max-width:360px; margin:0;">Data sourced directly from official AMC disclosures and SEBI filings.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── CHAT PAGE ───
elif page == "💬 Chat":
    # Clear query param once processed
    if q_param:
        st.query_params.clear()
        
    # Disclaimer
    st.markdown("""
    <div class="disclaimer-banner">
        <span class="material-symbols-outlined">verified_user</span>
        FACTS-ONLY. NO INVESTMENT ADVICE.
    </div>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            safe_prompt = markdown.markdown(str(msg["content"]), extensions=['nl2br', 'sane_lists'])
            st.markdown(f"""
<div class="chat-user-msg">
    <div class="chat-user-bubble">{safe_prompt}</div>
</div>
""", unsafe_allow_html=True)
        else:
            bubble_class = "chat-bot-bubble refusal-bubble" if msg.get("kind") == "refusal" else "chat-bot-bubble"
            citation_html = ""
            if msg.get("citation_url"):
                citation_html += f'<div class="chat-citation">📖 Source: <a href="{msg["citation_url"]}" target="_blank">{msg["citation_url"]}</a>'
                if msg.get("last_updated"):
                    citation_html += f'<div class="last-updated"><span class="material-symbols-outlined" style="font-size:14px">schedule</span> Last updated from sources: {msg["last_updated"]}</div>'
                citation_html += '</div>'

            citation_str = citation_html if citation_html else ""
            safe_content = markdown.markdown(str(msg["content"]), extensions=['nl2br', 'sane_lists'])
            st.markdown(f'<div class="chat-bot-msg"><div class="chat-bot-avatar"><span class="material-symbols-outlined">smart_toy</span></div><div class="{bubble_class}">{safe_content}{citation_str}</div></div>', unsafe_allow_html=True)

    # Handle incoming query from URL
    prompt = st.chat_input("Ask about funds, exit loads, or policies...")
    
    # If the user clicked a card, q_param is populated
    if q_param and not prompt:
        prompt = q_param
        
    if st.session_state.get("suggestion") and not prompt:
        prompt = st.session_state["suggestion"]
        st.session_state["suggestion"] = "" # Clear it immediately

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        safe_prompt = markdown.markdown(str(prompt), extensions=['nl2br', 'sane_lists'])
        st.markdown(f"""
<div class="chat-user-msg">
    <div class="chat-user-bubble">{safe_prompt}</div>
</div>
""", unsafe_allow_html=True)

        # Run pipeline
        with st.spinner("Searching official documents..."):
            result = run_pipeline(prompt)

        # Add bot response
        bot_msg = {
            "role": "assistant",
            "content": result["answer_text"],
            "citation_url": result.get("citation_url"),
            "last_updated": result.get("last_updated"),
            "kind": result["kind"]
        }
        st.session_state.messages.append(bot_msg)

        bubble_class = "chat-bot-bubble refusal-bubble" if result["kind"] == "refusal" else "chat-bot-bubble"
        citation_html = ""
        if result.get("citation_url"):
            citation_html += f'<div class="chat-citation">📖 Source: <a href="{result["citation_url"]}" target="_blank">{result["citation_url"]}</a>'
            if result.get("last_updated"):
                citation_html += f'<div class="last-updated"><span class="material-symbols-outlined" style="font-size:14px">schedule</span> Last updated from sources: {result["last_updated"]}</div>'
            citation_html += '</div>'

        citation_str = citation_html if citation_html else ""
        safe_content = markdown.markdown(str(result["answer_text"]), extensions=['nl2br', 'sane_lists'])
        st.markdown(f'<div class="chat-bot-msg"><div class="chat-bot-avatar"><span class="material-symbols-outlined">smart_toy</span></div><div class="{bubble_class}">{safe_content}{citation_str}</div></div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns([1.5, 2, 2, 2, 2])
    with col1:
        st.markdown('<div style="font-size:12px; color:#7C7E8C; font-weight:500; margin-top:8px;">Suggestions:</div>', unsafe_allow_html=True)
    with col2:
        if st.button("Technology Exit Load", use_container_width=True):
            st.session_state["suggestion"] = "What is the exit load for the Technology Fund?"
            st.rerun()
    with col3:
        if st.button("Bharat 22 Manager", use_container_width=True):
            st.session_state["suggestion"] = "Who manages the Bharat 22 FOF?"
            st.rerun()
    with col4:
        if st.button("Pharma SIP Amount", use_container_width=True):
            st.session_state["suggestion"] = "What is the minimum SIP amount for the Pharma Fund?"
            st.rerun()


    # Footer disclaimer
    st.markdown("""
    <div style="text-align:center; margin-top:24px; font-size:12px; color:#7C7E8C; font-style:italic;">
        AI-generated response based on official ICICI Prudential mutual fund documents.
    </div>
    """, unsafe_allow_html=True)


# ─── SOURCE HUB PAGE ───
elif page == "📚 Source Hub":
    st.markdown("""
    <h1 style="font-family:'Hanken Grotesk',sans-serif; font-size:32px; font-weight:600; color:#181b26; margin-bottom:8px;">The Source Hub</h1>
    <p style="color:var(--on-surface-variant); max-width:800px; margin:0 auto; font-size:15px; line-height:1.6;">
        A verified repository of core mutual fund schemes, regulatory documents, and investor education resources. All information is direct from official filings.
    </p>
    """, unsafe_allow_html=True)

    import csv
    import os
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    sources_file = os.path.join(data_dir, "sources.csv")
    
    schemes = []
    if os.path.exists(sources_file):
        with open(sources_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['url'].strip():
                    schemes.append(row)
                    
    # Let's display them in a responsive grid
    cols = st.columns(3)
    for i, s in enumerate(schemes):
        with cols[i % 3]:
            # Generate a badge dynamically
            badge_text = "FUND"
            title_upper = s['title'].upper()
            if "EQUITY" in title_upper or "BLUECHIP" in title_upper: badge_text = "EQUITY"
            if "FOF" in title_upper: badge_text = "FOF"
            if "RETIREMENT" in title_upper: badge_text = "RETIREMENT"
            if "BALANCED" in title_upper or "HYBRID" in title_upper or "DYNAMIC" in title_upper: badge_text = "HYBRID"
            
            st.markdown(f"""
            <div class="source-card">
                <span class="source-badge">{badge_text}</span>
                <h3 style="font-size: 16px; margin-bottom: 8px;">{s["title"]}</h3>
                <div style="border-top:1px solid #EBECEF; padding-top:12px; margin-top: auto;">
                    <a class="source-link" href="{s["url"]}" target="_blank">
                        <span class="material-symbols-outlined" style="font-size:16px">open_in_new</span>
                        Groww Source
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Investor Resources
    st.markdown("""
    <h2 style="font-family:'Hanken Grotesk',sans-serif; font-size:24px; font-weight:600; color:#181b26; margin:32px 0 16px;">Investor Resources</h2>
    <p style="font-size:14px; line-height:22px; color:#3c4a43; margin-bottom:24px;">
        Access general regulatory guidelines and educational content to make informed investment decisions.
    </p>
    """, unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    resources = [
        {"name": "AMFI India", "url": "https://www.amfiindia.com", "icon": "language"},
        {"name": "SEBI Investor Education", "url": "https://investor.sebi.gov.in", "icon": "gavel"},
        {"name": "ICICI Pru AMC", "url": "https://www.icicipruamc.com", "icon": "account_balance"},
    ]
    for col, res in zip([r1, r2, r3], resources):
        with col:
            st.markdown(f"""
            <div class="source-card" style="text-align:center; padding:24px;">
                <span class="material-symbols-outlined" style="font-size:36px; color:#006c4f; margin-bottom:12px;">{res["icon"]}</span>
                <h3 style="font-size:16px;">{res["name"]}</h3>
                <a class="source-link" href="{res["url"]}" target="_blank" style="justify-content:center; margin-top:auto;">
                    Visit <span class="material-symbols-outlined" style="font-size:14px">open_in_new</span>
                </a>
            </div>
            """, unsafe_allow_html=True)
