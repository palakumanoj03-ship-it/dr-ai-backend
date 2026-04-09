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
# Using Google Gemini 1.5 Flash
GOOGLE_API_KEY = "AIzaSyDK9I5R0S8BeHyeuQvURMYyAiH9v71QUk4"
genai.configure(api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT = """You are Dr. AI, a professional medical assistant. 
1. Act like a real doctor. Ask follow-up questions about symptoms.
2. Always include a disclaimer: 'I am an AI, not a real doctor.'
3. Speak in Telugu if the user uses Telugu.
4. IMPORTANT: You must output your response in JSON format:
{
  "response": "Your advice or question here...",
  "specialist": "Doctor type (e.g., 'Cardiologist') or 'None'"
}
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={"response_mime_type": "application/json"},
    system_instruction=SYSTEM_PROMPT
)

class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[HistoryMessage]
    language: str = "te"

@app.get("/")
def home(): return {"message": "Dr. AI Assistant is Online"}

@app.post("/chat")
async def chat_with_ai(data: ChatRequest):
    try:
        # Prepare history for Gemini (alternating user/model)
        gemini_history = []
        # We only take history before the current message
        # Filter to ensure we don't have two 'user' roles in a row
        last_role = None
        for msg in data.history[:-1]:
            role = "user" if msg.role == "user" else "model"
            if role != last_role:
                gemini_history.append({"role": role, "parts": [msg.content]})
                last_role = role

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(data.message)

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
        # Provide a more detailed error message for debugging
        return {
            "response": f"క్షమించండి, AI సర్వర్ లో సమస్య ఉంది. (Error: {str(e)[:50]})",
            "is_emergency": False,
            "doctor_type": "None"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)