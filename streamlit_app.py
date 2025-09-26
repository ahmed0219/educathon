import streamlit as st
import sqlite3
import json
import random
from gemini import generate_myth
from evaluation import evaluate_response
from setup_db import setup_db
from setup_leaderboard import setup_leaderboard, update_leaderboard

# ------------------ Page Config ------------------
st.set_page_config(page_title="♻️ Sustainability Myth-Busting Chatbot", page_icon="🌱")

# ------------------ Init DBs ------------------
setup_db()
setup_leaderboard()

# ------------------ Defaults ------------------
defaults = {
    "messages": [],
    "myth": None,
    "score": 0,
    "level": 1,
    "badges": [],
    "user": None,
    "pending_input": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------ Auth Helpers ------------------
def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def register_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# ------------------ Auth UI ------------------
if not st.session_state.user:
    st.title("🔐 Login or Register")
    choice = st.radio("Choose an option:", ["Login", "Register"])
    username = st.text_input("Username", key="auth_username")
    password = st.text_input("Password", type="password", key="auth_password")

    if choice == "Login":
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = username
                st.success(f"Welcome back, {username}! 🌱")
            else:
                st.error("Invalid username or password.")
    else:
        if st.button("Register"):
            success = register_user(username, password)
            if success:
                st.success("Account created! Please log in.")
            else:
                st.error("Username already exists.")
    st.stop()

# ------------------ Helpers ------------------
themes = ["Energy Myths", "Recycling Myths", "Water Myths", "Transport Myths"]

def get_current_theme():
    return themes[(st.session_state.level - 1) % len(themes)]

predefined_myths = [
    "Recycling plastic always saves the environment.",
    "Electric cars are worse than gasoline cars.",
    "Turning off lights at night barely saves energy.",
]

def safe_generate_myth():
    with st.spinner("Generating myth..."):
        try:
            return generate_myth(theme=get_current_theme())
        except Exception:
            return random.choice(predefined_myths)

def render_stars(score, max_score=5):
    score = int(score) if score is not None else 0
    score = max(0, min(max_score, score))
    return "⭐" * score + "☆" * (max_score - score)

def display_message(msg):
    role = msg["role"]
    if role == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
    elif role == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        st.markdown(f"**{role}:** {msg['content']}")

# ------------------ UI Tabs ------------------
tab_game, tab_leaderboard = st.tabs(["🎮 Game", "🏆 Leaderboard"])

# ------------------ Game Tab ------------------
with tab_game:
    st.title("♻️ ECOED Sustainability Myth-Busting Chatbot")

    # Generate first myth if needed
    if st.session_state.myth is None:
        st.session_state.myth = safe_generate_myth()
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Here’s a sustainability myth for you to bust:\n\n**{st.session_state.myth}**"
        })

    # ------------------ User input ------------------
    user_input = st.chat_input("💬 Bust the myth with evidence...")
    if user_input:
        st.session_state.pending_input = user_input

    # ------------------ Process pending input ------------------
    if st.session_state.pending_input:
        user_msg = st.session_state.pending_input
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_msg})

        # Evaluate
        try:
            eval_result = evaluate_response(user_msg, st.session_state.myth)
            if isinstance(eval_result, str):
                eval_result = json.loads(eval_result)
        except Exception:
            eval_result = {
                "correctness": False, "clarity": 0, "tone": 0, "evidence": 0,
                "points": 0, "badge": None, "level_up": False,
                "feedback": "⚠️ Error during evaluation. Try rephrasing your answer.",
            }

        # Evidence tip
        if "according to" not in user_msg.lower() and eval_result.get("evidence", 0) > 2:
            eval_result["feedback"] += " 💡 Tip: Cite a source like UNEP, IPCC, or a scientific study."

        # Update score/level/badges
        st.session_state.score += int(eval_result.get("points", 0))
        if eval_result.get("level_up"):
            st.session_state.level += 1
        badge = eval_result.get("badge")
        if badge and badge not in st.session_state.badges:
            st.session_state.badges.append(badge)

        # Prepare assistant message
        clarity_stars = render_stars(eval_result.get("clarity", 0))
        tone_stars = render_stars(eval_result.get("tone", 0))
        evidence_stars = render_stars(eval_result.get("evidence", 0))
        eval_text = (
            f"📝 **Evaluation**\n\n"
            f"- ✅ Correctness: {eval_result.get('correctness')}\n"
            f"- ✨ Clarity: {clarity_stars}\n"
            f"- 🤝 Tone: {tone_stars}\n"
            f"- 📚 Evidence: {evidence_stars}\n"
            f"- 🏆 Points Earned: {eval_result.get('points')}\n"
            f"- 🎖️ Badge: {badge}\n"
            f"- 🚀 Level Up: {eval_result.get('level_up')}\n"
            f"- 💡 Feedback: {eval_result.get('feedback')}\n\n"
            f"**Total Score: {st.session_state.score}**"
        )
        st.session_state.messages.append({"role": "assistant", "content": eval_text})

        # Update leaderboard
        update_leaderboard(st.session_state.user, st.session_state.score, st.session_state.badges)

        # Generate next myth
        st.session_state.myth = safe_generate_myth()
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Here’s your next myth:\n\n**{st.session_state.myth}**"
        })

        # Clear pending input
        st.session_state.pending_input = None

    # ------------------ Display chat history ------------------
    for msg in st.session_state.messages:
        display_message(msg)

    # ------------------ Sidebar ------------------
    st.sidebar.header("🏅 Your Progress")
    st.sidebar.metric("Total Score", st.session_state.score)
    max_score = st.session_state.level * 50
    st.sidebar.progress(min(st.session_state.score / max_score, 1.0))
    st.sidebar.write(f"Level: {st.session_state.level}")
    st.sidebar.write(f"🌿 Current Theme: {get_current_theme()}")
    st.sidebar.write(f"🔮 Next Theme Unlock: {themes[st.session_state.level % len(themes)]}")
    if st.session_state.badges:
        st.sidebar.write("🎖️ Badges Earned:")
        for b in st.session_state.badges:
            st.sidebar.markdown(f"- {b}")

# ------------------ Leaderboard Tab ------------------
with tab_leaderboard:
    st.title("🏆 Leaderboard")
    conn = sqlite3.connect("leaderboard.db")
    c = conn.cursor()
    c.execute("SELECT username, score, badges FROM leaderboard ORDER BY score DESC")
    rows = c.fetchall()
    conn.close()

    if rows:
        table_data = []
        for r in rows:
            badges_list = r[2].split(",") if r[2] else []
            table_data.append({"Username": r[0], "Score": r[1], "Badges": ", ".join(badges_list)})
        st.table(table_data)
    else:
        st.info("No leaderboard entries yet. Play the game to appear here!")
