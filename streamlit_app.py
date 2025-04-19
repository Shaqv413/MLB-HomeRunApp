import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from pybaseball import statcast_batter, batting_stats_range

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown("#### Date: {}".format(datetime.today().strftime("%Y-%m-%d")))

@st.cache_data(show_spinner=False)
def get_team_lookup():
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    res = requests.get(url).json()
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
        })
    return pd.DataFrame(results)

def get_ab_hr_rate(player_name):
    seasons = {
        "2023": ("2023-03-01", "2023-11-01"),
        "2024": ("2024-03-01", "2024-11-01"),
        "2025": ("2025-03-01", datetime.today().strftime('%Y-%m-%d')),
    }
    total_ab = 0
    total_hr = 0
    weight = {"2023": 0.1, "2024": 0.3, "2025": 0.6}

    for year, (start, end) in seasons.items():
        try:
            stats = batting_stats_range(start, end)
            player_row = stats[stats['Name'] == player_name]
            if not player_row.empty:
                ab = int(player_row['AB'].values[0])
                hr = int(player_row['HR'].values[0])
                total_ab += ab * weight[year]
                total_hr += hr * weight[year]
        except:
            continue

    if total_hr > 0:
        ab_per_hr = round(total_ab / total_hr, 2)
        hr_rate = round(1 / ab_per_hr, 4)
        return ab_per_hr, hr_rate
    else:
        return "N/A", 0.0

def get_recent_hr_boost(batter_id):
    try:
        end = datetime.today()
        start = end - timedelta(days=7)
        logs = statcast_batter(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), batter_id)
        if logs.empty:
            return 0
        hr_count = logs['events'].fillna('').str.count('home_run').sum()
        if hr_count >= 4:
            return 0.25
        elif hr_count >= 2:
            return 0.1
        else:
            return 0
    except:
        return 0

with st.spinner("Loading player data..."):
    season = datetime.today().year
    df = fetch_top_hitters(season)

    # Add probability calculation
    hr_chances = []
    for _, row in df.iterrows():
        name = row['Player']
        pid = row['ID']
        ab_hr, base_rate = get_ab_hr_rate(name)
        recency_boost = get_recent_hr_boost(pid)
        hr_chance = round(base_rate * (1 + recency_boost) * 100, 2)
        hr_chances.append({
            "Player": name,
            "Team": row['Team'],
            "HRs": row['HRs'],
            "HR Chance": f"{hr_chance}%" if hr_chance > 0 else "N/A"
        })

    result_df = pd.DataFrame(hr_chances)
    st.dataframe(result_df, use_container_width=True)
