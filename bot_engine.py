# bot_engine.py
import os
import random
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

# Try to import google generative client if API key present
GENAI_AVAILABLE = False
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY and GENAI_AVAILABLE:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        # prefer a stable conversational model; adjust if needed
        MODEL_NAME = "gemini-pro"
    except Exception as e:
        print("Could not configure google generative client:", e)
        GENAI_AVAILABLE = False
else:
    GENAI_AVAILABLE = False

class BotEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        # Broad crisis keywords (not exhaustive)
        self.crisis_keywords = [
            "kill myself", "killing myself", "suicide", "end my life", "want to die", "cant live", "give up",
            "no reason to live", "hurt myself", "i'll end it", "i will end it", "i can't go on",
            "i'm going to kill myself", "i'm going to end my life"
        ]

        # Friendly companion fallback responses
        self.fallback = {
            "sad": [
                "I’m really sorry you’re feeling down. I’m here with you — tell me more when you’re ready.",
                "That sounds heavy. Thank you for sharing it with me. I’m here to listen."
            ],
            "anxious": [
                "Take a slow breath with me. You’re safe right now. What’s on your mind?",
                "Anxiety is so tough — you’re not alone. Tell me what’s worrying you if you can."
            ],
            "angry": [
                "It makes sense to feel upset. You’re allowed to feel what you feel.",
                "I’m listening. If you want, tell me why this is making you angry."
            ],
            "positive": [
                "That’s wonderful news — I’m so happy for you!",
                "That sounds great! Tell me more."
            ],
            "neutral": [
                "I’m here and listening. What would you like to talk about?",
                "I’m right here. Tell me what’s on your mind."
            ]
        }

    def check_crisis(self, text):
        t = text.lower()
        print(f"DEBUG: Checking crisis for '{t}' against keywords")
        for k in self.crisis_keywords:
            if k in t:
                print(f"DEBUG: Match found for '{k}'")
                return True
        return False

    def detect_emotion(self, text):
        t = text.lower()
        vs = self.analyzer.polarity_scores(text)
        compound = vs.get("compound", 0.0)
        # keyword overrides for clarity
        if any(w in t for w in ["sad", "cry", "depressed", "down", "hopeless"]):
            return "sad"
        if any(w in t for w in ["anxious", "anxiety", "panic", "nervous", "scared", "worried"]):
            return "anxious"
        if any(w in t for w in ["angry", "annoyed", "mad", "furious", "irritated"]):
            return "angry"
        if compound >= 0.4:
            return "positive"
        if compound <= -0.3:
            return "sad"
        return "neutral"

    def generate_ai_response(self, user_msg, history, emotion):
        if not GENAI_AVAILABLE:
            return None
        # Build a concise prompt for the generative model
        system_prompt = (
            "You are 'Serena', a friendly, non-romantic, empathetic AI companion. "
            "Be warm, validating, and supportive. Keep responses concise (2-4 short paragraphs). "
            "Do not provide medical diagnoses. If the user expresses self-harm or suicide, respond with "
            "empathy and advise contacting local emergency services and trusted people."
            f"\nDetected user emotion: {emotion}\n\n"
        )
        # Build a small chat history for context
        chat_history = ""
        for item in history[-8:]:
            u = item.get("user_msg", "")
            b = item.get("bot_msg", "")
            if u:
                chat_history += f"User: {u}\n"
            if b:
                chat_history += f"Assistant: {b}\n"
        prompt = system_prompt + "Conversation:\n" + chat_history + f"User: {user_msg}\nAssistant:"

        try:
            # Use the modern GenerativeModel API
            model = genai.GenerativeModel(MODEL_NAME)
            resp = model.generate_content(prompt)
            
            if resp and resp.text:
                return resp.text.strip()
        except Exception as e:
            print("Generative API error:", e)
            return None

        return None

    def generate_response(self, user_msg, history):
        print(f"DEBUG: Generating response for: '{user_msg}'")
        
        # 1. crisis detection (highest priority)
        is_crisis = self.check_crisis(user_msg)
        print(f"DEBUG: Crisis detected: {is_crisis}")
        
        if is_crisis:
            return (
                "I’m really sorry you’re in so much pain. You deserve immediate support and safety. "
                "Please consider contacting your local emergency services or a suicide prevention hotline, "
                "or reach out to someone close to you right now. You are not alone."
            )

        # 2. detect emotion
        emotion = self.detect_emotion(user_msg)
        print(f"DEBUG: Emotion detected: {emotion}")
        
        # 3. try online generative AI
        ai_reply = self.generate_ai_response(user_msg, history, emotion)
        if ai_reply:
            print("DEBUG: Using AI response")
            return ai_reply
        
        print("DEBUG: AI failed, using fallback")
        # 4. fallback local response
        choices = self.fallback.get(emotion, self.fallback["neutral"])
        return random.choice(choices)
