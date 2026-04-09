import random
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
# Using Google Gemini (Free Tier available at aistudio.google.com)
GOOGLE_API_KEY = "AIzaSyDK9I5R0S8BeHyeuQvURMYyAiH9v71QUk4"
genai.configure(api_key=GOOGLE_API_KEY)

# Use gemini-1.5-flash for speed and free-tier efficiency
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={"response_mime_type": "application/json"}
)

class ChatMessage(BaseModel):
    role: str  # "user" or "model" (Gemini uses 'model' instead of 'assistant')
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]
    language: str = "te"

# Emergency keywords in English and Telugu
EMERGENCY_WORDS = ["chest pain", "breathless", "unconscious", "bleeding", "ఛాతీ నొప్పి", "శ్వాస", "స్పృహ", "రక్తం", "heart attack"]

SYSTEM_PROMPT = """You are Dr. AI, a professional and empathetic medical assistant. 
Your goal is to help users understand their symptoms by having a realistic medical conversation. 

Instructions:
1. Act like a real doctor during a consultation. 
2. When a user mentions a symptom, acknowledge it and ask 1-2 relevant follow-up questions to gather more detail (e.g., duration, severity, or related symptoms like headache/cough).
3. Do not give a final recommendation or suggest a specialist immediately unless the situation seems urgent or you have enough information (usually after 2-3 exchanges).
4. Keep responses brief (2-3 sentences).
5. Always speak in Telugu if the user uses Telugu, or English if they use English.
6. When you are ready to recommend a specialist, mention it clearly in your response.
7. Always include a brief disclaimer: 'I am an AI, not a real doctor.'

IMPORTANT: You must output your response in JSON format with exactly these two keys:
{
  "response": "Your medical response or question here...",
  "specialist": "The name of the specialist (e.g., 'Cardiologist', 'Dermatologist') ONLY if you are making a recommendation, otherwise 'None'"
}
"""

@app.post("/chat")
async def chat_with_ai(data: ChatRequest):
    user_input = data.message.lower()

    # 1. Safety Layer: Emergency Detection
    if any(word in user_input for word in EMERGENCY_WORDS):
        return {
            "response": "⚠️ EMERGENCY: Your symptoms look serious. Please visit the nearest hospital or call 108 immediately. (ఇది అత్యవసర పరిస్థితి! వెంటనే ఆసుపత్రికి వెళ్ళండి.)",
            "is_emergency": True,
            "doctor_type": "Emergency"
        }

    # 2. Context-Aware Conversation (Gemini)
    # Gemini history format requires converting 'assistant' to 'model'
    gemini_history = []
    for msg in data.history[-6:]:
        role = "user" if msg.role == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg.content]})

    try:
        # Start a chat session with history
        chat = model.start_chat(history=gemini_history)
        
        # Include the system prompt in the instruction or as part of the context
        # In Gemini 1.5, we can use system_instruction when initializing the model, 
        # but for a quick swap, we'll prefix the prompt or use the chat session.
        
        response = chat.send_message(f"{SYSTEM_PROMPT}\n\nUser Message: {data.message}")
        
        # Parse the JSON response from Gemini
        result = json.loads(response.text)
        ai_reply = result.get("response", "")
        recommended_doctor = result.get("specialist", "None")

        return {
            "response": ai_reply,
            "is_emergency": False,
            "doctor_type": recommended_doctor
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "response": "క్షమించండి, AI ప్రస్తుతం అందుబాటులో లేదు. దయచేసి మళ్ళీ ప్రయత్నించండి. (AI is currently unavailable.)",
            "is_emergency": False,
            "doctor_type": "None"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
