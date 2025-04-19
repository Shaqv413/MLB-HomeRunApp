import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Predictor with Days Since Last HR (via Baseball-Reference)")
st.markdown(f"**Date:** {datetime.today().date()}")

# Map: Player Name → Baseball-Reference slug
slugs = {
    "Aaron Judge": "judgeaa01",
    "Shohei Ohtani": "ohtansh01",
    "Mookie Betts": "bettsmo01",
    "Juan Soto": "sotoju01",
    "Matt Olson": "olsonma01"
}

# Function to get "Days Since Last HR" from Baseball-Reference
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

# Build dataset
results = []
with st.spinner("Fetching Days Since Last HR..."):
    for name, slug in slugs.items():
        days = get_days_since_last_hr(slug)
        results.append({"Player": name, "Days Since Last HR": days})

df = pd.DataFrame(results)
st.dataframe(df, use_container_width=True)
