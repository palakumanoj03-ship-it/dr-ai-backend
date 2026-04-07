import random
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Add CORS Middleware so the API can be accessed from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SymptomRequest(BaseModel):
    symptoms: str
    language: str = "en"

# Specialist mappings
SPECIALISTS = {
    # English
    "chest pain": "Cardiologist", "heart": "Cardiologist",
    "skin": "Dermatologist", "rash": "Dermatologist", "itching": "Dermatologist",
    "stomach": "Gastroenterologist", "digestion": "Gastroenterologist",
    "cancer": "Oncologist", "tumor": "Oncologist",
    "brain": "Neurologist", "seizure": "Neurologist",
    "tooth": "Dentist", "gum": "Dentist",
    "eye": "Ophthalmologist", "vision": "Ophthalmologist",
    "bone": "Orthopedist", "fracture": "Orthopedist",
    "fever": "General Physician", "headache": "General Physician", "cold": "General Physician", "cough": "General Physician",
    "bleeding": "Surgeon", "injury": "Surgeon", "wound": "Surgeon",
    
    # Hindi
    "सीना दर्द": "Cardiologist", "दिल": "Cardiologist",
    "त्वचा": "Dermatologist", "खुजली": "Dermatologist",
    "पेट दर्द": "Gastroenterologist", "पाचन": "Gastroenterologist",
    "कैंसर": "Oncologist",
    "दिमाग": "Neurologist",
    "दांत": "Dentist",
    "आंख": "Ophthalmologist",
    "हड्डी": "Orthopedist",
    "बुखार": "General Physician", "सिरदर्द": "General Physician",
    
    # Local Telugu & "Telugish"
    "ఛాతీ నొప్పి": "Cardiologist", "గుండె": "Cardiologist", "దమ్ము": "Cardiologist", "శ్వాస": "Cardiologist",
    "చర్మం": "Dermatologist", "దురద": "Dermatologist", "మచ్చలు": "Dermatologist", "గుల్లలు": "Dermatologist",
    "కడుపు నొప్పి": "Gastroenterologist", "మంట": "Gastroenterologist", "వాంతులు": "Gastroenterologist", "విరేచనాలు": "Gastroenterologist",
    "క్యాన్సర్": "Oncologist", "గడ్డ": "Oncologist",
    "మెదడు": "Neurologist", "ఫిట్స్": "Neurologist", "తల తిరగడం": "Neurologist",
    "పంటి నొప్పి": "Dentist", "చిగుళ్లు": "Dentist",
    "కన్ను": "Ophthalmologist", "చూపు": "Ophthalmologist",
    "ఎముక": "Orthopedist", "నడుము నొప్పి": "Orthopedist", "కాళ్ల నొప్పులు": "Orthopedist",
    "జ్వరం": "General Physician", "తలనొప్పి": "General Physician", "తల నొప్పి": "General Physician", "నీరసం": "General Physician", "జలుబు": "General Physician", "దగ్గు": "General Physician",
    "రక్తం": "Surgeon", "దెబ్బ": "Surgeon", "గాయం": "Surgeon", "బ్లీడింగ్": "Surgeon",
    "ఫీవర్": "General Physician", "పెయిన్": "General Physician", "బాడీ పెయిన్స్": "General Physician",
    "షుగర్": "Endocrinologist", "బీపీ": "Cardiologist"
}

