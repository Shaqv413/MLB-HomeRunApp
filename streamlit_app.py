import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown("#### Date: {}".format(datetime.today().strftime("%Y-%m-%d")))

@st.cache_data(show_spinner=False)
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

        # Try getting team abbreviation from team object
        team_abbr = info.get('currentTeam', {}).get('abbreviation', None)

        # If no abbreviation, fallback to full name or N/A
        team_name = info.get('currentTeam', {}).get('name', None)
        team = team_abbr or team_name or "N/A"

        results.append({
            "Player": info.get('fullName', 'Unknown'),
            "Team": team,
            "HRs": stats.get('homeRuns', 0),
            "AVG": stats.get('avg', 'N/A'),
            "OPS": stats.get('ops', 'N/A')
        })

    return pd.DataFrame(results)

df = fetch_data()

if df.empty:
    st.warning("No player data found.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
