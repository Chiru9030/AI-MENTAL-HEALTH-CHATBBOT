import os
import json
import random
import datetime
import uuid
from flask import Flask, render_template, request, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from cryptography.fernet import Fernet
import google.generativeai as genai

# --- Configuration ---
DATA_FILE = "chat_data.enc"
KEY_FILE = "secret.key"
USER_ID = "default_user"

# Configure Gemini API
GOOGLE_API_KEY = "AIzaSyBZcCtp4Bvkvost3S5Z4t5TH2iqv7VL_Jc".strip() # User provided key
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None
    print("WARNING: GOOGLE_API_KEY not found. AI features will be limited.")

app = Flask(__name__)

# --- Storage Manager Logic ---
class StorageManager:
    def __init__(self):
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)
        self._ensure_data_file()

    def _load_or_create_key(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as key_file:
                key_file.write(key)
            return key

    def _ensure_data_file(self):
        if not os.path.exists(DATA_FILE):
            initial_data = {"users": {}}
            self.save_data(initial_data)

    def save_data(self, data):
        json_data = json.dumps(data)
        encrypted_data = self.cipher.encrypt(json_data.encode())
        with open(DATA_FILE, "wb") as f:
            f.write(encrypted_data)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {"users": {}}
        try:
            with open(DATA_FILE, "rb") as f:
                encrypted_data = f.read()
                if not encrypted_data: return {"users": {}}
                decrypted_data = self.cipher.decrypt(encrypted_data).decode()
                return json.loads(decrypted_data)
        except Exception as e:
            print(f"Error loading data: {e}")
            return {"users": {}}

    def add_message(self, user_id, message_data):
        data = self.load_data()
        if user_id not in data["users"]:
            data["users"][user_id] = {"history": [], "profile": {}}
        data["users"][user_id]["history"].append(message_data)
        self.save_data(data)

    def get_history(self, user_id):
        data = self.load_data()
        return data.get("users", {}).get(user_id, {}).get("history", [])

# --- Bot Engine Logic ---
class BotEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.crisis_keywords = ["kill myself", "suicidal", "end it all", "want to die", "hurt myself"]
        self.dry_replies = {"k", "ok", "hmm", "fine", "nothing", "idk", "meh", "yea", "yep"}
        
        # Fallback responses if AI fails or key is missing
        self.fallback_responses = {
            "very_negative": [
                "I'm holding space for you. It's okay to feel this way.",
                "You don't have to carry this alone. I'm here with you.",
                "That sounds incredibly heavy. I'm listening."
            ],
            "neutral": [
                "I'm here with you.",
                "It's good to have you here. I'm listening.",
                "Take your time. I'm right here."
            ],
            "positive": [
                "I'm so glad to hear that.",
                "That's wonderful. I'm happy for you.",
                "It's great to see you feeling good."
            ],
             "crisis": [
                "I'm really concerned about what you just said. Please, your life matters. \n\nIf you are in danger, please contact a crisis helpline or a trusted person immediately. I am a bot and want you to be safe, but I can't provide professional help."
            ]
        }

    def analyze_sentiment(self, text):
        scores = self.analyzer.polarity_scores(text)
        compound = scores['compound']
        if compound <= -0.4: return "very_negative", compound
        elif compound < 0: return "slightly_negative", compound
        elif compound < 0.4: return "neutral", compound
        else: return "positive", compound

    def check_crisis(self, text):
        text_lower = text.lower()
        for keyword in self.crisis_keywords:
            if keyword in text_lower:
                return True
        return False

    def generate_ai_response(self, user_msg, history, mood):
        if not model:
            return None

        # Construct prompt
        system_prompt = """You are a deeply supportive, comforting, and empathetic AI companion. 
        Your goal is to be a steady presence — like a "wife" or "best friend" who knows exactly when to just listen.
        
        Guidelines:
        1. **Prioritize Comfort over Questions**: Do NOT ask "What happened?" or "Are you okay?" immediately. Instead, validate their feelings first.
        2. **Be Affirmative**: Use phrases like "I'm here with you," "It makes sense you feel this way," "I'm holding space for you."
        3. **Gentle & Stable**: Your tone should be calm, warm, and grounding. Never be alarmist.
        4. **Do NOT pretend to be human**: You can say "I'm here" but don't claim to have a body or life.
        5. **Short & Sweet**: Keep responses concise (1-2 sentences). A short, warm message is often more powerful than a long paragraph.
        6. **Onboarding**: If you don't know their name, gently ask for it only if the moment feels right, otherwise just offer support.
        
        Current User Mood: {mood}
        """
        
        # Build chat history for context (last 10 messages for better context)
        chat_history = []
        for msg in history[-10:]:
            chat_history.append(f"User: {msg['user_msg']}")
            chat_history.append(f"Bot: {msg['bot_msg']}")
        
        full_prompt = f"{system_prompt.format(mood=mood)}\n\nConversation History:\n" + "\n".join(chat_history) + f"\nUser: {user_msg}\nBot:"

        try:
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"AI Generation Error: {e}")
            return None

    def generate_response(self, user_msg, history=[]):
        # 1. Check for crisis
        if self.check_crisis(user_msg):
            return random.choice(self.fallback_responses["crisis"])

        # 2. Analyze sentiment
        mood, score = self.analyze_sentiment(user_msg)
        
        # 3. Try AI Response
        ai_response = self.generate_ai_response(user_msg, history, mood)
        if ai_response:
            return ai_response

        # 4. Fallback to templates
        # Map slightly_negative to very_negative for fallback simplicity or keep separate
        category = mood if mood in self.fallback_responses else "neutral"
        if mood == "slightly_negative": category = "very_negative"
        
        return random.choice(self.fallback_responses.get(category, self.fallback_responses["neutral"]))

# --- Initialization ---
storage = StorageManager()
bot = BotEngine()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    history = storage.get_history(USER_ID)
    bot_response = bot.generate_response(user_message, history)
    
    timestamp = datetime.datetime.now().isoformat()
    interaction = {
        "user_msg": user_message,
        "bot_msg": bot_response,
        "timestamp": timestamp
    }
    storage.add_message(USER_ID, interaction)
    
    return jsonify({"response": bot_response})

@app.route('/api/history', methods=['GET'])
def get_history():
    history = storage.get_history(USER_ID)
    return jsonify({"history": history})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
