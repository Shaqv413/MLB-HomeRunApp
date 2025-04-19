import streamlit as st
import pandas as pd
from datetime import datetime
from pybaseball import batting_stats_range

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.now().date()}")

# Updated 2025 Ballpark HR Factors (for future use if needed)
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
    "George M. Steinbrenner Field": 104,
    "Sutter Health Park": 89
}

@st.cache_data(ttl=3600)
def fetch_data():
    start_date = "2025-03-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    try:
        data = batting_stats_range(start_date, end_date)
    except Exception as e:
        st.error(f"Failed to load batting stats: {e}")
        return pd.DataFrame()

    data = data.sort_values(by="HR", ascending=False).head(50)
    results = []

    for _, row in data.iterrows():
        player = row["Name"]
        hr = int(row["HR"])
        ab = int(row["AB"])
        avg = row["AVG"]
        team = row["Team"]
        ab_per_hr = round(ab / hr, 1) if hr > 0 else None

        # No venue info in pybaseball — default to neutral
        park = "Unknown"
        park_factor = 100

        if ab_per_hr:
            hr_prob = round((1 / ab_per_hr) * (park_factor / 100) * 100, 1)
        else:
            hr_prob = None

        results.append({
            "Player": player,
            "Team": team,
            "HRs": hr,
            "AVG": avg,
            "AB": ab,
            "AB/HR (2025)": ab_per_hr if ab_per_hr else "N/A",
            "Park": park,
            "Park Factor": park_factor,
            "HR Chance": hr_prob
        })

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.dropna(subset=["HR Chance"])
        df = df.sort_values(by="HR Chance", ascending=False)
        df["HR Chance"] = df["HR Chance"].astype(float).round(1).astype(str) + "%"

    return df

# Display app
with st.spinner("Loading player data..."):
    df = fetch_data()

if df.empty:
    st.warning("No data available.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