TRANSLATIONS = {
    "en": {
        "doctor_names": {
            "Cardiologist": "Heart Specialist (Cardiologist)",
            "Dermatologist": "Skin Specialist (Dermatologist)",
            "Gastroenterologist": "Stomach and Digestion Specialist",
            "Oncologist": "Cancer Specialist",
            "Neurologist": "Brain and Nerve Specialist",
            "Dentist": "Tooth Doctor (Dentist)",
            "Ophthalmologist": "Eye Specialist (Ophthalmologist)",
            "Orthopedist": "Bone and Joint Specialist",
            "General Physician": "General Family Doctor",
            "Surgeon": "Surgeon (Operation Specialist)",
            "Endocrinologist": "Diabetes Specialist"
        },
        "greeting": "Hello! I am Dr. AI. How are you feeling today? Tell me what's bothering you.",
        "gratitude": "You're welcome! I'm here to help. Anything else?",
        "closing": "Take care! If you don't feel better, please visit a doctor. Bye!",
        "emergency": "⚠️ This looks serious! You should see a **{doctor}** immediately. Please don't delay!",
        "advice": "I understand. For this issue, I recommend meeting a **{doctor}**.",
        "question": "Doctor's Question:",
        "fallback": "I didn't quite get that. Can you tell me more? Where exactly is the pain? Do you have a fever?",
        "follow_ups": {
            "General Physician": ["How high is the fever?", "Do you have a cough or cold?", "Is there any headache?", "Since when are you feeling this way?"],
            "Cardiologist": ["Is there any sweating?", "Do you feel pain in your left arm?", "Are you feeling breathless?"],
            "Dermatologist": ["Is the skin itchy?", "Is there any redness or swelling?", "When did the rash start?"],
            "Dentist": ["Is there sensitivity to hot or cold?", "Is your gum bleeding?", "Is there any swelling in the face?"],
            "Default": ["Since when is this happening?", "Is the pain very high?", "Did you take any medicine for this?", "Are you feeling very weak?"]
        }
    },
    "te": {
        "doctor_names": {
            "Cardiologist": "గుండె సంబంధిత వైద్యులు (Heart Specialist)",
            "Dermatologist": "చర్మ వ్యాధుల నిపుణులు (Skin Specialist)",
            "Gastroenterologist": "కడుపు మరియు జీర్ణక్రియ నిపుణులు",
            "Oncologist": "క్యాన్సర్ వ్యాధి నిపుణులు",
            "Neurologist": "మెదడు మరియు నరాల నిపుణులు",
            "Dentist": "పంటి డాక్టర్ (Dentist)",
            "Ophthalmologist": "కంటి చూపు నిపుణులు",
            "Orthopedist": "ఎముకల మరియు కీళ్ల నిపుణులు",
            "General Physician": "సాధారణ రోగాల డాక్టర్ (Family Doctor)",
            "Surgeon": "సర్జన్ (ఆపరేషన్ నిపుణులు)",
            "Endocrinologist": "షుగర్ వ్యాధి నిపుణులు"
        },
        "greeting": "నమస్తే! నేను డాక్టర్ AI ని. మీకు ఏమైంది? ఎక్కడైనా నొప్పులుగా ఉందా? చెప్పండి.",
        "gratitude": "పర్వాలేదండి! సహాయం చేయడానికి నేను ఇక్కడే ఉంటాను. ఇంకేమైనా అడగాలా?",
        "closing": "జాగ్రత్తగా ఉండండి! నొప్పులు తగ్గకపోతే వెంటనే డాక్టర్ దగ్గరికి వెళ్ళండి. ఉంటానండి!",
        "emergency": "⚠️ ఇది కొంచెం సీరియస్ గా ఉంది! మీరు వెంటనే ఒక **{doctor}** ని కలవాలి. అస్సలు ఆలస్యం చేయకండి!",
        "advice": "అర్థమైంది. దీని కోసం మీరు ఒకసారి **{doctor}** దగ్గరికి వెళ్లి చూపించుకోండి.",
        "question": "డాక్టర్ అడిగే ప్రశ్న:",
        "follow_ups": {
            "General Physician": ["జ్వరం ఎంత ఉంది?", "దగ్గు లేదా జలుబు ఏమైనా ఉందా?", "తలనొప్పిగా అనిపిస్తుందా?", "ఇది ఎప్పటి నుండి జరుగుతోంది?"],
            "Cardiologist": ["చెమటలు ఏమైనా పడుతున్నాయా?", "ఎడమ చేయి లాగుతున్నట్టు ఉందా?", "శ్వాస తీసుకోవడం ఇబ్బందిగా ఉందా?"],
            "Dermatologist": ["చర్మంపై దురదగా ఉందా?", "వాపు లేదా ఎరుపు మచ్చలు ఉన్నాయా?", "మచ్చలు ఎప్పుడు మొదలయ్యాయి?"],
            "Dentist": ["వేడి లేదా చల్లటి వస్తువులు తిన్నప్పుడు పళ్ళు జివ్వుమంటున్నాయా?", "చిగుళ్ల నుండి రక్తం వస్తుందా?", "ముఖంపై ఏమైనా వాపు ఉందా?"],
            "Default": ["ఇది ఎప్పటి నుండి జరుగుతోంది?", "నొప్పి ఎక్కువగా ఉందా లేక తక్కువగా ఉందా?", "దీని కోసం ఏమైనా మందులు వాడారా?", "ఇంకేమైనా ఇబ్బందిగా అనిపిస్తుందా?"]
        },
        "fallback": "క్షమించండి, నాకు సరిగ్గా అర్థం కాలేదు. మీకు ఎక్కడ నొప్పిగా ఉంది? జ్వరం ఏమైనా ఉందా?"
    }
}

EMERGENCY_WORDS = ["chest pain", "breathless", "seizure", "bleeding", "unconscious", "सीने में दर्द", "बेहोश", "ఛాతీ నొప్పి", "శ్వాస ఆడకపోవడం", "దమ్ము", "స్పృహ తప్పడం", "రక్తం", "బ్లీడింగ్", "పెయిన్", "సీరియస్"]

@app.get("/")
def home():
    return {"message": "Dr. AI Assistant is Online"}

@app.post("/analyze-symptoms")
async def analyze_symptoms(data: SymptomRequest, request: Request):
    text = data.symptoms.lower().strip()
    lang = data.language if data.language in TRANSLATIONS else "en"
    t = TRANSLATIONS[lang]
    
    # 1. Handle Greetings, Gratitude, Closings
    if any(word in text for word in ["hi", "hello", "नमस्ते", "నమస్తే", "హలో", "hey"]):
        return {"doctor_type": "None", "advice": t["greeting"], "symptoms_detected": "Greeting"}
    if any(word in text for word in ["thanks", "thank you", "धन्यवाद", "ధన్యవాదాలు", "థాంక్స్", "మంచిది"]):
        return {"doctor_type": "None", "advice": t["gratitude"], "symptoms_detected": "Gratitude"}
    if any(word in text for word in ["bye", "goodbye", "अलविदा", "సెలవు", "వెళ్తాను", "ఉంటాను"]):
        return {"doctor_type": "None", "advice": t["closing"], "symptoms_detected": "Closing"}

    # 2. Standard Symptom Analysis
    doctor = "General Physician"
    found_symptom = False
    for symptom, specialist in SPECIALISTS.items():
        if symptom in text:
            doctor = specialist
            found_symptom = True
            break

    simple_doctor = t.get("doctor_names", {}).get(doctor, doctor)
    is_emergency = any(word in text for word in EMERGENCY_WORDS)
    
    if is_emergency:
        advice = t["emergency"].format(doctor=simple_doctor)
    elif found_symptom:
        # GET DOCTOR-SPECIFIC QUESTIONS
        questions = t["follow_ups"].get(doctor, t["follow_ups"]["Default"])
        follow_up = random.choice(questions)
        advice = f"{t['advice'].format(doctor=simple_doctor)} {t['question']} {follow_up}"
    else:
        advice = t["fallback"]

    return {
        "doctor_type": doctor,
        "advice": advice,
        "symptoms_detected": text
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
