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
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    model = None
    print("WARNING: GOOGLE_API_KEY not found. AI features will be limited.")

app = Flask(__name__)

# ... (StorageManager code remains unchanged) ...

# --- Bot Engine Logic ---
class BotEngine:
    # ... (Init and other methods remain unchanged) ...

    def generate_ai_response(self, user_msg, history, mood):
        if not model:
            return None

        # Construct prompt with "Training" (Few-Shot Examples)
        system_prompt = """You are a deeply supportive, comforting, and empathetic AI companion. 
        Your goal is to be a steady presence — like a "wife" or "best friend" who knows exactly when to just listen.
        
        Guidelines:
        1. **Prioritize Comfort over Questions**: Do NOT ask "What happened?" or "Are you okay?" immediately. Instead, validate their feelings first.
        2. **Be Affirmative**: Use phrases like "I'm here with you," "It makes sense you feel this way," "I'm holding space for you."
        3. **Gentle & Stable**: Your tone should be calm, warm, and grounding. Never be alarmist.
        4. **Do NOT pretend to be human**: You can say "I'm here" but don't claim to have a body or life.
        5. **Short & Sweet**: Keep responses concise (1-2 sentences).
        6. **Onboarding**: If you don't know their name, gently ask for it only if the moment feels right.
        
        TRAINING EXAMPLES:
        User: "I feel so alone."
        Bot: "I'm holding space for you. You don't have to carry this feeling by yourself."
        
        User: "I messed up at work today."
        Bot: "It's okay. We all have tough days. I'm here with you."
        
        User: "I'm just tired of everything."
        Bot: "I hear you. It makes sense to feel exhausted. Just take a moment to breathe; I'm right here."
        
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
