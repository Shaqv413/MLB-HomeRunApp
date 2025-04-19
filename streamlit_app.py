import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MLB Home Run Probability Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown("**Date:** {}".format(datetime.now().strftime("%Y-%m-%d")))

@st.cache_data
def fetch_data():
    try:
        url = "https://www.mlb.com/stats/home-runs/2025"
        tables = pd.read_html(url)
        df = tables[0]
    except Exception as e:
        st.error(f"Failed to load batting stats: {e}")
        return pd.DataFrame()

    try:
        df["Team"] = df["Name"].str.extract(r"\((\w{2,3})\)")
        df["Name"] = df["Name"].str.replace(r"\s*\(\w{2,3}\)", "", regex=True)
        df = df.rename(columns={"Name": "Player"})
        df = df.head(50)
        df["HR Chance"] = df["HR"].astype(float) / df["AB"].astype(float)
        df["HR Chance"] = (df["HR Chance"] * 100).round(1).astype(str) + "%"
        return df
    except Exception as e:
        st.error(f"Error processing data: {e}")
        return pd.DataFrame()

df = fetch_data()

if df.empty:
    st.warning("No data available.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
