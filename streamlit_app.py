import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

today = datetime.now().strftime("%Y-%m-%d")

# Ballpark Home Run Factors
park_factors = {
    "Coors Field": 120,
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
    "Angel Stadium": 102,
    "Busch Stadium": 95,
    "Tropicana Field": 90,
    "Citi Field": 93,
    "PNC Park": 95,
    "T-Mobile Park": 94,
    "Minute Maid Park": 109,
    "American Family Field": 104,
    "Target Field": 98,
    "Rogers Centre": 106,
    "Comerica Park": 92,
    "Chase Field": 103,
    "Kauffman Stadium": 94,
    "Guaranteed Rate Field": 105,
    "Nationals Park": 99,
    "Progressive Field": 95,
    "Oakland Coliseum": 86
}

@st.cache_data(show_spinner=False)
def fetch_data():
    results = []
