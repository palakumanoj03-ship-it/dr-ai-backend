import random
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
# IMPORTANT: Ensure this key is from https://aistudio.google.com/
GOOGLE_API_KEY = "AIzaSyDK9I5R0S8BeHyeuQvURMYyAiH9v71QUk4"
genai.configure(api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT = """You are Dr. AI, a professional medical assistant. 
1. Act like a real doctor. Ask 1-2 follow-up questions about symptoms.
2. Always include a disclaimer: 'I am an AI, not a real doctor.'
3. Speak in Telugu if the user uses Telugu.
4. IMPORTANT: You must output your response in JSON format:
{
  "response": "Your advice or question here...",
  "specialist": "Doctor type (e.g., 'Cardiologist') or 'None'"
}
"""

def get_model(name):
    return genai.GenerativeModel(
        model_name=name,
        generation_config={"response_mime_type": "application/json"},
        system_instruction=SYSTEM_PROMPT
    )

# Primary model
model = get_model("gemini-1.5-flash")

class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[HistoryMessage]
    language: str = "te"

@app.get("/")
def home():
    return {"message": "Dr. AI Assistant is Online"}

@app.post("/chat")
async def chat_with_ai(data: ChatRequest):
    global model
    try:
        # Prepare history for Gemini
        gemini_history = []
        last_role = None
        # Clean history to ensure roles alternate: user -> model -> user
        for msg in data.history[:-1]:
            role = "user" if msg.role == "user" else "model"
            if role != last_role:
                gemini_history.append({"role": role, "parts": [msg.content]})
                last_role = role

        try:
            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(data.message)
        except Exception as model_err:
            # FALLBACK: If Flash fails (404), try Gemini Pro
            if "404" in str(model_err) or "not found" in str(model_err).lower():
                print("Gemini 1.5 Flash not found, falling back to Gemini Pro...")
                model = get_model("gemini-pro")
                chat = model.start_chat(history=gemini_history)
                # Note: gemini-pro might not support system_instruction in older SDKs,
                # but modern SDKs handle it.
                response = chat.send_message(data.message)
            else:
                raise model_err

        # Clean and parse JSON
        clean_json = re.sub(r"```json\n?|\n?```", "", response.text).strip()
        result = json.loads(clean_json)

        return {
            "response": result.get("response", ""),
            "is_emergency": False,
            "doctor_type": result.get("specialist", "None")
        }
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return {
            "response": f"క్షమించండి, AI సర్వర్ లో సమస్య ఉంది. దయచేసి కాసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి.",
            "is_emergency": False,
            "doctor_type": "None"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)