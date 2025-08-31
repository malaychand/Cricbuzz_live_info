import streamlit as st
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Page configuration
st.set_page_config(
    page_title="🏏 Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stSelectbox > div > div {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics</h1>
        
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.image(r"C:\Users\malay chand\Desktop\project\guvi_project\test part\image\match.jpg", width=200)  # Cricket logo
        st.markdown("---")
        
        page = st.selectbox(
            "🧭 Navigate to:",
            [
                "🏠 Home",
                "⚡ Live Matches", 
                "📊 Top Stats",
                "🔍 SQL Analytics",
                "🛠️ CRUD Operations"
            ]
        )
        
        

    # Route to appropriate page
    if page == "🏠 Home":
        show_home()
    elif page == "⚡ Live Matches":
        from pages.live_matches import show_live_matches
        show_live_matches()
    elif page == "📊 Top Stats":
        from pages.top_stats import show_top_stats
        show_top_stats()
    elif page == "🔍 SQL Analytics":
        from pages.sql_queries import show_sql_queries
        show_sql_queries()
    elif page == "🛠️ CRUD Operations":
        from pages.crud_operations import show_crud_operations
        show_crud_operations()

def show_home():
    st.markdown("## 🌟 Welcome to Cricbuzz LiveStats Dashboard")
    
    # Feature overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ Live Matches</h3>
            <p>Real-time match updates, scores, and player performance</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Top Stats</h3>
            <p>Batting and bowling leaders across formats</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🔍 SQL Analytics</h3>
            <p>Custom queries and advanced analytics</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🛠️ CRUD Operations</h3>
            <p>Manage player data and match records</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Architecture Overview
    st.markdown("### 🏗️ System Architecture")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔌 API Integration")
        st.code("""
        # Cricbuzz API Integration
        import requests
                
        headers = {
            "x-rapidapi-key": "your-api-key",
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }
                
        response = requests.get(
            "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live", 
            headers=headers
        )
        """, language="python")
    
    with col2:
        st.markdown("### 🗄️ Database Schema")
        st.code("""
        # MySQL Database Tables
        CREATE TABLE matches (
            match_id INT PRIMARY KEY,
            team1 VARCHAR(100),
            venue VARCHAR(200)
        );
        
        CREATE TABLE players (
            player_id INT PRIMARY KEY,
            name VARCHAR(100),
            team VARCHAR(100),
            role VARCHAR(50)
        );
        """, language="sql")
    
    # Project Stats
    st.markdown("## 📈 Project Overview")
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("API Endpoints", "15+", "🔗")
    
    with metric_col2:
        st.metric("Database Tables", "8", "🗄️")
    
    with metric_col3:
        st.metric("Live Matches", "25+", "⚡")
    
    with metric_col4:
        st.metric("Player Records", "5000+", "👥")

if __name__ == "__main__":
    main()