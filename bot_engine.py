import os
import google.generativeai as genai
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini safely
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
else:
    model = None
    print("⚠ WARNING: GOOGLE_API_KEY not found. Using local fallback mode.")


class BotEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

        # Crisis keywords
        self.crisis_keywords = [
            "kill myself", "suicide", "end my life", "want to die",
            "hurt myself", "cut myself", "hopeless", "worthless",
            "no reason to live", "give up", "can't go on",
            "end it", "life is pointless"
        ]

        # Local fallback responses
        self.fallback = {
            "sad": [
                "I'm really sorry you're feeling this way. You’re not alone — I'm here with you.",
                "That sounds really heavy. Thank you for sharing it with me. I'm here to support you.",
            ],
            "angry": [
                "It makes sense that you're feeling upset. Your emotions are valid — tell me what happened.",
                "I'm listening. It's okay to feel anger; it usually means something important is going on."
            ],
            "anxious": [
                "Take a slow breath with me. You're safe right now. Tell me what’s worrying you.",
                "Anxiety can feel overwhelming, but you aren't facing it alone. I'm here with you."
            ],
            "neutral": [
                "I’m here and listening. Tell me more — whatever is on your mind matters.",
                "I'm here for you. What would you like to talk about?"
            ]
        }

    # -------------------------------
    # Crisis + Emotion Detection
    # -------------------------------

    def check_crisis(self, text):
        text = text.lower()
        return any(w in text for w in self.crisis_keywords)

    def detect_emotion(self, text):
        text = text.lower()
        if any(w in text for w in ["sad", "cry", "hurt", "pain", "down", "depressed"]):
            return "sad"
        if any(w in text for w in ["angry", "mad", "upset", "pissed"]):
            return "angry"
        if any(w in text for w in ["anxious", "scared", "panic", "nervous"]):
            return "anxious"
        return "neutral"

    # -------------------------------
    # Gemini Response
    # -------------------------------

    def generate_ai_response(self, user_msg, history, emotion):
        if not model:
            return None

        system_prompt = """
You are a supportive, empathetic mental-health companion — NOT a therapist.
Your role:
• Listen actively
• Validate feelings
• Encourage grounding and reflection
• Avoid medical, diagnostic, or therapeutic claims
• Never provide instructions involving harm
• Never encourage self-treatment or diagnosis
• Stay non-romantic and emotionally neutral

Tone:
• Warm, gentle, calming
• Short, clear sentences
• Supportive, not intimate

If the user expresses suicidal intent:
• Encourage reaching out to a trusted person
• Recommend contacting local emergency services
• Do NOT attempt to “fix” the crisis

Detected emotion: {emotion}
"""

        # Build short history
        formatted_history = ""
        for h in history[-8:]:
            formatted_history += f"User: {h['user_msg']}\n"
            formatted_history += f"Assistant: {h['bot_msg']}\n"

        full_prompt = (
            system_prompt.format(emotion=emotion)
            + "\nConversation:\n"
            + formatted_history
            + f"\nUser: {user_msg}\nAssistant:"
        )

        try:
            response = model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            print("Gemini Error:", e)
            return None

    # -------------------------------
    # Main Response
    # -------------------------------
    
    def generate_response(self, user_msg, history):
        # Emotion
        emotion = self.detect_emotion(user_msg)
        if emotion not in self.fallback:
            emotion = "neutral"

        # Crisis check
        if self.check_crisis(user_msg):
            return (
                "I’m really sorry you're feeling this much pain. You deserve care and safety. "
                "Please reach out to someone you trust or your local suicide helpline. "
                "If you're in immediate danger, please contact emergency services right now. "
                "You are not alone — your feelings matter. ❤️"
            )

        # Try online AI
        ai_reply = self.generate_ai_response(user_msg, history, emotion)
        if ai_reply:
            return ai_reply

        # Local fallback
        return self.fallback[emotion][0]
