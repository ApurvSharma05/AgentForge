import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import json
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import Pipeline
from config import Config

st.set_page_config(
    page_title="🔍 Multi-Agent Research System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    /* Dark theme colors */
    :root {
        --bg-main: #0f0f0f;
        --bg-secondary: #1a1a1a;
        --text-primary: #e0e0e0;
        --text-secondary: #a0a0a0;
        --accent: #4a9eff;
        --border: #333333;
    }
    
    body, [data-testid="stMainBlockContainer"] {
        background-color: #0f0f0f !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1a1a1a !important;
        border-right: 1px solid #333333;
    }
    
    /* Text colors */
    [data-testid="stMarkdownContainer"], 
    .streamlit-expanderHeader,
    p, h1, h2, h3, h4, h5, h6 {
        color: #e0e0e0 !important;
    }
    
    /* Header styling */
    .header-container {
        background-color: #1a1a1a;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 3px solid #4a9eff;
        margin-bottom: 2rem;
    }
    
    .header-title {
        font-size: 2rem;
        font-weight: 600;
        color: #e0e0e0;
        margin: 0;
    }
    
    .header-subtitle {
        font-size: 0.9rem;
        color: #a0a0a0;
        margin-top: 0.5rem;
    }
    
    /* Cards */
    .card {
        background-color: #1a1a1a;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #333333;
        border-left: 3px solid #4a9eff;
        margin-bottom: 1rem;
    }
    
    /* Stage indicators */
    .stage-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .stage-pending {
        background-color: #333333;
        color: #a0a0a0;
    }
    
    .stage-running {
        background-color: #2a5a7f;
        color: #4a9eff;
    }
    
    .stage-success {
        background-color: #1a3a2a;
        color: #4ade80;
    }
    
    .stage-error {
        background-color: #3a1a1a;
        color: #ff6b6b;
    }
    
    /* Report section */
    .report-container {
        background-color: #1a1a1a;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #333333;
        border-top: 3px solid #4a9eff;
    }
    
    .report-title {
        color: #e0e0e0;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 1px solid #333333;
        padding-bottom: 0.8rem;
    }
    
    /* Statistics */
    .stat-card {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        border-left: 3px solid #4a9eff;
        color: #e0e0e0;
        padding: 1.2rem;
        border-radius: 8px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0.5rem 0;
        color: #4a9eff;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #a0a0a0;
    }
    
    /* Buttons */
    button {
        background-color: #4a9eff !important;
        border: none !important;
        color: #0f0f0f !important;
        font-weight: 600 !important;
    }
    
    button:hover {
        background-color: #3a8eef !important;
    }
    
    /* Input fields */
    input, textarea, [data-testid="stTextInput"] input {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        color: #e0e0e0 !important;
        border-radius: 4px !important;
    }
    
    /* Sliders */
    [data-testid="stSlider"] {
        color: #4a9eff !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #1a3a2a !important;
        border: 1px solid #2a5a3a !important;
        color: #4ade80 !important;
    }
    
    .stError {
        background-color: #3a1a1a !important;
        border: 1px solid #5a2a2a !important;
        color: #ff6b6b !important;
    }
    
    .stInfo {
        background-color: #1a2a3a !important;
        border: 1px solid #2a4a5a !important;
        color: #4a9eff !important;
    }
    
    .stWarning {
        background-color: #3a3a1a !important;
        border: 1px solid #5a5a2a !important;
        color: #ffd700 !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 4px !important;
    }
    
    /* Divider */
    hr {
        border-color: #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

if "pipeline" not in st.session_state:
    st.session_state.pipeline = None

if "execution_result" not in st.session_state:
    st.session_state.execution_result = None

if "execution_in_progress" not in st.session_state:
    st.session_state.execution_in_progress = False


def get_pipeline() -> Pipeline:
    """Get or create pipeline instance."""
    if st.session_state.pipeline is None:
        with st.spinner("⏳ Initializing pipeline..."):
            try:
                config = Config()
                st.session_state.pipeline = Pipeline(config)
            except Exception as e:
                st.error(f"❌ Failed to initialize pipeline: {str(e)}")
                st.stop()
    return st.session_state.pipeline


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🤖 Multi-Agent Research System</h1>
        <p class="header-subtitle">AI-powered research automation with intelligent agents</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with configuration options."""
    with st.sidebar:
        st.markdown("## Settings")
        
        num_results = st.slider(
            "Search Results",
            min_value=1,
            max_value=10,
            value=5
        )
        
        max_pages = st.slider(
            "Pages to Read",
            min_value=1,
            max_value=10,
            value=3
        )
        
        save_results = st.checkbox(
            "Save Results",
            value=True
        )
        
        st.markdown("---")
        
        pipeline = get_pipeline()
        agents = pipeline.get_agent_info()
        
        st.markdown("## Agents")
        for agent in agents:
            st.caption(f"• {agent['name']}")
        
        return num_results, max_pages, save_results


def render_execution_interface():
    """Render the main execution interface."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        topic = st.text_input(
            "Research Topic",
            placeholder="Enter topic to research...",
            help="What would you like to research?"
        )
    
    with col2:
        execute_button = st.button(
            "▶ Start",
            key="execute_button",
            use_container_width=True,
            disabled=not topic or st.session_state.execution_in_progress
        )
    
    return topic, execute_button


def render_execution_progress(pipeline, topic, num_results, max_pages, save_results):
    """Render execution progress with detailed stage tracking."""
    progress_placeholder = st.empty()
    stage_placeholder = st.empty()
    result_placeholder = st.empty()
    
    with progress_placeholder.container():
        st.markdown("### Execution Progress")
        progress_bar = st.progress(0)
    
    with stage_placeholder.container():
        st.markdown("### Stage Status")
        stage_cols = st.columns(4)
        stage_badges = {
            "search": stage_cols[0].empty(),
            "read": stage_cols[1].empty(),
            "write": stage_cols[2].empty(),
            "critique": stage_cols[3].empty()
        }
    
    st.session_state.execution_in_progress = True
    start_time = time.time()
    
    try:
        stages = ["search", "read", "write", "critique"]
        
        for idx, stage in enumerate(stages):
            progress = (idx / len(stages))
            progress_bar.progress(progress)
            
            badge_text = f"→ {stage.upper()}"
            stage_badges[stage].markdown(
                f'<span class="stage-badge stage-running">{badge_text}</span>',
                unsafe_allow_html=True
            )
        
        with result_placeholder.container():
            st.info("Running pipeline...")
        
        result = pipeline.execute(
            topic=topic,
            num_search_results=num_results,
            max_pages_to_read=max_pages,
            save_results=save_results
        )
        
        progress_bar.progress(1.0)
        elapsed = time.time() - start_time
        
        for stage in stages:
            if result["stages"][stage] and result["stages"][stage].get("success"):
                badge_text = f"✓ {stage.upper()}"
                stage_badges[stage].markdown(
                    f'<span class="stage-badge stage-success">{badge_text}</span>',
                    unsafe_allow_html=True
                )
            else:
                badge_text = f"✗ {stage.upper()}"
                stage_badges[stage].markdown(
                    f'<span class="stage-badge stage-error">{badge_text}</span>',
                    unsafe_allow_html=True
                )
        
        result_placeholder.empty()
        
        st.session_state.execution_result = result
        st.session_state.execution_in_progress = False
        
        if result["success"]:
            st.success(f"✓ Completed in {elapsed:.1f}s")
        else:
            st.error(f"Failed: {result['error']}")
        
        return result
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.session_state.execution_in_progress = False
        return None


def render_results(result):
    """Render the execution results."""
    if not result or not result.get("success"):
        return
    
    st.markdown("---")
    st.markdown("## Results")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_results = len(result["stages"]["search"]["data"]["results"]) if result["stages"]["search"] else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Search Results</div>
            <div class="stat-value">{search_results}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pages_read = len(result["stages"]["read"]["data"]["scraped_contents"]) if result["stages"]["read"] else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Pages Read</div>
            <div class="stat-value">{pages_read}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Status</div>
            <div class="stat-value">✓</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        timestamp = datetime.fromisoformat(result["timestamp"])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Time</div>
            <div class="stat-value">{timestamp.strftime('%H:%M')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if result.get("final_report"):
        st.markdown("---")
        st.markdown("## Report")
        
        with st.container():
            st.markdown(result['final_report'])
        
        if result.get("critique_feedback"):
            st.markdown("---")
            st.markdown("## Feedback")
            
            with st.expander("Critique Analysis", expanded=False):
                st.markdown(result['critique_feedback'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_json = json.dumps(result, indent=2, default=str)
            st.download_button(
                label="JSON",
                data=report_json,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            st.download_button(
                label="Markdown",
                data=result['final_report'],
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
    
    if result["stages"]["search"]:
        st.markdown("---")
        st.markdown("## Sources")
        
        sources = result["stages"]["search"]["data"]["results"]
        for i, source in enumerate(sources[:5], 1):
            with st.expander(f"{i}. {source.get('title', 'No title')[:60]}"):
                st.caption(f"**URL:** {source.get('link', 'N/A')}")
                st.caption(f"{source.get('snippet', 'N/A')[:200]}...")


def render_footer():
    """Render footer."""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #a0a0a0; border-top: 1px solid #333333; margin-top: 2rem;">
        <p style="margin: 0; font-size: 0.9rem;">🤖 Multi-Agent Research System</p>
        <p style="font-size: 0.8rem; margin-top: 0.5rem;">SearchAgent • ReaderAgent • WriterAgent • CritiqueAgent</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application function."""
    render_header()
    
    num_results, max_pages, save_results = render_sidebar()
    
    st.markdown("---")
    
    topic, execute_button = render_execution_interface()
    
    if execute_button and topic:
        pipeline = get_pipeline()
        result = render_execution_progress(
            pipeline,
            topic,
            num_results,
            max_pages,
            save_results
        )
        
        if result:
            render_results(result)
    
    elif st.session_state.execution_result:
        render_results(st.session_state.execution_result)
    
    render_footer()


if __name__ == "__main__":
    main()
