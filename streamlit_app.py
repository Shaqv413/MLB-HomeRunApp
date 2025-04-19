import streamlit as st
import pandas as pd
import requests
from pybaseball import batting_stats, playerid_lookup
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Predictor with Days Since Last HR")
st.write("Date:", datetime.today().date())

# Step 1: Pull 2025 top home run hitters from pybaseball
@st.cache_data(ttl=3600)
def fetch_top_hitters():
    df = batting_stats(2025)
    df = df.sort_values("HR", ascending=False).head(25)
    df = df[["Name", "Team", "HR", "AB", "AVG"]]
    df["AB/HR"] = (df["AB"] / df["HR"]).replace([float("inf"), -float("inf")], None)
    league_avg = df["AB/HR"].mean(skipna=True)
    df["HR Chance"] = ((1 / df["AB/HR"]) / (1 / league_avg)) * 100
    df["HR Chance"] = df["HR Chance"].fillna(0).round(1)
    return df

# Step 2: Use pybaseball to get the Baseball-Reference slug (key_bbref)
def get_br_slug(name):
    try:
        first, last = name.split(" ", 1)
        result = playerid_lookup(last, first)
        if not result.empty:
            return result.iloc[0]["key_bbref"]
        else:
            return None
    except:
        return None

# Step 3: Scrape Baseball-Reference game log to get last HR date
def get_days_since_last_hr(slug):
    try:
        url = f"https://www.baseball-reference.com/players/gl.fcgi?id={slug}&t=b&year=2025"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
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

# Execute the pipeline
df = fetch_top_hitters()

if df.empty:
    st.warning("No data available.")
else:
    st.markdown("**Calculating Days Since Last HR (via Baseball-Reference)...**")
    days_list = []

    for name in df["Name"]:
        slug = get_br_slug(name)
        days = get_days_since_last_hr(slug) if slug else "N/A"
        days_list.append(days)

    df["Days Since Last HR"] = days_list

    st.dataframe(df.reset_index(drop=True), use_container_width=True)
