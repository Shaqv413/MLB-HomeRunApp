import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from pybaseball import statcast, playerid_lookup

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Predictor with Recent Performance")
st.markdown("#### Date: {}".format(datetime.today().strftime("%Y-%m-%d")))

@st.cache_data(show_spinner=False)
def get_team_lookup():
    team_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    res = requests.get(team_url).json()
    return {team['id']: team['abbreviation'] for team in res['teams']}

@st.cache_data(show_spinner=False)
def fetch_top_hitters(season):
    team_lookup = get_team_lookup()
    url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": season,
        "limit": 100,
        "sortStat": "homeRuns"
    }
    res = requests.get(url, params=params).json()
    players = res['stats'][0]['splits']
    results = []
    for player in players:
        info = player['player']
        stats = player['stat']
        team_id = player.get('team', {}).get('id')
        team = team_lookup.get(team_id, "N/A") if team_id else "N/A"
        results.append({
            "Player": info.get('fullName', 'Unknown'),
            "ID": info.get('id'),
            "Team": team,
            "HRs": stats.get('homeRuns', 0),
            "AVG": stats.get('avg', 'N/A'),
            "OPS": stats.get('ops', 'N/A')
        })
    return pd.DataFrame(results)

@st.cache_data(show_spinner=False)
def fetch_recent_stats(player_id, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    try:
        logs = statcast(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), player_id=player_id)
        logs = logs[logs['batter'] == player_id]
        if logs.empty:
            return 0, 'N/A', 'N/A'
        hr_count = logs['events'].fillna('').str.count('home_run').sum()
        hits = logs['events'].isin(['single', 'double', 'triple', 'home_run']).sum()
        ab = logs['at_bat'].sum()
        avg = round(hits / ab, 3) if ab > 0 else 'N/A'
        ops = 'N/A'  # Simplified placeholder
        return int(hr_count), avg, ops
    except:
        return 0, 'N/A', 'N/A'

with st.spinner("Loading player data..."):
    season = datetime.today().year
    df = fetch_top_hitters(season)

    # Add recent stats for each player
    recent_data = []
    for _, row in df.iterrows():
        pid = row['ID']
        hr7, avg7, ops7 = fetch_recent_stats(pid, 7)
        hr15, avg15, ops15 = fetch_recent_stats(pid, 15)
        recent_data.append({
            "HR (Last 7)": hr7,
            "AVG (Last 7)": avg7,
            "OPS (Last 7)": ops7,
            "HR (Last 15)": hr15,
            "AVG (Last 15)": avg15,
            "OPS (Last 15)": ops15
        })

    recent_df = pd.DataFrame(recent_data)
    full_df = pd.concat([df.reset_index(drop=True), recent_df], axis=1)
    full_df.drop(columns=["ID"], inplace=True)
    st.dataframe(full_df, use_container_width=True)
