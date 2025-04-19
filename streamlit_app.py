import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.now().date()}")

# Ballpark HR Factors (100 is neutral)
park_factors = {
    "Coors Field": 115,
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
    "Truist Park": 97,
    "Minute Maid Park": 99,
    "Citi Field": 94,
    "T-Mobile Park": 96,
    "Chase Field": 107,
    "Comerica Park": 92,
    "American Family Field": 106,
    "Target Field": 98,
    "Kauffman Stadium": 95,
    "Busch Stadium": 93,
    "Oakland Coliseum": 86,
    "Rogers Centre": 103,
    "Tropicana Field": 90,
    "Nationals Park": 100,
    "Progressive Field": 99,
    "Guaranteed Rate Field": 102,
    "Angel Stadium": 101,
    "PNC Park": 97
}

@st.cache_data(ttl=3600)
def fetch_data():
    stats_url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": "2025",
        "limit": 50,  # faster load
        "sortStat": "homeRuns"
    }

    response = requests.get(stats_url, params=params)
    data = response.json()

    results = []
    players = data.get("stats", [{}])[0].get("splits", [])

    for player in players:
        info = player.get("player", {})
        stats = player.get("stat", {})
        team_info = info.get("currentTeam", {}).get("name", "N/A")
        venue = player.get("team", {}).get("venue", {}).get("name", "N/A")

        hr = int(stats.get("homeRuns", 0))
        avg = stats.get("avg", "N/A")
        ab = int(stats.get("atBats", 0))
        ab_per_hr = round(ab / hr, 1) if hr > 0 else None

        park = venue
        park_factor = park_factors.get(park, 100)

        if ab_per_hr:
            hr_prob = round((1 / ab_per_hr) * (park_factor / 100) * 100, 1)
        else:
            hr_prob = None

        results.append({
            "Player": info.get("fullName", "N/A"),
            "Team": team_info,
            "HRs": hr,
            "AVG": avg,
            "AB/HR (2025)": ab_per_hr if ab_per_hr else "N/A",
            "Park": park,
            "Park Factor": park_factor,
            "HR Chance": hr_prob
        })

    df = pd.DataFrame(results)

    if not df.empty and "HR Chance" in df.columns:
        df = df.dropna(subset=["HR Chance"])
        df = df.sort_values(by="HR Chance", ascending=False)
        df["HR Chance"] = df["HR Chance"].astype(str) + "%"

    return df

# Load and show
df = fetch_data()

if df.empty:
    st.warning("No data available. Please try again later.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
