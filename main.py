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

def create_model(model_name, use_system_instruction=True):
    try:
        kwargs = {
            "model_name": model_name,
            "generation_config": {"response_mime_type": "application/json"}
        }
        if use_system_instruction:
            kwargs["system_instruction"] = SYSTEM_PROMPT
        return genai.GenerativeModel(**kwargs)
    except Exception:
        # Fallback for older models that don't support system_instruction or JSON mode
        return genai.GenerativeModel(model_name=model_name)

# Try initializing with the most modern name
model = create_model("gemini-1.5-flash")

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
        # 1. Prepare history for Gemini (Alternating roles)
        gemini_history = []
        last_role = None
        # Use history from request but filter duplicates
        for msg in data.history:
            # Android sends 'assistant', Gemini needs 'model'
            current_role = "user" if msg.role == "user" else "model"
            if current_role != last_role:
                gemini_history.append({"role": current_role, "parts": [msg.content]})
                last_role = current_role
        
        # Gemini history shouldn't end with 'user' if we are sending a new message
        if gemini_history and gemini_history[-1]["role"] == "user":
            gemini_history.pop()

        # 2. Call Gemini
        try:
            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(data.message)
        except Exception as e:
            err_str = str(e).lower()
            if "404" in err_str or "not found" in err_str:
                # Try absolute fallback to gemini-pro
                model = create_model("gemini-pro", use_system_instruction=False)
                chat = model.start_chat(history=gemini_history)
                # For gemini-pro, we inject system prompt manually
                full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {data.message}\n\nRespond in JSON."
                response = chat.send_message(full_prompt)
            else:
                raise e

        # 3. Parse and Clean Response
        try:
            raw_text = response.text
            # Remove markdown if present
            clean_json = re.sub(r"```json\n?|\n?```", "", raw_text).strip()
            result = json.loads(clean_json)
        except Exception:
            # If JSON parsing fails, return raw text as response
            result = {"response": response.text, "specialist": "None"}

        return {
            "response": result.get("response", ""),
            "is_emergency": False,
            "doctor_type": result.get("specialist", "None")
        }

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return {
            "response": f"క్షమించండి, సర్వర్ లో చిన్న సమస్య ఉంది. (Error: {str(e)[:30]})",
            "is_emergency": False,
            "doctor_type": "None"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
