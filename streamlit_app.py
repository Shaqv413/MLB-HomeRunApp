import streamlit as st
import pandas as pd
import datetime
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="MLB Home Run Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.date.today()}")

@st.cache_data(show_spinner="Loading player data...")
def fetch_data():
    try:
        url = "https://www.mlb.com/stats/home-runs/2025"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        # Find script tag that contains JSON-like player data
        scripts = soup.find_all("script")
        data_script = None
        for s in scripts:
            if "window.__INITIAL_STATE__" in s.text:
                data_script = s.text
                break

        if not data_script:
            raise ValueError("Player data script not found.")

        # Parse the JSON-like string
        json_str = data_script.split("window.__INITIAL_STATE__ = ")[1].split("};")[0] + "}"
        import json
        data_json = json.loads(json_str)

        # Navigate to player rows
        players_raw = data_json["stats"]["playerStats"]["leaders"]["hits"]
        if not players_raw:
            raise ValueError("No player data found.")

        # Extract top 50 hitters
        players = []
        for p in players_raw[:50]:
            name_team = p["playerName"]
            team = name_team.split("(")[-1].replace(")", "").strip() if "(" in name_team else "N/A"
            name = name_team.split("(")[0].strip()
            hr = p.get("value", 0)
            avg = p.get("avg", "N/A")
            players.append({
                "Player": name,
                "Team": team,
                "HRs": hr,
                "AVG": avg
            })

        df = pd.DataFrame(players)
        return df

    except Exception as e:
        st.error(f"Error processing data: {e}")
        return pd.DataFrame()

df = fetch_data()

if df.empty:
    st.warning("No data available.")
else:
    st.dataframe(df)
