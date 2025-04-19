import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown("#### Date: {}".format(datetime.today().strftime("%Y-%m-%d")))

# Ballpark Home Run Factors (simplified for example)
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
}

def fetch_data():
    url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": "2024",
        "limit": 100,
        "sortStat": "homeRuns"
    }
    res = requests.get(url, params=params).json()
    players = res['stats'][0]['splits']
    
    results = []
    for player in players:
        info = player['player']
        stats = player['stat']
        
        # Pull team name if available
        team = info.get('currentTeam', {}).get('name', 'N/A')
        
        results.append({
            "Player": info.get('fullName', 'Unknown'),
            "Team": team,
            "HRs": stats.get('homeRuns', 0),
            "AVG": stats.get('avg', 'N/A'),
            "OPS": stats.get('ops', 'N/A'),
            "Pitcher": "N/A",
            "Matchup": "No confirmed matchup",
            "Location": "N/A",
            "Time": "N/A",
            "Park Factor": "N/A",
            "HR Chance": "N/A"
        })
    return pd.DataFrame(results)

df = fetch_data()

if df.empty:
    st.warning("No confirmed matchups available. Please check back later.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
