import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
today = datetime.today().strftime('%Y-%m-%d')
st.markdown(f"**Date:** {today}")

# Ballpark HR Factors (2025 update)
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
    "Oakland Coliseum": 0,  # removed
    "Tropicana Field": 0,   # removed
    "Steinbrenner Field": 96,
    "Las Vegas Ballpark": 107  # New A's 2025
}

@st.cache_data(show_spinner="Loading player data...")
def fetch_data():
    url = "https://www.mlb.com/stats/"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find("table")
    df = pd.read_html(str(table))[0]

    df = df.head(50)
    df["Team"] = df["Player"].str.extract(r"\((\w{2,3})\)")  # Fallback if format includes team
    df["Player"] = df["Player"].str.replace(r"\s*\(.*\)", "", regex=True)

    # Simulate confirmed pitcher (for now — enhancement needed for live matchup)
    df["Pitcher"] = ""
    df["Matchup"] = "N/A"
    df["Location"] = "N/A"
    df["Time"] = "N/A"

    # Pull last 7/15 game stats
    df["Last 7 HRs"] = 0
    df["Last 7 AVG"] = 0.0
    df["Last 15 HRs"] = 0
    df["Last 15 AVG"] = 0.0

    # Simulated stat collection: in real deployment, you’d call an API or scrape game logs
    for i in range(len(df)):
        df.loc[i, "Last 7 HRs"] = int(df.loc[i, "HR"]) // 2
        df.loc[i, "Last 15 HRs"] = int(df.loc[i, "HR"]) // 3
        df.loc[i, "Last 7 AVG"] = round(float(df.loc[i, "AVG"]) * 1.1, 3)
        df.loc[i,
