import streamlit as st
from gemini import generate_myth
from evaluation import evaluate_response
import json
import sqlite3
import random
from setup_db import setup_db
from setup_leaderboard import setup_leaderboard, update_leaderboard

st.set_page_config(page_title="♻️ Sustainability Myth-Busting Chatbot", page_icon="🌱")

# --- Setup Databases ---
setup_db()
setup_leaderboard()

# --- Session State Initialization ---
for key in ["messages", "myth", "score", "level", "badges", "user"]:
    if key not in st.session_state:
        if key in ["messages", "badges"]:
            st.session_state[key] = []
        elif key == "score":
            st.session_state[key] = 0
        elif key == "level":
            st.session_state[key] = 1
        else:
            st.session_state[key] = None

# --- Login/Register Functions ---
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

# --- Login/Register Page ---
if not st.session_state.user:
    st.title("🔐 Login or Register")
    choice = st.radio("Choose an option:", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Login" and st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.user = username
            st.success(f"Welcome back, {username}! 🌱")
        else:
            st.error("Invalid username or password.")
    elif choice == "Register" and st.button("Register"):
        success = register_user(username, password)
        if success:
            st.success("Account created! Please log in.")
        else:
            st.error("Username already exists.")
    st.stop()

# --- Helper Functions ---
themes = ["Energy Myths", "Recycling Myths", "Water Myths", "Transport Myths"]
def get_current_theme():
    return themes[(st.session_state.level - 1) % len(themes)]

predefined_myths = [
    "Recycling plastic always saves the environment.",
    "Electric cars are worse than gasoline cars.",
    "Turning off lights at night barely saves energy."
]

def safe_generate_myth():
    current_theme = get_current_theme()
    try:
        return generate_myth(theme=current_theme)
    except Exception:
        return random.choice(predefined_myths)

def render_stars(score, max_score=5):
    return "⭐" * score + "☆" * (max_score - score)

# --- Tabs ---
tab_game, tab_leaderboard = st.tabs(["Game", "Leaderboard"])

# --- Game Tab ---
with tab_game:
    st.title("♻️ Sustainability Myth-Busting Chatbot")

    # Generate myth if none exists
    if st.session_state.myth is None:
        st.session_state.myth = safe_generate_myth()
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Here’s a sustainability myth for you to bust:\n\n**{st.session_state.myth}**"
        })

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Sidebar: Progress
    st.sidebar.header("🏅 Your Progress")
    st.sidebar.metric("Total Score", st.session_state.score)
    max_score = st.session_state.level * 50
    st.sidebar.progress(min(st.session_state.score / max_score, 1.0))
    st.sidebar.write(f"Level: {st.session_state.level}")
    st.sidebar.write(f"🌿 Current Theme: {get_current_theme()}")
    st.sidebar.write(f"🔮 Next Theme Unlock: {themes[st.session_state.level % len(themes)]}")
    if st.session_state.badges:
        st.sidebar.write("🎖️ Badges Earned:")
        for badge in st.session_state.badges:
            st.sidebar.markdown(f"- {badge}")

    # --- User Input ---
    if user_input := st.chat_input("Correct the myth with evidence..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Evaluate response
        try:
            eval_result = evaluate_response(user_input, st.session_state.myth)
            if isinstance(eval_result, str):
                eval_result = json.loads(eval_result)
        except Exception:
            eval_result = {
                "correctness": False, "clarity": 0, "tone": 0, "evidence": 0,
                "points": 0, "badge": "Myth Apprentice", "level_up": False,
                "feedback": "Error evaluating. Try rephrasing your answer."
            }

        # Citation tip
        if "according to" not in user_input.lower() and eval_result['evidence'] > 2:
            eval_result['feedback'] += " Tip: Cite a source like UNEP, IPCC, or a scientific study."

        # Update score, level, badges
        st.session_state.score += eval_result.get("points", 0)
        if eval_result.get("level_up"):
            st.session_state.level += 1
        if eval_result.get("badge") and eval_result["badge"] not in st.session_state.badges:
            st.session_state.badges.append(eval_result["badge"])

        # Render evaluation message
        clarity_stars = render_stars(eval_result['clarity'])
        tone_stars = render_stars(eval_result['tone'])
        evidence_stars = render_stars(eval_result['evidence'])

        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                f"📝 **Evaluation**\n\n"
                f"- ✅ Correctness: {eval_result['correctness']}\n"
                f"- ✨ Clarity: {clarity_stars}\n"
                f"- 🤝 Tone: {tone_stars}\n"
                f"- 📚 Evidence: {evidence_stars}\n"
                f"- 🏆 Points Earned: {eval_result.get('points',0)}\n"
                f"- 🎖️ Badge: {eval_result['badge']}\n"
                f"- 🚀 Level Up: {eval_result['level_up']}\n"
                f"- 💡 Feedback: {eval_result['feedback']}\n\n"
                f"**Total Score: {st.session_state.score}**"
            )
        })

        # Update leaderboard
        update_leaderboard(st.session_state.user, st.session_state.score, st.session_state.badges)

        # Generate next myth
        st.session_state.myth = safe_generate_myth()
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Here’s your next myth:\n\n**{st.session_state.myth}**"
        })

# --- Leaderboard Tab ---
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
