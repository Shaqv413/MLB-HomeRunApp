import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

today = datetime.now().strftime("%Y-%m-%d")

# Ballpark Home Run Factors
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
    results = []
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
        home_team = game['teams']['home']['team']['name']
        away_team = game['teams']['away']['team']['name']
        venue = game['venue']['name']
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
        park_factor = park_factors.get(venue, 100)

        try:
            pitcher_stat = requests.get(
                f"https://statsapi.mlb.com/api/v1/people/{pitcher['id']}/stats?stats=season&group=pitching&season=2025"
            ).json()['stats'][0]['splits'][0]['stat']
            pitcher_hr_rate = int(pitcher_stat['homeRuns']) / float(pitcher_stat['inningsPitched'])
        except:
            continue

        gp = int(s.get('gamesPlayed', 0))
        hrs = int(s.get('homeRuns', 0))
        hr_rate = hrs / gp if gp > 0 else 0
        hr_prob = hr_rate * pitcher_hr_rate * 10000

        matchup_note = "No prior matchup"
        try:
            matchup = requests.get(
                f"https://statsapi.mlb.com/api/v1/people/{p['id']}/stats?stats=vsPlayer&opposingPlayerId={pitcher['id']}"
            ).json()['stats'][0]['splits'][0]['stat']
            ab = int(matchup['atBats'])
            hits = int(matchup['hits'])
            hrs_vs = int(matchup['homeRuns'])
            if hrs_vs > 0:
                hr_prob *= 1.05
            matchup_note = f"{ab} AB, {hits} H, {hrs_vs} HR vs {pitcher['fullName']}"
        except:
            pass

        try:
            split_data = requests.get(
                f"https://statsapi.mlb.com/api/v1/people/{p['id']}/stats?stats=seasonAdvancedSplits&group=hitting&season=2025"
            ).json()['stats'][0]['splits']
            splits = {s['split']['label']: s['stat'] for s in split_data}
            home = int(splits.get('Home', {}).get('homeRuns', 0))
            away = int(splits.get('Away', {}).get('homeRuns', 0))
            if is_home and home > away:
                hr_prob *= 1.05
            if not is_home and away > home:
                hr_prob *= 1.05
            night = int(splits.get('Night', {}).get('homeRuns', 0))
            day = int(splits.get('Day', {}).get('homeRuns', 0))
            if is_night and night > day:
                hr_prob *= 1.05
            if not is_night and day > night:
                hr_prob *= 1.05
        except:
            pass

        if park_factor > 105:
            hr_prob *= 1.05
        elif park_factor < 95:
            hr_prob *= 0.95

        try:
            recent = requests.get(
                f"https://statsapi.mlb.com/api/v1/people/{p['id']}/stats?stats=last7Days,last15Days&group=hitting&season=2025"
            ).json()['stats']
            for stat in recent:
                label = stat['type']['displayName']
                d = stat['splits'][0]['stat']
                g = int(d.get('gamesPlayed', 0))
                h = int(d.get('homeRuns', 0))
                rate = h / g if g > 0 else 0
                if label == "Last 7 Days" and rate > hr_rate:
                    hr_prob *= 1.05
                if label == "Last 15 Days" and rate > hr_rate:
                    hr_prob *= 1.03
        except:
            pass

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
            "Park Factor": f"{venue} ({park_factor})",
            "HR Chance": f"{round(hr_prob, 1)}%"
        })

    return pd.DataFrame(results).sort_values(by="HR Chance", ascending=False)

# MAIN DISPLAY LOGIC
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

# Always show the table — no matter what
st.dataframe(df.reset_index(drop=True), use_container_width=True)
