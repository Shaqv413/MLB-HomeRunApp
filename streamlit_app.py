import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown("#### Date: {}".format(datetime.today().strftime("%Y-%m-%d")))

@st.cache_data(show_spinner=False)
def get_team_lookup():
    """Fetch all team abbreviations and IDs"""
    team_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    res = requests.get(team_url).json()
    lookup = {}
    for team in res['teams']:
        lookup[team['id']] = team['abbreviation']
    return lookup

@st.cache_data(show_spinner=False)
def fetch_data():
    # Determine the current season based on today's date
    today = datetime.today()
    current_season = today.year

    # Get team ID to abbreviation map
    team_lookup = get_team_lookup()

    url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": current_season,
        "limit": 100,
        "sortStat": "homeRuns"
    }

    res = requests.get(url, params=params).json()
    players = res['stats'][0]['splits']

    results = []
    for player in players:
        info = player['player']
        stats = player['stat']

        # Get team ID from player['team']['id']
        team_id = player.get('team', {}).get('id')
        team = team_lookup.get(team_id, "N/A") if team_id else "N/A"

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
