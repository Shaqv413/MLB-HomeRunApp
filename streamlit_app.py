import streamlit as st
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {date.today()}")

@st.cache_data(show_spinner=True)
def fetch_data():
    stats_url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": "2025",
        "limit": 50,  # top 50
        "sortStat": "homeRuns"
    }
    
    response = requests.get(stats_url, params=params)
    data = response.json()

    players = data['stats'][0]['splits']
    player_list = []

    for player in players:
        info = player['player']
        stats = player['stat']

        name = info.get('fullName', 'Unknown')
        team = info.get('currentTeam', {}).get('name', 'N/A')

        try:
            ab = int(stats.get('atBats', 0))
            hr = int(stats.get('homeRuns', 0))
            ab_per_hr = ab / hr if hr > 0 else ab
            hr_chance = round(100 / ab_per_hr, 2) if ab_per_hr else 0.0
        except:
            hr_chance = 0.0

        player_list.append({
            "Player": name,
            "Team": team,
            "HRs": hr,
            "AVG": stats.get('avg', 'N/A'),
            "OPS": stats.get('ops', 'N/A'),
            "AB": ab,
            "AB/HR": round(ab / hr, 2) if hr > 0 else 'N/A',
            "HR Chance": f"{hr_chance:.2f}%"
        })

    df = pd.DataFrame(player_list)
    df = df.sort_values(by="HRs", ascending=False)
    return df

with st.spinner("Loading player data..."):
    df = fetch_data()

st.dataframe(df.reset_index(drop=True), use_container_width=True)
