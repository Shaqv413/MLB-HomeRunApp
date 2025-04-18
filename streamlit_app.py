import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

today = datetime.now().strftime("%Y-%m-%d")

# Ballpark Home Run Factors (simplified)
park_factors = {
    "Coors Field": 120,
    "Yankee Stadium": 110,
    "Fenway Park": 108,
    "Dodger Stadium": 104,
    "Oracle Park": 85,
    "Petco Park": 91,
    "Great American Ball Park": 115,
    "LoanDepot Park": 88,
    "Camden Yards": 107,
    "Wrigley Field": 105,
    "Globe Life Field": 102,
    "Angel Stadium": 102,
    "Busch Stadium": 95,
    "Tropicana Field": 90,
    "Citi Field": 93,
    "PNC Park": 95,
    "T-Mobile Park": 94,
    "Minute Maid Park": 109,
    "American Family Field": 104,
    "Target Field": 98,
    "Rogers Centre": 106,
    "Comerica Park": 92,
    "Chase Field": 103,
    "Kauffman Stadium": 94,
    "Guaranteed Rate Field": 105,
    "Nationals Park": 99,
    "Progressive Field": 95,
    "Oakland Coliseum": 86
}

@st.cache_data(show_spinner=False)
def fetch_data():
df = fetch_data()

if df.empty:
    st.warning("No confirmed pitcher matchups today — showing top 100 HR leaders without HR chance.")
    
    stats_url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": "2025",
        "limit": 100,
        "sortStat": "homeRuns"
    }
    top_players = requests.get(stats_url, params=params).json()['stats'][0]['splits']
    fallback_rows = []

    for player in top_players:
        p = player['player']
        s = player['stat']
        fallback_rows.append({
            "Player": p['fullName'],
            "Team": p.get('currentTeam', {}).get('name', 'N/A'),
            "HRs": s.get('homeRuns', 0),
            "AVG": s.get('avg', 'N/A'),
            "OPS": s.get('ops', 'N/A'),
            "Pitcher": "N/A",
            "Matchup": "No confirmed matchup",
            "Location": "N/A",
            "Time": "N/A",
            "Park Factor": "N/A",
            "HR Chance": "N/A"
        })

    df = pd.DataFrame(fallback_rows)

st.dataframe(df.reset_index(drop=True), use_container_width=True)
