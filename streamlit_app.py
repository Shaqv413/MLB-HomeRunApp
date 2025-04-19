import streamlit as st
import pandas as pd
import requests
from pybaseball import batting_stats
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Predictor with Days Since Last HR")
st.markdown(f"**Date:** {datetime.today().date()}")

# Manually mapped Baseball-Reference slugs for demo purposes
br_slugs = {
    "Aaron Judge": "judgeaa01",
    "Shohei Ohtani": "ohtansh01",
    "Mookie Betts": "bettsmo01",
    "Juan Soto": "sotoju01",
    "Matt Olson": "olsonma01"
}

# Function to scrape days since last HR from Baseball-Reference
def get_days_since_last_hr(br_slug):
    try:
        url = f"https://www.baseball-reference.com/players/gl.fcgi?id={br_slug}&t=b&year=2025"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "batting_gamelogs"})
        if not table:
            return "N/A"
        df = pd.read_html(str(table))[0]
        df = df[df["HR"] > 0]
        if df.empty:
            return "N/A"
        last_date = pd.to_datetime(df.iloc[-1]["Date"])
        return (datetime.today() - last_date).days
    except:
        return "N/A"

# Get top 25 HR hitters
@st.cache_data
def fetch_data():
    df = batting_stats(2025)
    df = df.sort_values("HR", ascending=False).head(25)
    df["AB/HR"] = (df["AB"] / df["HR"]).replace([float('inf'), 0], 999)
    df["HR Chance"] = round((1 / df["AB/HR"]) * 100, 2).astype(str) + "%"
    return df[["Name", "Team", "HR", "AB", "AVG", "AB/HR", "HR Chance"]]

df = fetch_data()

# Add "Days Since Last HR" if slug exists
days_since = []
with st.spinner("Fetching Days Since Last HR from Baseball-Reference..."):
    for name in df["Name"]:
        slug = br_slugs.get(name, None)
        if slug:
            days = get_days_since_last_hr(slug)
        else:
            days = "N/A"
        days_since.append(days)

df["Days Since Last HR"] = days_since

# Display the full table
st.dataframe(df.reset_index(drop=True), use_container_width=True)
