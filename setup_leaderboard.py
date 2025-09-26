import sqlite3

def setup_leaderboard():
    conn = sqlite3.connect("leaderboard.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            username TEXT PRIMARY KEY,
            score INTEGER,
            badges TEXT
        )
    """)
    conn.commit()
    conn.close()

def update_leaderboard(username, score, badges):
    badges_str = ",".join(badges)  # convert list to a string
    conn = sqlite3.connect("leaderboard.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO leaderboard (username, score, badges)
        VALUES (?, ?, ?)
    """, (username, score, badges_str))
    conn.commit()
    conn.close()
