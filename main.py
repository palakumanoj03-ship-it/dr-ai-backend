import random
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

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

# Specialist mappings - Expanded for better diagnosis
SPECIALISTS = {
    "chest pain": "Cardiologist", "heart": "Cardiologist", "sweating": "Cardiologist",
    "skin": "Dermatologist", "rash": "Dermatologist", "itching": "Dermatologist",
    "stomach": "Gastroenterologist", "digestion": "Gastroenterologist", "vomiting": "Gastroenterologist",
    "cancer": "Oncologist", "tumor": "Oncologist",
    "brain": "Neurologist", "seizure": "Neurologist", "fits": "Neurologist",
    "tooth": "Dentist", "gum": "Dentist", "teeth": "Dentist",
    "eye": "Ophthalmologist", "vision": "Ophthalmologist", "red eye": "Ophthalmologist",
    "bone": "Orthopedist", "fracture": "Orthopedist", "joint pain": "Orthopedist",
    "fever": "General Physician", "headache": "General Physician", "cold": "General Physician", "cough": "General Physician",
    "ear pain": "ENT Specialist", "throat": "ENT Specialist", "nose": "ENT Specialist",
    "child": "Pediatrician", "baby": "Pediatrician",
    "bleeding": "Surgeon", "injury": "Surgeon", "wound": "Surgeon",
    
    # Telugu mappings
    "ఛాతీ నొప్పి": "Cardiologist", "గుండె": "Cardiologist", "దమ్ము": "Cardiologist",
    "చర్మం": "Dermatologist", "దురద": "Dermatologist", "మచ్చలు": "Dermatologist",
    "కడుపు నొప్పి": "Gastroenterologist", "వాంతులు": "Gastroenterologist", "విరేచనాలు": "Gastroenterologist",
    "మెదడు": "Neurologist", "ఫిట్స్": "Neurologist", "తల తిరగడం": "Neurologist",
    "పంటి నొప్పి": "Dentist", "చిగుళ్లు": "Dentist",
    "కన్ను": "Ophthalmologist", "చూపు": "Ophthalmologist", "కళ్ళు ఎర్రగా": "Ophthalmologist",
    "ఎముక": "Orthopedist", "నడుము నొప్పి": "Orthopedist", "కీళ్ల నొప్పులు": "Orthopedist",
    "జ్వరం": "General Physician", "తలనొప్పి": "General Physician", "జలుబు": "General Physician", "దగ్గు": "General Physician",
    "చెవి నొప్పి": "ENT Specialist", "గొంతు నొప్పి": "ENT Specialist", "ముక్కు": "ENT Specialist",
    "పిల్లలు": "Pediatrician", "పాప": "Pediatrician", "బాబు": "Pediatrician",
    "రక్తం": "Surgeon", "గాయం": "Surgeon"
}

