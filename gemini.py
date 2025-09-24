
from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st

import os
load_dotenv()
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel("models/gemini-2.0-flash")

def generate_myth():

    
    prompt = """
You are a misinformed student. You will generate common sustainability myths 
- Provide only one myth per request.
- Keep it realistic and widely believed.
- Do not correct it or provide evidence.

"""

   
    response = model.generate_content(prompt)
    return response.text
