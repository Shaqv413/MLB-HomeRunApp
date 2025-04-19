import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Predictor with Days Since Last HR")
st.write("Date:", datetime.today().date())

# ⏳ Get the top HR hitters live from MLB.com
@st.cache_data(ttl=3600)
def fetch_top_hitters():
    url = "https://www.mlb.com/stats/home-runs"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table")

    if not table:
        return pd.DataFrame()

    try:
        df = pd.read_html(str(table))[0]
    except Exception:
        return pd.DataFrame()

    df = df.rename(columns={"Player": "Name"})
    df = df.head(25)

    for col in ["HR", "AB", "AVG"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["HR", "AB", "AVG"])
    df["AB/HR"] = df["AB"] / df["HR"]
    league_avg_ab_hr = df["AB/HR"].mean(skipna=True)
    df["HR Chance"] = ((1 / df["AB/HR"]) / (1 / league_avg_ab_hr)) * 100
    df["HR Chance"] = df["HR Chance"].fillna(0).round(1)

    return df[["Name", "Team", "HR", "AB", "AVG", "AB/HR", "HR Chance"]]

# 🔍 Build BR slugs from player name (first initial + 5 letters of last + 2 digit number)
def generate_br_slug(name):
    try:
        first, last = name.split(" ", 1)
        slug = (last[:5] + first[:2]).lower()
        return slug + "01"
    except:
        return None

# 📅 Get Days Since Last HR from BR game logs
def get_days_since_last_hr(br_slug):
    try:
        url = f"https://www.baseball-reference.com/players/gl.fcgi?id={br_slug}&t=b&year=2025"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", {"id": "batting_gamelogs"})
        if not table:
            return "N/A"

        df = pd.read_html(str(table))[0]
        df = df[df["HR"] > 0]
        if df.empty:
            return "N/A"

        last_hr_date = pd.to_datetime(df.iloc[-1]["Date"])
        return (datetime.today() - last_hr_date).days
    except:
        return "N/A"

# 🚀 Load data and calculate all stats
df = fetch_top_hitters()

if df.empty:
    st.warning("No data available.")
else:
    st.markdown("**Calculating Days Since Last HR...**")
    days_list = []

    for name in df["Name"]:
        slug = generate_br_slug(name)
        days = get_days_since_last_hr(slug) if slug else "N/A"
        days_list.append(days)

    df["Days Since Last HR"] = days_list
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
