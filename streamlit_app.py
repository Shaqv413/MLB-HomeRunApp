import streamlit as st
import pandas as pd
from pybaseball import batting_stats, playerid_reverse_lookup, statcast_batter
from datetime import datetime

st.set_page_config(page_title="MLB HR Predictor (2025)", layout="wide")
st.title("MLB Home Run Predictor with Days Since Last HR")
st.markdown(f"**Date:** {datetime.now().date()}")

@st.cache_data
def fetch_top_hitters():
    df = batting_stats(2025)
    df = df.sort_values("HR", ascending=False).head(25)
    return df[["Name", "Team", "HR", "AB", "AVG"]]

@st.cache_data
def get_days_since_last_hr(player_name):
    try:
        # Use reverse lookup (last name only match) for better accuracy
        last_name = player_name.split()[-1]
        matches = playerid_reverse_lookup()
        matched = matches[matches["name_last"] == last_name]

        if matched.empty:
            return "N/A"

        player_id = matched.iloc[0]["key_mlbam"]
        logs = statcast_batter("2025-03-01", datetime.today().strftime("%Y-%m-%d"), player_id)

        hr_logs = logs[logs["events"] == "home_run"]
        if hr_logs.empty:
            return "N/A"

        last_hr_date = pd.to_datetime(hr_logs.iloc[-1]["game_date"])
        return (datetime.today() - last_hr_date).days
    except Exception as e:
        return "N/A"

# Load base stats
df = fetch_top_hitters()

# Calculate probability
df["AB/HR"] = (df["AB"] / df["HR"]).replace([float("inf"), 0], 999)
df["HR Chance"] = round((1 / df["AB/HR"]) * 100, 2).astype(str) + "%"

# Calculate days since last HR
days_since = []
with st.spinner("Calculating Days Since Last HR..."):
    for player in df["Name"]:
        days = get_days_since_last_hr(player)
        days_since.append(days)

df["Days Since Last HR"] = days_since

# Show data
st.dataframe(df.reset_index(drop=True), use_container_width=True)
