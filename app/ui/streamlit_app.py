import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocIQ — Enterprise RAG",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

.stApp { background-color: #0a0a0f; color: #e8e4dc; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1200px; }

[data-testid="stSidebar"] {
    background: #0f0f18;
    border-right: 1px solid #1e1e2e;
}
[data-testid="stSidebar"] > div { padding: 2rem 1.5rem; }

.dociq-logo {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    color: #e8e4dc;
    letter-spacing: -2px;
    line-height: 1;
}
.dociq-logo span { color: #6ee7b7; }

.dociq-tagline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #4a4a6a;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2.5rem;
    border-left: 2px solid #6ee7b7;
    padding-left: 10px;
}

.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #4a4a6a;
    margin-bottom: 0.75rem;
}

[data-testid="stFileUploader"] {
    background: #0f0f18;
    border: 1px dashed #2a2a3e;
    border-radius: 8px;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #6ee7b7; }

.stButton > button {
    background: transparent;
    border: 1px solid #6ee7b7;
    color: #6ee7b7;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-radius: 4px;
    padding: 0.5rem 1.25rem;
    transition: all 0.2s;
    width: 100%;
}
.stButton > button:hover { background: #6ee7b7; color: #0a0a0f; }
.stButton > button[kind="primary"] { background: #6ee7b7; color: #0a0a0f; font-weight: 600; }
.stButton > button[kind="primary"]:hover { background: #34d399; border-color: #34d399; }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #0f0f18;
    border: 1px solid #1e1e2e;
    color: #e8e4dc;
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6ee7b7;
    box-shadow: 0 0 0 2px rgba(110,231,183,0.1);
}

.answer-card {
    background: #0f0f18;
    border: 1px solid #1e1e2e;
    border-left: 3px solid #6ee7b7;
    border-radius: 8px;
    padding: 1.5rem 1.75rem;
    font-size: 1rem;
    line-height: 1.75;
    color: #c8c4bc;
    margin: 1rem 0;
    white-space: pre-wrap;
}

.metric-row { display: flex; gap: 12px; margin: 1.25rem 0; }
.metric-card {
    flex: 1;
    background: #0f0f18;
    border: 1px solid #1e1e2e;
    border-radius: 6px;
    padding: 0.875rem 1rem;
    text-align: center;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem;
    font-weight: 500;
    color: #6ee7b7;
    line-height: 1;
}
.metric-label {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #4a4a6a;
    margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
}

.citation-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #6ee7b7;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 1.5rem 0 0.75rem;
}
.citation-item {
    background: #0f0f18;
    border: 1px solid #1e1e2e;
    border-radius: 6px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    color: #7a7a9a;
    line-height: 1.6;
}
.citation-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #4a4a6a;
    margin-bottom: 0.5rem;
    display: flex;
    gap: 1rem;
}
.citation-score { color: #6ee7b7; }

.badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 3px;
    margin-left: 6px;
}
.badge-green { background: rgba(110,231,183,0.15); color: #6ee7b7; }
.badge-yellow { background: rgba(251,191,36,0.15); color: #fbbf24; }
.badge-red { background: rgba(239,68,68,0.15); color: #ef4444; }

.doc-item {
    background: #0f0f18;
    border: 1px solid #1e1e2e;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.4rem;
}
.doc-name { font-size: 0.85rem; color: #c8c4bc; }
.doc-chunks { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #4a4a6a; }

hr { border-color: #1e1e2e; margin: 1.5rem 0; }

.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: #0f0f18;
    border-color: #1e1e2e;
    color: #e8e4dc;
    font-family: 'Syne', sans-serif;
}

.stSpinner > div { border-top-color: #6ee7b7 !important; }
.stSuccess { background: rgba(110,231,183,0.1); border-color: #6ee7b7; }
.stError { background: rgba(239,68,68,0.1); }
</style>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────
if "documents" not in st.session_state:
    st.session_state.documents = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# ─── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def check_api():
    """Cache health check for 10s — prevents blocking query execution."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else {}
    except requests.exceptions.ConnectionError:
        return False, {}
    except requests.exceptions.Timeout:
        return False, {}
    except Exception:
        return False, {}

def refresh_docs():
    try:
        r = requests.get(f"{API_URL}/documents", timeout=5)
        if r.status_code == 200:
            data = r.json()
            st.session_state.documents = data if isinstance(data, list) else []
    except Exception:
        pass

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="dociq-logo">Doc<span>IQ</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="dociq-tagline">Enterprise RAG System</div>', unsafe_allow_html=True)

    # API status badge
    api_ok, health = check_api()
    if api_ok:
        generation = health.get("components", {}).get("generation", False)
        gen_label = "online" if generation else "offline"
        gen_badge = "badge-green" if generation else "badge-yellow"
        st.markdown(
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.68rem;'
            f'color:#4a4a6a;margin-bottom:1.5rem;">'
            f'API <span class="badge badge-green">online</span> &nbsp; '
            f'LLM <span class="badge {gen_badge}">{gen_label}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.68rem;'
            'color:#ef4444;margin-bottom:1.5rem;">'
            'API <span class="badge badge-red">offline</span> &nbsp;'
            '<span style="color:#4a4a6a;font-size:0.6rem;">run: python -m app.main</span>'
            '</div>',
            unsafe_allow_html=True
        )

    # Upload section
    st.markdown('<div class="section-label">Upload Document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "label",
        type=["pdf", "txt", "docx", "png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        st.markdown(
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;'
            f'color:#7a7a9a;margin:0.5rem 0;">⬡ {uploaded_file.name}</div>',
            unsafe_allow_html=True
        )
        if st.button("Index Document", type="primary"):
            with st.spinner("Processing..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                try:
                    r = requests.post(
                        f"{API_URL}/documents/upload",
                        files=files,
                        timeout=120
                    )
                    if r.status_code == 200:
                        result = r.json()
                        st.success(f"✓ {result['chunks_indexed']} chunks indexed")
                        if result.get("ocr_used"):
                            st.info("🔍 OCR applied to scanned content")
                        refresh_docs()
                    else:
                        st.error(f"Upload failed: {r.text[:120]}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)[:100]}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Document list
    st.markdown('<div class="section-label">Indexed Documents</div>', unsafe_allow_html=True)
    refresh_docs()

    if st.session_state.documents:
        for doc in st.session_state.documents:
            ocr_tag = ' <span class="badge badge-yellow">OCR</span>' if doc.get("ocr_used") else ""
            st.markdown(
                f'<div class="doc-item">'
                f'<div class="doc-name">{doc.get("filename", "unknown")}{ocr_tag}</div>'
                f'<div class="doc-chunks">'
                f'{doc.get("chunks", 0)} chunks · {doc.get("char_count", 0):,} chars'
                f'</div></div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;'
            'color:#2a2a3e;text-align:center;padding:1.5rem 0;">No documents yet</div>',
            unsafe_allow_html=True
        )

    # Query history
    if st.session_state.query_history:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Recent Queries</div>', unsafe_allow_html=True)
        for q in st.session_state.query_history[-4:][::-1]:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#4a4a6a;padding:0.3rem 0;'
                f'border-bottom:1px solid #1e1e2e;">'
                f'{q[:45]}{"…" if len(q) > 45 else ""}</div>',
                unsafe_allow_html=True
            )

# ─── Main area ─────────────────────────────────────────────────────────────────
col_main, col_right = st.columns([3, 1])

with col_main:
    st.markdown('<div class="section-label">Ask a Question</div>', unsafe_allow_html=True)
    query = st.text_area(
        "label",
        placeholder="What are the key findings in this document?",
        height=100,
        label_visibility="collapsed"
    )

with col_right:
    st.markdown('<div class="section-label">Top Results</div>', unsafe_allow_html=True)
    top_k = st.number_input(
        "label", min_value=1, max_value=10, value=3,
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    run_query = st.button("⬡ Search & Answer", type="primary", use_container_width=True)

# ─── Query execution ───────────────────────────────────────────────────────────
# KEY FIX: No longer blocked by api_ok. The health check is cached and
# can show "offline" while the server is busy — we always try the request.
if run_query:
    if not query.strip():
        st.warning("Enter a question above.")
    else:
        with st.spinner("Retrieving · Reranking · Generating…"):
            try:
                r = requests.post(
                    f"{API_URL}/query",
                    json={"query": query.strip(), "top_k": int(top_k)},
                    timeout=120
                )
                if r.status_code == 200:
                    st.session_state.last_result = r.json()
                    if query.strip() not in st.session_state.query_history:
                        st.session_state.query_history.append(query.strip())
                else:
                    st.error(f"Query failed ({r.status_code}): {r.text[:200]}")
            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot reach the API. Make sure the FastAPI server is running:\n\n"
                    "`python -m app.main`"
                )
            except requests.exceptions.Timeout:
                st.error("Query timed out (>120s). The LLM may be slow — try again.")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)[:150]}")

# ─── Result display ────────────────────────────────────────────────────────────
if st.session_state.last_result:
    result = st.session_state.last_result

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown('<div class="section-label">Answer</div>', unsafe_allow_html=True)
    answer_text = result.get("answer", "No answer returned.")
    st.markdown(
        f'<div class="answer-card">{answer_text}</div>',
        unsafe_allow_html=True
    )

    # Metrics row
    r_ms = result.get("retrieval_time_ms", 0)
    g_ms = result.get("generation_time_ms", 0)
    t_ms = result.get("total_time_ms", 0)
    n_citations = len(result.get("citations", []))

    st.markdown(
        f'<div class="metric-row">'
        f'<div class="metric-card"><div class="metric-value">{r_ms:.0f}'
        f'<span style="font-size:0.75rem">ms</span></div>'
        f'<div class="metric-label">Retrieval</div></div>'
        f'<div class="metric-card"><div class="metric-value">{g_ms:.0f}'
        f'<span style="font-size:0.75rem">ms</span></div>'
        f'<div class="metric-label">Generation</div></div>'
        f'<div class="metric-card"><div class="metric-value">{t_ms:.0f}'
        f'<span style="font-size:0.75rem">ms</span></div>'
        f'<div class="metric-label">Total</div></div>'
        f'<div class="metric-card"><div class="metric-value">{n_citations}</div>'
        f'<div class="metric-label">Citations</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Citations
    if result.get("citations"):
        st.markdown('<div class="citation-header">⬡ Sources</div>', unsafe_allow_html=True)
        for i, c in enumerate(result["citations"], 1):
            score = c.get("score", 0)
            st.markdown(
                f'<div class="citation-item">'
                f'<div class="citation-meta">'
                f'<span>[{i}] {c.get("source", "unknown")}</span>'
                f'<span>page {c.get("page", 1)}</span>'
                f'<span class="citation-score">score {score:.3f}</span>'
                f'</div>'
                f'{c.get("text", "")}'
                f'</div>',
                unsafe_allow_html=True
            )

# ─── Empty state ───────────────────────────────────────────────────────────────
if not st.session_state.last_result and not run_query:
    st.markdown(
        '<div style="text-align:center;padding:4rem 2rem;">'
        '<div style="font-size:3rem;margin-bottom:1rem;color:#2a2a3e;">⬡</div>'
        '<div style="font-family:\'Syne\',sans-serif;font-size:1.1rem;font-weight:600;'
        'color:#3a3a5a;margin-bottom:0.5rem;">Upload a document · Ask a question</div>'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;'
        'letter-spacing:0.1em;color:#2a2a3e;">BM25 + VECTOR + RERANKING + LLM</div>'
        '</div>',
        unsafe_allow_html=True
    )