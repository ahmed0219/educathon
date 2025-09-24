import json
from gemini import model

def evaluate_response(user_response, myth):
    eval_prompt = f"""
    The user was asked to correct this sustainability myth: "{myth}".

    Here is the user's response:
    {user_response}

    Evaluate their answer and return a JSON object with:
    1. Correctness (true/false)
    2. Clarity (0-5)
    3. Tone (0-5)
    4. Evidence quality (0-5)
    5. Feedback (short, constructive)

    Return ONLY JSON.
    
    """
    response = model.generate_content(eval_prompt)
    raw_text = response.text.strip()

    # 🔹 Clean up Markdown fences if they exist
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        # remove optional "json" language tag
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