import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from pybaseball import playerid_lookup, statcast_batter

st.set_page_config(page_title="MLB HR Predictor", layout="wide")
st.title("MLB Home Run Probability Predictor")
st.markdown("**Date:** " + str(datetime.today().date()))

# Ballpark Factors (sample values)
park_factors = {
    "Yankee Stadium": 110,
    "Fenway Park": 108,
    "Dodger Stadium": 104,
    "Coors Field": 125,
    "Oracle Park": 85
}

# Get today's probable pitchers
def get_probable_pitchers():
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1, "date": datetime.today().strftime('%Y-%m-%d')}
    data = requests.get(url, params=params).json()
    matchups = {}
    for date in data.get("dates", []):
        for game in date.get("games", []):
            teams = game["teams"]
            away = teams["away"]
            home = teams["home"]
            venue = game["venue"]["name"]
            time = game["gameDate"][11:16]
            if "probablePitcher" in away:
                matchups[home["team"]["name"]] = {
                    "pitcher": away["probablePitcher"]["fullName"],
                    "pitcher_id": away["probablePitcher"]["id"],
                    "venue": venue,
                    "time": time
                }
            if "probablePitcher" in home:
                matchups[away["team"]["name"]] = {
                    "pitcher": home["probablePitcher"]["fullName"],
                    "pitcher_id": home["probablePitcher"]["id"],
                    "venue": venue,
                    "time": time
                }
    return matchups

# Get top 100 HR hitters
def get_top_hitters():
    url = "https://statsapi.mlb.com/api/v1/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": datetime.today().year,
        "limit": 100,
        "sortStat": "homeRuns"
    }
    data = requests.get(url, params=params).json()
    players = []
    for item in data["stats"][0]["splits"]:
        p = item["player"]
        stats = item["stat"]
        players.append({
            "Name": p["fullName"],
            "ID": p["id"],
            "Team": p.get("currentTeam", {}).get("name", "N/A"),
            "HR": stats.get("homeRuns", 0),
            "AVG": stats.get("avg", "N/A"),
            "OPS": stats.get("ops", "N/A")
        })
    return players

# Get batter vs pitcher statcast data
def get_h2h(batter_id, pitcher_id):
    try:
        df = statcast_batter('2023-01-01', '2024-12-31', batter_id)
        df_vs = df[df["pitcher"] == pitcher_id]
        ab = len(df_vs)
        hits = len(df_vs[df_vs["events"].isin(["single", "double", "triple", "home_run"])])
        hrs = len(df_vs[df_vs["events"] == "home_run"])
        avg = round(hits / ab, 3) if ab > 0 else "N/A"
        return ab, hits, hrs, avg
    except:
        return "N/A", "N/A", "N/A", "N/A"

# Combine all data
def build_table():
    matchups = get_probable_pitchers()
    players = get_top_hitters()
    rows = []

    for p in players:
        team = p["Team"]
        opp = matchups.get(team, {})
        pitcher = opp.get("pitcher", "N/A")
        pid = opp.get("pitcher_id")
        park = opp.get("venue", "N/A")
        time = opp.get("time", "N/A")
        pf = park_factors.get(park, "N/A")

        ab, hits, hr_vs, avg_vs = get_h2h(p["ID"], pid) if pid else ("N/A", "N/A", "N/A", "N/A")

        rows.append({
            "Player": p["Name"],
            "Team": team,
            "HRs": p["HR"],
            "AVG": p["AVG"],
            "OPS": p["OPS"],
            "Pitcher": pitcher,
            "AB vs P": ab,
            "Hits": hits,
            "HR vs P": hr_vs,
            "BA vs P": avg_vs,
            "Location": park,
            "Time": time,
            "Park Factor": pf
        })

    return pd.DataFrame(rows)

# Main render
with st.spinner("Gathering today’s stats…"):
    df = build_table()

if df.empty:
    st.warning("No confirmed matchups available. Please check back later.")
else:
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
