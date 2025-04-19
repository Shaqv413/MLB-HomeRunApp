import streamlit as st
import pandas as pd
from pybaseball import batting_stats
from datetime import datetime

st.set_page_config(page_title="MLB Home Run Predictor", layout="wide")
st.title("MLB Home Run Predictor (2025)")
st.markdown(f"**Date:** {datetime.now().date()}")

@st.cache_data
def fetch_data():
    try:
        # Pull full 2025 batting stats
        df = batting_stats(2025)
        # Sort by home runs and select top 50
        df = df.sort_values("HR", ascending=False).head(50)
        # Calculate AB/HR safely
        df["AB/HR"] = (df["AB"] / df["HR"]).replace([float('inf'), 0], 999)
        # Estimate HR chance %
        df["HR Chance"] = round((1 / df["AB/HR"]) * 100, 2).astype(str) + "%"
        # Select relevant columns
        return df[["Name", "Team", "HR", "AB", "AVG", "AB/HR", "HR Chance"]]
    except Exception as e:
        st.error(f"Failed to load 2025 data: {e}")
        return pd.DataFrame()

df = fetch_data()

if df.empty:
    st.warning("No 2025 player data available.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
