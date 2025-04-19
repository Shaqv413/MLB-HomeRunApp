import streamlit as st
import pandas as pd
import requests
from pybaseball import batting_stats, playerid_reverse_lookup
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Predictor with Days Since Last HR")
st.markdown(f"**Date:** {datetime.today().date()}")

# ⚙️ Load Baseball-Reference ID lookup table
@st.cache_data
def generate_slug_table():
    return playerid_reverse_lookup()

# 🔁 Convert "First Last" to Baseball-Reference slug
def get_br_slug(name, slug_table):
    try:
        first, last = name.split(" ", 1)
        match = slug_table[
            (slug_table["name_first"].str.lower() == first.lower()) &
            (slug_table["name_last"].str.lower() == last.lower())
        ]
        if not match.empty:
            return match.iloc[0]["key_bbref"]
        return None
    except:
        return None

# 📅 Get Days Since Last HR from Baseball-Reference game log
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

# 📊 Load 2025 top HR hitters
@st.cache_data
def fetch_top_hitters():
    df = batting_stats(2025)
    df = df.sort_values("HR", ascending=False).head(25)
    df["AB/HR"] = (df["AB"] / df["HR"]).replace([float("inf"), 0], 999)
    df["HR Chance"] = round((1 / df["AB/HR"]) * 100, 2).astype(str) + "%"
    return df[["Name", "Team", "HR", "AB", "AVG", "AB/HR", "HR Chance"]]

# 🏁 Fetch and process data
df = fetch_top_hitters()
slug_table = generate_slug_table()

# 🔍 Calculate Days Since Last HR
days_list = []
with st.spinner("Calculating Days Since Last HR from Baseball-Reference..."):
    for name in df["Name"]:
        slug = get_br_slug(name, slug_table)
        if slug:
            days = get_days_since_last_hr(slug)
        else:
            days = "N/A"
        days_list.append(days)

df["Days Since Last HR"] = days_list

# 📋 Show final table
st.dataframe(df.reset_index(drop=True), use_container_width=True)
