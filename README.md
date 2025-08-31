# 🏏 Real-Time Cricket Updates & Database Integration (Python + Streamlit)

A **Python + Streamlit project** that provides **real-time cricket updates, scorecards, and player information** using Cricbuzz API.  
This project also integrates with a database (MySQL / SQLite) to manage cricket-related data such as players, squads, and trending statistics.

---

## 🚀 Features
- 📊 **Live Cricket Updates** – Fetches real-time match details using Cricbuzz data.
- 📝 **Scorecards & Player Info** – View batting, bowling, and player statistics.
- 🎯 **Streamlit Dashboard** – Interactive web-based UI for browsing matches.
- 🗄️ **Database Integration** – Supports MySQL/SQLite for storing & managing data.
- 🔎 **SQL Queries** – Run custom queries directly from the app.
- 🛠 **CRUD Operations** – Insert, update, delete, and view cricket data.

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Cricbuzz_live_info
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
.env add you api key RAPIDAPI_KEY="API-Key"
```

5. **Run the application**
```bash
streamlit run app.py
```

## 🎯 Key Features Walkthrough

### 1. Live Matches Dashboard
- **Auto-refresh**: 30-second intervals for live updates
- **Filtering**: By format, status, and venue
- **Match Details**: Click-through for detailed information
- **Statistics**: Real-time match statistics and visualizations

### 2. Top Stats Analytics
- **Batting Leaders**: Runs, averages, strike rates, boundaries
- **Bowling Leaders**: Wickets, economy rates, maidens
- **Performance Trends**: Team and format comparisons
- **Data Management**: Sample data generation and cleanup

### 3. SQL Query Playground
- **Quick Queries**: Pre-built analytics for common scenarios
- **Custom Builder**: Write and execute custom SQL queries
- **Schema Explorer**: Interactive database schema browser

### 4. CRUD Operations
- **Player Management**: Complete lifecycle management
- **Match Management**: Add, update, view, and delete matches
- **Statistics Management**: Batting and bowling performance data
- **Data Cleanup**: Maintenance and integrity checks


## 🙏 Acknowledgments

- **Cricbuzz API** for providing comprehensive cricket data
- **Streamlit** for the amazing web app framework
- **MySQL** for robust data storage

---

**Built with ❤️ for cricket analytics enthusiasts**