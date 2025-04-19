import streamlit as st
import pandas as pd
from pybaseball import batting_stats, playerid_lookup, statcast_batter
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
        # Lookup player ID
        name_parts = player_name.split(" ", 1)
        player_info = playerid_lookup(name_parts[0], name_parts[1]) if len(name_parts) == 2 else pd.DataFrame()
        if player_info.empty:
            return "N/A"
        player_id = player_info.iloc[0]["key_mlbam"]

        # Pull statcast data for 2025
        logs = statcast_batter(
            start_dt="2025-03-01",
            end_dt=datetime.today().strftime("%Y-%m-%d"),
            player_id=player_id
        )

        # Filter for HRs
        hr_logs = logs[logs["events"] == "home_run"]
        if hr_logs.empty:
            return "N/A"

        last_hr_date = pd.to_datetime(hr_logs.iloc[-1]["game_date"])
        days_since = (datetime.today() - last_hr_date).days
        return days_since
    except:
        return "N/A"

# Load data
df = fetch_top_hitters()

# Calculate AB/HR and HR Chance
df["AB/HR"] = (df["AB"] / df["HR"]).replace([float("inf"), 0], 999)
df["HR Chance"] = round((1 / df["AB/HR"]) * 100, 2).astype(str) + "%"

# Calculate Days Since Last HR
days_since_list = []
with st.spinner("Calculating Days Since Last HR..."):
    for name in df["Name"]:
        days = get_days_since_last_hr(name)
        days_since_list.append(days)

df["Days Since Last HR"] = days_since_list

# Display
st.dataframe(df.reset_index(drop=True), use_container_width=True)
