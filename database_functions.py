import sqlite3
def register_user(username, password):    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username exists
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_score(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT score FROM users WHERE username=?", (username,))
    score = c.fetchone()
    conn.close()
    return score[0] if score else 0

def update_score(username, points):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET score = score + ? WHERE username=?", (points, username))
    conn.commit()
    conn.close()