import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pybaseball import statcast_batter_pitcher

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

today = datetime.now().strftime("%Y-%m-%d")

@st.cache_data(show_spinner=False)
def fetch_data():
    stats_url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": "2025",
        "limit": 100,
        "sortStat": "homeRuns"
    }
    top_players = requests.get(stats_url, params=params).json()['stats'][0]['splits']

    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    games_res = requests.get(schedule_url).json()
    games = games_res['dates'][0]['games'] if games_res['dates'] else []

    pitcher_map = {}
    game_meta = {}

    for game in games:
        venue = game['venue']['name']
        home_team = game['teams']['home']['team']['name']
        away_team = game['teams']['away']['team']['name']
        game_time = game['gameDate']
        hour = int(game_time[11:13])
        is_night = hour >= 18
        meta = {"venue": venue, "is_night": is_night}

        if 'probablePitcher' in game['teams']['home']:
            pitcher_map[away_team] = game['teams']['home']['probablePitcher']
            game_meta[away_team] = {**meta, "is_home": False}
        if 'probablePitcher' in game['teams']['away']:
            pitcher_map[home_team] = game['teams']['away']['probablePitcher']
            game_meta[home_team] = {**meta, "is_home": True}

    results = []
    for player in top_players:
        p = player['player']
        s = player['stat']
        team = p.get('currentTeam', {}).get('name', 'N/A')

        if team not in pitcher_map:
            continue

        pitcher = pitcher_map[team]
        meta = game_meta[team]
        venue = meta['venue']
        is_home = meta['is_home']
        is_night = meta['is_night']

        gp = int(s.get('gamesPlayed', 0))
        hrs = int(s.get('homeRuns', 0))
        hr_rate = hrs / gp if gp > 0 else 0
        hr_prob = hr_rate * 10000

        # Batter vs Pitcher using statcast
        matchup_note = "No Statcast matchup"
        try:
            matchup_df = statcast_batter_pitcher(start_dt="2024-03-01", end_dt=today, batter=p['id'], pitcher=pitcher['id'])
            if not matchup_df.empty:
                ab = len(matchup_df)
                hr = matchup_df['events'].fillna('').str.count('home_run').sum()
                hits = matchup_df['events'].fillna('').str.contains('single|double|triple|home_run').sum()
                matchup_note = f"{ab} AB, {int(hits)} H, {int(hr)} HR vs {pitcher['fullName']}"
                if hr > 0:
                    hr_prob *= 1.05
        except:
            matchup_note = "Matchup data unavailable"

        results.append({
            "Player": p['fullName'],
            "Team": team,
            "HRs": hrs,
            "AVG": s.get('avg', 'N/A'),
            "OPS": s.get('ops', 'N/A'),
            "Pitcher": pitcher['fullName'],
            "Matchup": matchup_note,
            "Location": "Home" if is_home else "Away",
            "Time": "Night" if is_night else "Day",
            "Venue": venue,
            "HR Chance": f"{round(hr_prob, 1)}%"
        })

    return pd.DataFrame(results).sort_values(by="HR Chance", ascending=False)

# === MAIN ===
df = fetch_data()

if df.empty:
    st.warning("No confirmed matchups available. Please check back later.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
