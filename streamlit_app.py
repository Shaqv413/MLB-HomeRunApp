import streamlit as st
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.write("Date:", date.today())

@st.cache_data(ttl=3600)
def fetch_top_hitters():
    url = "https://www.mlb.com/stats/home-runs"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        st.error("Failed to load batting stats: Table not found")
        return pd.DataFrame()

    headers = [th.text.strip() for th in table.find("thead").find_all("th")]
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = [td.text.strip() for td in tr.find_all("td")]
        rows.append(cells)

    df = pd.DataFrame(rows, columns=headers)

    # Rename columns for consistency
    df = df.rename(columns={
        "Player": "Name",
        "HR": "HR",
        "AVG": "AVG",
        "AB": "AB",
        "Team": "Team"
    })

    # Keep top 50 only
    df = df.head(50)

    # Convert necessary fields to numeric
    for col in ["HR", "AB", "AVG"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Calculate AB/HR
    df["AB/HR"] = df["AB"] / df["HR"]
    df["AB/HR"] = df["AB/HR"].replace([float("inf"), -float("inf")], None)

    # Estimate Home Run Chance using AB/HR
    league_avg_ab_hr = df["AB/HR"].mean(skipna=True)
    df["HR Chance"] = ((1 / df["AB/HR"]) / (1 / league_avg_ab_hr)) * 100
    df["HR Chance"] = df["HR Chance"].fillna(0).round(1)

    return df[["Name", "Team", "HR", "AB", "AVG", "AB/HR", "HR Chance"]]

try:
    df = fetch_top_hitters()
    if df.empty:
        st.warning("No data available.")
    else:
        st.dataframe(df.reset_index(drop=True), use_container_width=True)
except Exception as e:
    st.error(f"Error processing data: {e}")
    st.warning("No data available.")
