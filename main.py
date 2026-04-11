import random
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
# We now read the key from an Environment Variable for safety
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables!")

SYSTEM_PROMPT = """You are Dr. AI, a professional medical assistant. 
1. Act like a real doctor. Ask 1-2 follow-up questions about symptoms.
2. Always include a disclaimer: 'I am an AI, not a real doctor.'
3. Speak in Telugu if the user uses Telugu.
4. IMPORTANT: You must output your response in JSON format with these exact keys:
{
  "response": "Your advice or question here...",
  "specialist": "Doctor type (e.g., 'Cardiologist') or 'None'"
}
"""

def get_working_model_name():
    try:
        if not GOOGLE_API_KEY:
            return "models/gemini-1.5-flash"
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ["models/gemini-1.5-flash", "models/gemini-1.5-flash-8b", "models/gemini-pro"]
        for p in priority:
            if p in models: return p
        return models[0] if models else "models/gemini-pro"
    except Exception as e:
        print(f"Error detecting models: {e}")
        return "models/gemini-1.5-flash"

# Detect model name
DETECTED_MODEL = get_working_model_name()

class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[HistoryMessage]
    language: str = "te"

def clean_history(history_list):
    cleaned = []
    last_role = None
    for msg in history_list:
        role = "user" if msg.role == "user" else "model"
        if role != last_role:
            cleaned.append({"role": role, "parts": [msg.content]})
            last_role = role
    if cleaned and cleaned[-1]["role"] == "user":
        cleaned.pop()
    return cleaned

@app.get("/")
def home():
    return {"status": "online", "model": DETECTED_MODEL, "key_configured": bool(GOOGLE_API_KEY)}

@app.post("/chat")
async def chat_with_ai(data: ChatRequest):
    if not GOOGLE_API_KEY:
        return {"response": "Server configuration error: API Key missing.", "is_emergency": False, "doctor_type": "None"}
        
    try:
        if "1.5" in DETECTED_MODEL:
            model = genai.GenerativeModel(
                model_name=DETECTED_MODEL,
                generation_config={"response_mime_type": "application/json"},
                system_instruction=SYSTEM_PROMPT
            )
            user_input = data.message
        else:
            model = genai.GenerativeModel(model_name=DETECTED_MODEL)
            user_input = f"{SYSTEM_PROMPT}\n\nUser: {data.message}\n\nRespond in JSON format."

        chat = model.start_chat(history=clean_history(data.history))
        response = chat.send_message(user_input)
        
        text = response.text
        clean_json = re.sub(r"```json\n?|```", "", text).strip()
        result = json.loads(clean_json)

        return {
            "response": result.get("response", ""),
            "is_emergency": False,
            "doctor_type": result.get("specialist", "None")
        }
    except Exception as e:
        return {"response": f"AI Error: {str(e)[:50]}", "is_emergency": False, "doctor_type": "None"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
