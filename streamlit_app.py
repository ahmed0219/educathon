import streamlit as st
from gemini import generate_myth
from evaluation import evaluate_response
import json
import sqlite3
from setup_db import setup_db
st.title("♻️ Sustainability Myth-Busting Chatbot")
setup_db()
# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "myth" not in st.session_state:
    st.session_state.myth = None
if "score" not in st.session_state:
    st.session_state.score = 0
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
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Login or Register")

    choice = st.radio("Choose an option:", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
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
# Start with a myth
if st.session_state.myth is None:
    st.session_state.myth = generate_myth()
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Here’s a sustainability myth for you to bust:\n\n**{st.session_state.myth}**"
    })


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Correct the myth with evidence..."):
    st.session_state.messages.append({"role": "user", "content": user_input})


    eval_result = evaluate_response(user_input, st.session_state.myth)
    print(eval_result)
    points = (eval_result["Clarity"] + eval_result["Tone"] + eval_result["Evidence quality"]
             if eval_result.get("Correctness") else 0)
    st.session_state.score += points
    print(f"Points earned: {points}, Total score: {st.session_state.score}")
    
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            f"📝 **Evaluation**\n\n"
            f"- Clarity: {eval_result['Clarity']}/5\n"
            f"- Tone: {eval_result['Tone']}/5\n"
            f"- Evidence Quality: {eval_result['Evidence quality']}/5\n"
            f"- Feedback: {eval_result['Feedback']}"
        )
    })


    st.session_state.myth = generate_myth()
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Here’s your next myth:\n\n**{st.session_state.myth}**"
    })

    st.rerun()