TRANSLATIONS = {
    "te": {
        "doctor_names": {
            "Cardiologist": "గుండె సంబంధిత వైద్యులు (Cardiologist)",
            "Dermatologist": "చర్మ వ్యాధుల నిపుణులు (Skin Specialist)",
            "Gastroenterologist": "కడుపు మరియు జీర్ణక్రియ నిపుణులు",
            "Oncologist": "క్యాన్సర్ వ్యాధి నిపుణులు",
            "Neurologist": "మెదడు మరియు నరాల నిపుణులు",
            "Dentist": "పంటి డాక్టర్ (Dentist)",
            "Ophthalmologist": "కంటి చూపు నిపుణులు",
            "Orthopedist": "ఎముకల మరియు కీళ్ల నిపుణులు",
            "General Physician": "సాధారణ రోగాల డాక్టర్ (Family Doctor)",
            "ENT Specialist": "చెవి, ముక్కు, గొంతు నిపుణులు (ENT)",
            "Pediatrician": "పిల్లల వైద్య నిపుణులు (Pediatrician)",
            "Surgeon": "సర్జన్ (ఆపరేషన్ నిపుణులు)"
        },
        "greeting": "నమస్తే! నేను డాక్టర్ AI ని. మీకు ఏమైంది? ఎక్కడైనా నొప్పులుగా ఉందా? చెప్పండి.",
        "emergency": "⚠️ ఇది కొంచెం సీరియస్ గా ఉంది! మీరు వెంటనే ఒక **{doctor}** ని కలవాలి. అస్సలు ఆలస్యం చేయకండి!",
        "advice": "అర్థమైంది. మీ లక్షణాలను బట్టి మీరు ఒకసారి **{doctor}** దగ్గరికి వెళ్లి చూపించుకుంటే మంచిది.",
        "question": "అయితే, ఒక చిన్న ప్రశ్న:",
        "follow_ups": {
            "General Physician": ["జ్వరం ఎంత ఉంది? ఎక్కువగా ఉందా?", "దగ్గు లేదా జలుబు ఏమైనా ఉందా?", "తలనొప్పిగా అనిపిస్తుందా?", "ఒంటి నొప్పులు ఏమైనా ఉన్నాయా?", "ఆకలి ఎలా ఉంది? తిండి తింటున్నారా?", "ఇది ఎప్పటి నుండి జరుగుతోంది?"],
            "Cardiologist": ["చెమటలు ఏమైనా పడుతున్నాయా?", "ఎడమ చేయి లాగుతున్నట్టు ఉందా?", "శ్వాస తీసుకోవడం ఇబ్బందిగా ఉందా?", "గుండె దడగా అనిపిస్తుందా?"],
            "Dermatologist": ["చర్మంపై దురదగా ఉందా?", "వాపు లేదా ఎరుపు మచ్చలు ఉన్నాయా?", "మచ్చలు ఎప్పుడు మొదలయ్యాయి?", "ఏదైనా కొత్త సోపు లేదా క్రీము వాడారా?"],
            "Dentist": ["వేడి లేదా చల్లటి వస్తువులు తిన్నప్పుడు పళ్ళు జివ్వుమంటున్నాయా?", "చిగుళ్ల నుండి రక్తం వస్తుందా?", "ముఖంపై ఏమైనా వాపు ఉందా?", "నొప్పి రాత్రిపూట ఎక్కువగా ఉందా?"],
            "ENT Specialist": ["చెవిలో నుండి ఏమైనా ద్రవం కారుతుందా?", "వినబడటంలో ఏమైనా ఇబ్బంది ఉందా?", "గొంతు మంటగా లేదా నొప్పిగా ఉందా?"],
            "Orthopedist": ["నొప్పి ఉన్న చోట వాపు ఏమైనా ఉందా?", "నడవడానికి ఇబ్బందిగా ఉందా?", "దెబ్బ ఏమైనా తగిలిందా?"],
            "Default": ["ఇది ఎప్పటి నుండి జరుగుతోంది?", "నొప్పి ఎక్కువగా ఉందా లేక తక్కువగా ఉందా?", "దీని కోసం ఏమైనా మందులు వాడారా?", "ఇంకేమైనా ఇబ్బందిగా అనిపిస్తుందా?"]
        },
        "fallback": "క్షమించండి, నాకు సరిగ్గా అర్థం కాలేదు. మీకు ఎక్కడ నొప్పిగా ఉంది? జ్వరం ఏమైనా ఉందా?"
    }
}

@app.get("/")
def home(): return {"message": "Dr. AI Assistant is Online"}

@app.post("/analyze-symptoms")
async def analyze_symptoms(data: SymptomRequest, request: Request):
    text = data.symptoms.lower().strip()
    lang = "te" # Defaulting to Telugu for your users
    t = TRANSLATIONS[lang]
    
    # Basic check for greetings
    if any(word in text for word in ["hi", "hello", "నమస్తే", "హలో"]):
        return {"doctor_type": "None", "advice": t["greeting"], "symptoms_detected": "Greeting"}

    doctor = "General Physician"
    found_symptom = False
    for symptom, specialist in SPECIALISTS.items():
        if symptom in text:
            doctor = specialist
            found_symptom = True
            break

    simple_doctor = t["doctor_names"].get(doctor, doctor)
    is_emergency = any(word in text for word in ["రక్తం", "శ్వాస", "ఛాతీ నొప్పి", "serious", "emergency"])
    
    if is_emergency:
        advice = t["emergency"].format(doctor=simple_doctor)
    elif found_symptom:
        questions = t["follow_ups"].get(doctor, t["follow_ups"]["Default"])
        follow_up = random.choice(questions)
        advice = f"{t['advice'].format(doctor=simple_doctor)} {t['question']} {follow_up}"
    else:
        advice = t["fallback"]

    return {"doctor_type": doctor, "advice": advice, "symptoms_detected": text}
