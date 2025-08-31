import streamlit as st
import http.client
import json
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
API_KEY = os.getenv("RAPIDAPI_KEY")

if not API_KEY:
    st.error("❌ RAPIDAPI_KEY not found in environment variables. Please create a .env file with your API key.")
    st.stop()

# Cricbuzz API headers
HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': "cricbuzz-cricket.p.rapidapi.com"
}

BASE_URL = "cricbuzz-cricket.p.rapidapi.com"

# ---------------- Helper Functions ----------------
def search_players(query):
    conn = http.client.HTTPSConnection(BASE_URL)
    conn.request("GET", f"/stats/v1/player/search?plrN={query}", headers=HEADERS)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    try:
        return json.loads(data.decode("utf-8"))
    except:
        return {}


def get_player_details(player_id):
    conn = http.client.HTTPSConnection(BASE_URL)
    conn.request("GET", f"/stats/v1/player/{player_id}", headers=HEADERS)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    try:
        return json.loads(data.decode("utf-8"))
    except:
        return {}


def get_player_stats(player_id, stat_type="batting"):
    """Fetch batting or bowling stats"""
    url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/{stat_type}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return {}


def parse_stats_table(stats_json):
    """Convert Cricbuzz batting/bowling stats JSON to DataFrame"""
    if not stats_json or "headers" not in stats_json or "values" not in stats_json:
        return pd.DataFrame()

    headers = stats_json["headers"]  # e.g. [ROWHEADER, Test, ODI, T20, IPL]
    rows = []

    for row in stats_json["values"]:
        rows.append(row["values"])

    df = pd.DataFrame(rows, columns=headers)
    return df


# ---------------- Streamlit Page ----------------
st.title("🔎 Player Search & Profile")

# Step 1: Input player name
player_name = st.text_input("Enter player name (e.g. Kohli, Root, Dhoni):")

if player_name:
    results = search_players(player_name)

    if "player" in results and results["player"]:
        player_options = {p["name"]: p for p in results["player"]}

        # Step 2: Select player
        selected_name = st.selectbox("Select a player:", list(player_options.keys()))
        selected_player = player_options[selected_name]

        # Tabs for Profile / Batting / Bowling
        tabs = st.tabs(["📌 Profile", "🏏 Batting Stats", "🎯 Bowling Stats"])

        # ---------------- Profile Tab ----------------
        with tabs[0]:
            st.write(f"### {selected_player['name']} ({selected_player['teamName']})")
            st.write(f"📅 DOB: {selected_player.get('dob', 'N/A')}")

            # Player image
            if "faceImageId" in selected_player:
                img_url = f"http://i.cricketcb.com/stats/img/faceImages/{selected_player['faceImageId']}.jpg"
                st.image(img_url, width=150)

            # Detailed profile
            details = get_player_details(selected_player["id"])

            if details:
                st.subheader("Player Details")
                st.write(f"**Role:** {details.get('role', 'N/A')}")
                st.write(f"**Batting Style:** {details.get('bat', 'N/A')}")
                st.write(f"**Bowling Style:** {details.get('bowl', 'N/A')}")
                st.write(f"**Teams:** {details.get('teams', 'N/A')}")
                st.write(f"**Birth Place:** {details.get('birthPlace', 'N/A')}")

                # ICC Rankings
                if "rankings" in details and details["rankings"]:
                    st.subheader("🏆 ICC Rankings")
                    rankings = details["rankings"]

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("### Batting")
                        if "bat" in rankings and rankings["bat"]:
                            for k, v in rankings["bat"].items():
                                st.write(f"{k}: {v}")
                        else:
                            st.write("No rankings available")

                    with col2:
                        st.write("### Bowling")
                        if "bowl" in rankings and rankings["bowl"]:
                            for k, v in rankings["bowl"].items():
                                st.write(f"{k}: {v}")
                        else:
                            st.write("No rankings available")

                    with col3:
                        st.write("### All-Rounder")
                        if "all" in rankings and rankings["all"]:
                            for k, v in rankings["all"].items():
                                st.write(f"{k}: {v}")
                        else:
                            st.write("No rankings available")

                # Career Debut Info
                st.subheader("Career Debut Information")
                conn = http.client.HTTPSConnection(BASE_URL)
                conn.request("GET", f"/stats/v1/player/{selected_player['id']}/career", headers=HEADERS)
                res = conn.getresponse()
                career_data = res.read()
                conn.close()

                try:
                    career_json = json.loads(career_data.decode("utf-8"))
                    if "values" in career_json and career_json["values"]:
                        career_rows = []
                        for format_data in career_json["values"]:
                            if "values" in format_data:
                                career_rows.append(format_data["values"])
                        if career_rows:
                            career_df = pd.DataFrame(career_rows, columns=["Format", "Debut", "Last Played", "Debut Match ID", "Last Played Match ID"])
                            st.dataframe(career_df[["Format", "Debut", "Last Played"]], use_container_width=True)
                        else:
                            st.warning("No career debut information available.")
                    else:
                        st.warning("No career debut information available.")
                except:
                    st.warning("Could not load career debut information.")

                if "webURL" in details:
                    st.markdown(f"[🔗 View on Cricbuzz]({details['webURL']})")

        # ---------------- Batting Stats Tab ----------------
        with tabs[1]:
            st.subheader("Batting Stats")
            batting_stats = get_player_stats(selected_player["id"], "batting")
            df_bat = parse_stats_table(batting_stats)
            if not df_bat.empty:
                st.dataframe(df_bat, use_container_width=True)
            else:
                st.warning("No batting stats available.")

        # ---------------- Bowling Stats Tab ----------------
        with tabs[2]:
            st.subheader("Bowling Stats")
            bowling_stats = get_player_stats(selected_player["id"], "bowling")
            df_bowl = parse_stats_table(bowling_stats)
            if not df_bowl.empty:
                st.dataframe(df_bowl, use_container_width=True)
            else:
                st.warning("No bowling stats available.")

    else:
        st.warning("No players found. Try another name.")