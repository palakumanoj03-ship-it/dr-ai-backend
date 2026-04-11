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
4. IMPORTANT: You must output your response in JSON format with these exact keys:
{
  "response": "Your advice or question here...",
  "specialist": "Doctor type (e.g., 'Cardiologist') or 'None'"
}
"""

class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[HistoryMessage]
    language: str = "te"

def clean_history(history_list):
    """Ensures history alternates perfectly between user and model."""
    cleaned = []
    last_role = None
    for msg in history_list:
        # Map Android 'assistant' to Gemini 'model'
        current_role = "user" if msg.role == "user" else "model"
        if current_role != last_role:
            cleaned.append({"role": current_role, "parts": [msg.content]})
            last_role = current_role
    
    # History must end with a model response if we are about to send a new user message
    if cleaned and cleaned[-1]["role"] == "user":
        cleaned.pop()
    return cleaned

@app.get("/")
def home():
    return {"message": "Dr. AI Assistant is Online"}

@app.post("/chat")
async def chat_with_ai(data: ChatRequest):
    # List of model variations to try in order
    model_candidates = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    last_error = "Unknown Error"
    
    for model_name in model_candidates:
        try:
            # Configure model
            config = {"response_mime_type": "application/json"}
            
            # Models 1.5 and above support system_instruction
            if "1.5" in model_name:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=config,
                    system_instruction=SYSTEM_PROMPT
                )
                user_input = data.message
            else:
                # Legacy models (like gemini-pro) might need prompt injection
                model = genai.GenerativeModel(model_name=model_name)
                user_input = f"{SYSTEM_PROMPT}\n\nUser Message: {data.message}\n\nRespond in JSON format."

            # Prepare history
            gemini_history = clean_history(data.history)
            
            # Start chat
            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(user_input)
            
            # Parse response
            raw_text = response.text
            # Remove potential markdown formatting
            clean_json = re.sub(r"```json\n?|\n?```", "", raw_text).strip()
            result = json.loads(clean_json)

            return {
                "response": result.get("response", ""),
                "is_emergency": False,
                "doctor_type": result.get("specialist", "None")
            }

        except Exception as e:
            last_error = str(e)
            print(f"Failed with {model_name}: {last_error}")
            # If it's a 404, we continue to the next model in the list
            if "404" in last_error or "not found" in last_error.lower():
                continue
            else:
                # For other errors (like quota or key issues), we stop and report it
                break

    # If all attempts failed
    return {
        "response": f"క్షమించండి, AI కనెక్షన్ లో సమస్య ఉంది. (Error: {last_error[:50]})",
        "is_emergency": False,
        "doctor_type": "None"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
