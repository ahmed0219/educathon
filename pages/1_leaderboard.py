import streamlit as st
import sqlite3

st.set_page_config(page_title="🏆 Leaderboard", page_icon="🏆")
st.title("🏆 Sustainability Myth-Busting Leaderboard")

# Connect to leaderboard database
conn = sqlite3.connect("leaderboard.db")
c = conn.cursor()
c.execute("SELECT username, score, badges FROM leaderboard ORDER BY score DESC")
rows = c.fetchall()
conn.close()

# Display leaderboard
if rows:
    st.markdown("## Top Players")
    st.table([{"Username": r[0], "Score": r[1], "Badges": r[2]} for r in rows])
else:
    st.info("No leaderboard entries yet. Play the game to appear here!")
