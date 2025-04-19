import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MLB Home Run Probability Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.today().strftime('%Y-%m-%d')}")

@st.cache_data(show_spinner="Loading player data...")
def fetch_data():
    # Simulated or test data structure to avoid real-time delays
    data = [
        {"Name": "Aaron Judge", "Team": "NYY", "HR": 5, "AVG": 0.310},
        {"Name": "Shohei Ohtani", "Team": "LAD", "HR": 3},
        {"Name": "Juan Soto", "HR": 4, "AVG": 0.280},
        {"Name": "Mookie Betts"},
    ]
    df = pd.DataFrame(data)

    results = []
    for _, row in df.iterrows():
        player = row.get("Name", "Unknown")
        team = row.get("Team", "N/A")
        hr = row.get("HR", 0)
        avg = row.get("AVG", 0.0)

        # Sample HR probability calculation
        hr_chance = round(min(0.3, hr * avg / 10) * 100, 1)

        results.append({
            "Player": player,
            "Team": team,
            "HRs": hr,
            "AVG": f"{avg:.3f}" if avg else "N/A",
            "HR Chance": f"{hr_chance}%"
        })

    df_final = pd.DataFrame(results)
    return df_final

df = fetch_data()

if df.empty:
    st.warning("No player data available.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
