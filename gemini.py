
import google.generativeai as genai
import streamlit as st

import os

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel("models/gemini-2.0-flash")

def generate_myth(theme):
    prompt = f"""
You are roleplaying as a **misinformed student** in a classroom discussion.  
Your task is to generate **one sustainability myth** related to the {theme}.  

Guidelines:
- Speak in a natural, student-like way (casual, conversational).  
- Express the myth as if you genuinely believe it, or are unsure and asking.  
- Keep it short: 1–2 sentences max.  
- Do NOT correct yourself or add evidence.  
- Avoid being too formal or academic.  

Examples:
- "Isn’t it true that recycling plastic always helps the environment?"  
- "I heard electric cars are actually worse for the planet than gasoline ones."  
- "Doesn’t turning off lights at night save almost no energy?"  

Now generate one realistic sustainability myth a student might say.
"""
   
    response = model.generate_content(prompt)
    return response.text
