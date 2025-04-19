import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.now().date()}")

# Full 2025 ballpark HR factors
park_factors = {
    "Angel Stadium": 198,
    "Yankee Stadium": 198,
    "American Family Field": 180,
    "Great American Ball Park": 176,
    "Globe Life Field": 166,
    "Petco Park": 150,
    "Nationals Park": 129,
    "Citizens Bank Park": 125,
    "Comerica Park": 115,
    "Guaranteed Rate Field": 114,
    "Minute Maid Park": 102,
    "T-Mobile Park": 102,
    "Oracle Park": 101,
    "Wrigley Field": 98,
    "Coors Field": 95,
    "Dodger Stadium": 95,
    "Busch Stadium": 94,
    "Truist Park": 93,
    "Camden Yards": 90,
    "Fenway Park": 86,
    "Kauffman Stadium": 83,
    "Rogers Centre": 83,
    "Target Field": 74,
    "loanDepot Park": 71,
    "Chase Field": 70,
    "PNC Park": 69,
    "Citi Field": 63,
    "Progressive Field": 61,
    "George M. Steinbrenner Field": 104,  # Temporary Rays home
    "Sutter Health Park": 89              # Temporary A's home
}

@st.cache_data(ttl=3600)
def fetch_data():
    url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": "2025",
        "limit": 50,
        "sortStat": "homeRuns"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Failed to fetch player data: {e}")
        return pd.DataFrame()

    players = data.get("stats", [{}])[0].get("splits", [])
    results = []

    for player in players:
        info = player.get("player", {})
        stats = player.get("stat", {})
        team = info.get("currentTeam", {}).get("name", "N/A")
        venue = player.get("team", {}).get("venue", {}).get("name", "N/A")

        hr = int(stats.get("homeRuns", 0))
        ab = int(stats.get("atBats", 0))
        avg = stats.get("avg", "N/A")
        ab_per_hr = round(ab / hr, 1) if hr > 0 else None

        park = venue
        park_factor = park_factors.get(park, 100)

        if ab_per_hr:
            hr_prob = round((1 / ab_per_hr) * (park_factor / 100) * 100, 1)
        else:
            hr_prob = None

        results.append({
            "Player": info.get("fullName", "N/A"),
            "Team": team,
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
        df["HR Chance"] = df["HR Chance"].astype(float).round(1).astype(str) + "%"

    return df

# Show table
with st.spinner("Loading player data..."):
    df = fetch_data()

if df.empty:
    st.warning("No data available right now. Try again soon.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
