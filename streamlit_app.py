import streamlit as st
from gemini import generate_myth
from evaluation import evaluate_response
import json
import sqlite3
from setup_db import setup_db
import random

st.set_page_config(page_title="♻️ Sustainability Myth-Busting Chatbot", page_icon="🌱")
st.title("♻️ Sustainability Myth-Busting Chatbot")
setup_db()

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "myth" not in st.session_state:
    st.session_state.myth = None
if "score" not in st.session_state:
    st.session_state.score = 0
if "level" not in st.session_state:
    st.session_state.level = 1
if "badges" not in st.session_state:
    st.session_state.badges = []
if "user" not in st.session_state:
    st.session_state.user = None

themes = ["Energy Myths", "Recycling Myths", "Water Myths", "Transport Myths"]
predefined_myths = [
    "Recycling plastic always saves the environment.",
    "Electric cars are worse than gasoline cars.",
    "Turning off lights at night barely saves energy."
]

# --- Login / Register ---
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
            st.rerun()
        else:
            st.error("Invalid username or password.")
    elif choice == "Register" and st.button("Register"):
        success = register_user(username, password)
        if success:
            st.success("Account created! Please log in.")
        else:
            st.error("Username already exists.")
    st.stop()

# --- Determine current theme based on level ---
def get_current_theme():
    return themes[(st.session_state.level - 1) % len(themes)]

# --- Safe myth generator ---
def safe_generate_myth():
    current_theme = get_current_theme()
    try:
        return generate_myth(theme=current_theme)
    except Exception:
        return random.choice(predefined_myths)

# --- Generate first myth ---
if st.session_state.myth is None:
    st.session_state.myth = safe_generate_myth()
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Here’s a sustainability myth for you to bust:\n\n**{st.session_state.myth}**"
    })

# --- Helper: Render Stars ---
def render_stars(score, max_score=5):
    return "⭐" * score + "☆" * (max_score - score)

# --- Chat History Display ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Scoreboard / Progress Bar ---
current_theme = get_current_theme()
st.sidebar.header("🏅 Your Progress")
st.sidebar.metric("Total Score", st.session_state.score)
max_score = st.session_state.level * 50  # each level needs 50 points
st.sidebar.progress(min(st.session_state.score / max_score, 1.0))
st.sidebar.write(f"Level: {st.session_state.level}")
st.sidebar.write(f"🌿 Current Theme: {current_theme}")
st.sidebar.write(f"🔮 Next Theme Unlock: {themes[st.session_state.level % len(themes)]}")

if st.session_state.badges:
    st.sidebar.write("🎖️ Badges Earned:")
    for badge in st.session_state.badges:
        st.sidebar.markdown(f"- {badge}")

# --- User Response Handling ---
if user_input := st.chat_input("Correct the myth with evidence..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        eval_result = evaluate_response(user_input, st.session_state.myth)
        if isinstance(eval_result, str):
            eval_result = json.loads(eval_result)
    except Exception:
        eval_result = {
            "correctness": False, "clarity": 0, "tone": 0, "evidence": 0,
            "points": 0, "badge": "Myth Apprentice", "level_up": False,
            "feedback": "Error evaluating. Try rephrasing your answer.",
            "PPP_alignment": []
        }

    # Bonus feedback for citation
    if "according to" not in user_input.lower() and eval_result['evidence'] > 2:
        eval_result['feedback'] += " Tip: Cite a source like UNEP, IPCC, or a scientific study to strengthen your response."

    # Update score
    points = eval_result.get("points", 0)
    st.session_state.score += points

    # Level up
    if eval_result.get("level_up"):
        st.session_state.level += 1

    # Add badge if earned
    if eval_result.get("badge") and eval_result["badge"] not in st.session_state.badges:
        st.session_state.badges.append(eval_result["badge"])

    # Render stars
    clarity_stars = render_stars(eval_result['clarity'])
    tone_stars = render_stars(eval_result['tone'])
    evidence_stars = render_stars(eval_result['evidence'])

    # Show evaluation
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"📝 **Evaluation**\n\n"
            f"- ✅ Correctness: {eval_result['correctness']}\n"
            f"- ✨ Clarity: {clarity_stars}\n"
            f"- 🤝 Tone: {tone_stars}\n"
            f"- 📚 Evidence: {evidence_stars}\n"
            #f"- 🌍 P/P/P Alignment: {', '.join(eval_result.get('PPP_alignment', []))}\n"
            f"- 🏆 Points Earned: {points}\n"
            f"- 🎖️ Badge: {eval_result['badge']}\n"
            f"- 🚀 Level Up: {eval_result['level_up']}\n"
            f"- 💡 Feedback: {eval_result['feedback']}\n\n"
            f"**Total Score: {st.session_state.score}**"
        )
    })

    # Next myth
    st.session_state.myth = safe_generate_myth()
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Here’s your next myth:\n\n**{st.session_state.myth}**"
    })

    st.rerun()
