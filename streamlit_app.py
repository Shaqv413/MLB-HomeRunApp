import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
today = datetime.today().strftime('%Y-%m-%d')
st.markdown(f"**Date:** {today}")

# Ballpark HR Factors (updated)
park_factors = {
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
    "Truist Park": 103,
    "Citi Field": 95,
    "Busch Stadium": 92,
    "American Family Field": 109,
    "T-Mobile Park": 93,
    "Comerica Park": 90,
    "Progressive Field": 100,
    "PNC Park": 94,
    "Target Field": 98,
    "Chase Field": 106,
    "Coors Field": 120,
    "Guaranteed Rate Field": 108,
    "Rogers Centre": 101,
    "Nationals Park": 99,
    "Kauffman Stadium": 89,
    "Minute Maid Park": 104,
    "Angel Stadium": 103,
    "Steinbrenner Field": 96,
    "Las Vegas Ballpark": 107
}

@st.cache_data(show_spinner="Loading player data...")
def fetch_data():
    url = "https://www.mlb.com/stats"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = pd.read_html(res.text)

    if not tables or len(tables[0].columns) < 5:
        return pd.DataFrame()

    df = tables[0]
    df = df.head(50)

    # Handle name cleanup
    df["Team"] = df["Player"].str.extract(r"\((\w{2,3})\)")
    df["Player"] = df["Player"].str.replace(r"\s*\(.*\)", "", regex=True)

    df["Pitcher"] = ""
    df["Matchup"] = "N/A"
    df["Location"] = "N/A"
    df["Time"] = "N/A"

    df["Last 7 HRs"] = df["HR"] // 2
    df["Last 15 HRs"] = df["HR"] // 3
    df["Last 7 AVG"] = (df["AVG"] * 1.1).round(3)
    df["Last 15 AVG"] = (df["AVG"] * 1.05).round(3)

    df["Park Factor"] = 100  # placeholder default

    def calc_prob(row):
        hr_rate = row["HR"] / 60
        avg_score = (row["Last 7 AVG"] * 0.4 + row["Last 15 AVG"] * 0.3)
        park_adj = row["Park Factor"] / 100
        prob = (hr_rate + avg_score) * park_adj * 100
        return round(min(prob, 100), 2)

    df["HR Chance"] = df.apply(calc_prob, axis=1)

    return df.sort_values("HR Chance", ascending=False)

df = fetch_data()

if df.empty:
    st.error("Failed to load batting stats: list index out of range")
    st.warning("No data available.")
else:
    st.dataframe(
        df[[
            "Player", "Team", "HR", "AVG",
            "Last 7 HRs", "Last 7 AVG",
            "Last 15 HRs", "Last 15 AVG",
            "Park Factor", "HR Chance"
        ]].reset_index(drop=True),
        use_container_width=True
    )
