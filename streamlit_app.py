import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from pybaseball import statcast_batter, batting_stats_range

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown("#### Date: {}".format(datetime.today().strftime("%Y-%m-%d")))

# ----------------------------
# Ballpark HR Boost Factors
# ----------------------------
ballpark_factors = {
    "Coors Field": 1.20,
    "Yankee Stadium": 1.10,
    "Great American Ball Park": 1.12,
    "Dodger Stadium": 1.05,
    "Globe Life Field": 1.04,
    "Fenway Park": 1.08,
    "Wrigley Field": 1.07,
    "Oracle Park": 0.85,
    "Petco Park": 0.91,
    "LoanDepot Park": 0.89,
    "T-Mobile Park": 0.95,
    "Citi Field": 0.92,
    "PNC Park": 0.88,
}

# ----------------------------
# Game Schedule → Stadium Mapping
# ----------------------------
@st.cache_data(show_spinner=False)
def get_today_venues():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    res = requests.get(url).json()

    team_venue_map = {}
    for date in res.get("dates", []):
        for game in date.get("games", []):
            venue = game.get("venue", {}).get("name")
            home = game.get("teams", {}).get("home", {}).get("team", {}).get("name")
            away = game.get("teams", {}).get("away", {}).get("team", {}).get("name")
            if venue:
                if home:
                    team_venue_map[home] = venue
                if away:
                    team_venue_map[away] = venue
    return team_venue_map

# ----------------------------
# Caching Historical Season Data
# ----------------------------
@st.cache_data(show_spinner=False)
def load_historical_ab_hr():
    data_2023 = batting_stats_range("2023-03-01", "2023-11-01")
    data_2023["Season"] = "2023"
    data_2024 = batting_stats_range("2024-03-01", "2024-11-01")
    data_2024["Season"] = "2024"
    return pd.concat([data_2023, data_2024], ignore_index=True)

@st.cache_data(show_spinner=False)
def load_current_season_ab_hr():
    end = datetime.today().strftime('%Y-%m-%d')
    data_2025 = batting_stats_range("2025-03-01", end)
    data_2025["Season"] = "2025"
    return data_2025

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

# ----------------------------
# Recency Boost Based on Last 7 Days
# ----------------------------
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

# ----------------------------
# Weighted HR Rate Formula (2023–2025)
# ----------------------------
def calculate_weighted_hr_rate(name, combined_df):
    weights = {"2023": 0.1, "2024": 0.3, "2025": 0.6}
    total_ab = 0
    total_hr = 0
    for season in weights:
        row = combined_df[(combined_df["Name"] == name) & (combined_df["Season"] == season)]
        if not row.empty:
            ab = int(row["AB"].values[0])
            hr = int(row["HR"].values[0])
            total_ab += ab * weights[season]
            total_hr += hr * weights[season]
    if total_hr > 0:
        ab_per_hr = round(total_ab / total_hr, 2)
        hr_rate = round(1 / ab_per_hr, 4)
        return ab_per_hr, hr_rate
    else:
        return "N/A", 0.0

# ----------------------------
# Final App Display
# ----------------------------
with st.spinner("Loading player data..."):
    season = datetime.today().year
    top_df = fetch_top_hitters(season)

    historical_df = load_historical_ab_hr()
    current_df = load_current_season_ab_hr()
    combined_stats = pd.concat([historical_df, current_df], ignore_index=True)

    venue_map = get_today_venues()

    results = []
    for _, row in top_df.iterrows():
        name = row['Player']
        pid = row['ID']
        team = row['Team']

        ab_hr, base_rate = calculate_weighted_hr_rate(name, combined_stats)
        boost = get_recent_hr_boost(pid)

        venue = venue_map.get(team, None)
        park_factor = ballpark_factors.get(venue, 1.00)

        final_chance = round(base_rate * (1 + boost) * park_factor * 100, 2)

        results.append({
            "Player": name,
            "Team": team,
            "Stadium": venue if venue else "N/A",
            "HRs": row["HRs"],
            "HR Chance": f"{final_chance}%" if final_chance > 0 else "N/A"
        })

    st.dataframe(pd.DataFrame(results), use_container_width=True)
