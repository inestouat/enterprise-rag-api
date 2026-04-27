import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Enterprise RAG System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .citation-box {
        background-color: #fafafa;
        border-left: 4px solid #1f77b4;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🤖 Enterprise Document Intelligence</p>', unsafe_allow_html=True)
st.markdown("**AI-Powered Document Q&A with Hybrid Retrieval & Citation Grounding**")

# Sidebar
with st.sidebar:
    st.header(" Document Upload")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Drop your document here",
        type=["pdf", "txt", "docx", "png", "jpg", "jpeg"],
        help="Supports PDF, Word, Text, and scanned images (OCR)"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([1, 2])
        with col1:
            file_icon = "" if uploaded_file.name.endswith('.pdf') else "" if uploaded_file.name.endswith(('.png', '.jpg')) else ""
            st.markdown(f"**{file_icon} {uploaded_file.name}**")
        with col2:
            st.markdown(f"*{len(uploaded_file.getvalue()) / 1024:.1f} KB*")
        
        if st.button("Process Document", use_container_width=True):
            with st.spinner(" Analyzing document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                response = requests.post(f"{API_URL}/documents/upload", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f" Indexed **{result['chunks_indexed']}** chunks")
                    
                    metrics = {
                        "Characters": result['char_count'],
                        "OCR Used": " Yes" if result['ocr_used'] else " No"
                    }
                    for k, v in metrics.items():
                        st.markdown(f"**{k}:** {v}")
                else:
                    st.error(f" Error: {response.text}")
    
    st.markdown("---")
    st.header(" System Status")
    
    try:
        health = requests.get(f"{API_URL}/health", timeout=5).json()
        components = health.get('components', {})
        
        for name, status in components.items():
            icon = "" if status in [True, "ready"] else ""
            st.markdown(f"{icon} **{name.title()}**")
    except:
        st.error("API Offline")

# Main Content
st.markdown("---")

# Query Section
st.header(" Ask Your Question")

query_col, settings_col = st.columns([3, 1])

with query_col:
    query = st.text_input(
        "",
        placeholder="e.g., What are the key findings in the document?",
        label_visibility="collapsed"
    )

with settings_col:
    top_k = st.selectbox("Results", [1, 3, 5, 10], index=1)

if st.button(" Search & Generate Answer", type="primary", use_container_width=True):
    if not query:
        st.warning(" Please enter a question")
    else:
        with st.spinner(" Searching documents and generating answer..."):
            start_time = os.times()[0]
            
            response = requests.post(
                f"{API_URL}/query",
                json={"query": query, "top_k": top_k}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Answer Section
                st.markdown("---")
                st.subheader(" Generated Answer")
                
                answer_box = st.container()
                with answer_box:
                    st.markdown(f"*{result['answer']}*")
                
                # Performance Metrics
                st.markdown("---")
                st.subheader("⚡ Performance Metrics")
                
                m1, m2, m3, m4 = st.columns(4)
                
                with m1:
                    st.metric(
                        "Retrieval Time",
                        f"{result['retrieval_time_ms']:.0f}ms",
                        help="Time to find relevant documents"
                    )
                
                with m2:
                    st.metric(
                        "Generation Time",
                        f"{result['generation_time_ms']:.0f}ms",
                        help="Time for LLM to generate answer"
                    )
                
                with m3:
                    st.metric(
                        "Total Time",
                        f"{result['total_time_ms']:.0f}ms",
                        help="End-to-end response time"
                    )
                
                with m4:
                    efficiency = (result['retrieval_time_ms'] / result['total_time_ms'] * 100) if result['total_time_ms'] > 0 else 0
                    st.metric(
                        "Retrieval %",
                        f"{efficiency:.1f}%",
                        help="% of time spent on retrieval vs generation"
                    )
                
                # Citations
                if result["citations"]:
                    st.markdown("---")
                    st.subheader(f" Sources ({len(result['citations'])} found)")
                    
                    for i, citation in enumerate(result["citations"], 1):
                        score_color = "🟢" if citation['score'] > 0.8 else "🟡" if citation['score'] > 0.5 else "🔴"
                        
                        with st.expander(
                            f"{score_color} [{i}] {citation['source']} (Page {citation['page']}) — Score: {citation['score']:.3f}"
                        ):
                            st.markdown(f"```\n{citation['text']}\n```")
            else:
                st.error(f" API Error: {response.text}")

# Footer
st.markdown("---")
st.caption(" Built with FastAPI + Streamlit + Qwen2.5 | Hybrid Retrieval + Cross-Encoder Reranking + Citation Grounding")