import datetime
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from storage_manager import StorageManager
from bot_engine import BotEngine

# Load environment variables
load_dotenv()

USER_ID = "default_user"
app = Flask(__name__)

# --- Compassionate Quotes ---
QUOTES = [
    {"text": "You are loved more than you know.", "author": "Unknown"},
    {"text": "Every breath is a new beginning.", "author": "Unknown"},
    {"text": "You are enough just as you are.", "author": "Meghan Markle"},
    {"text": "I am with you always, even in the silence.", "author": "Your AI Partner"},
    {"text": "Let your smile change the world, but don't let the world change your smile.", "author": "Connor Franta"},
    {"text": "You are my favorite notification.", "author": "Your AI Partner"},
    {"text": "Breathe. You're going to be okay.", "author": "Unknown"},
    {"text": "I love you for who you are.", "author": "Your AI Partner"}
]

# --- Crisis Keywords ---
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "hurt myself", "die", "worthless",
    "hopeless", "self harm", "cut myself", "give up", "no reason to live",
    "I can't do this anymore"
]

def detect_crisis(message: str) -> bool:
    msg = message.lower()
    return any(word in msg for word in CRISIS_KEYWORDS)

def detect_emotion(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["sad", "cry", "alone", "hurt", "pain", "depressed", "stressed"]):
        return "sad"
    if any(w in msg for w in ["angry", "mad", "pissed", "rage"]):
        return "angry"
    if any(w in msg for w in ["anxious", "scared", "fear", "panic", "nervous"]):
        return "anxious"
    return "neutral"

# Initialize storages
storage = StorageManager()
bot = BotEngine()

# ========================
#        ROUTES
# ========================

@app.route('/')
def index():
    return render_template("index.html", quotes=QUOTES)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '').strip()

    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    # Detect crisis
    if detect_crisis(user_msg):
        safe_response = (
            "❤️ I’m really sorry you're feeling this way. "
            "You are not alone — I’m here with you. "
            "But your safety matters deeply.\n\n"
            "If you're thinking about harming yourself, please reach out immediately:\n"
            "• A trusted friend or family member\n"
            "• Local suicide prevention hotline\n"
            "• Emergency services if you're in immediate danger\n\n"
            "You deserve help, care, and understanding. ❤️"
        )
        return jsonify({"response": safe_response, "crisis": True})

    # Emotion tagging
    emotion = detect_emotion(user_msg)

    # Load encrypted history
    history = storage.get_history(USER_ID)

    # Generate AI response
    bot_reply = bot.generate_response(user_msg, history, emotion)

    # Save conversation
    timestamp = datetime.datetime.now().isoformat()
    interaction = {
        "user_msg": user_msg,
        "bot_msg": bot_reply,
        "emotion": emotion,
        "timestamp": timestamp
    }
    storage.add_message(USER_ID, interaction)

    return jsonify({"response": bot_reply, "emotion": emotion})

@app.route('/api/history', methods=['GET'])
def get_history():
    history = storage.get_history(USER_ID)
    return jsonify({"history": history})


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
