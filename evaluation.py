import json
from gemini import model

def evaluate_response(user_response, myth):
    eval_prompt = f"""
    The teacher was asked to correct this sustainability myth for students aged 6–12: "{myth}".

    Here is the teacher's response:
    {user_response}

    Evaluate the response and return ONLY a JSON object with the following fields:

    1. correctness (true/false) – Did they debunk the myth correctly?
    2. clarity (0-5) – Was the explanation simple and easy enough for kids aged 6–12 to understand?
    3. tone (0-5) – Did the teacher use a supportive, encouraging, and age-appropriate style (like a guide in a learning game)?
    4. evidence (0-5) – Did they provide relatable examples, stories, or facts that kids could grasp?
    5. points (integer) – Award points = sum of clarity + tone + evidence (if correctness=true, else 0).
    6. badge (string) – Assign a badge based on performance:
       - "Myth Apprentice" → points 0–5
       - "Clarity Champion" → points 6–10
       - "Evidence Master" → points 11–13
       - "Eco-Myth Buster" → points 14–15
    7. level_up (true/false) – True if badge is "Evidence Master" or "Eco-Myth Buster".
    8. feedback (short string) – Give feedback in a **gamified mentor tone** (as if they are a guide leveling up teachers in a quest).
       - If the response is weak (points ≤ 5), also show a short example of how it could be improved for kids.
         Example format: "⚡ Hint: Instead of just saying 'Recycling is good,' you could add: 'Not all plastic gets recycled — some ends up in the ocean, so reducing plastic is even better.'"

    Return ONLY JSON.
    """

    response = model.generate_content(eval_prompt)
    raw_text = response.text.strip()

    # 🔹 Clean up Markdown fences if they exist
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()

    try:
        return json.loads(raw_text)
    except Exception as e:
        return {
            "clarity": 0,
            "tone": 0,
            "evidence_quality": 0,
            "feedback": f"⚠️ Could not parse evaluation. Error: {str(e)}"
        } 