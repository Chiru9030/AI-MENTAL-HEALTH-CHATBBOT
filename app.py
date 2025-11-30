import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from storage_manager import StorageManager
from bot_engine import BotEngine

# Load environment variables
load_dotenv()

# --- Configuration ---
USER_ID = "default_user"

app = Flask(__name__)

# --- Quotes Data ---
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

# --- Initialization ---
storage = StorageManager()
bot = BotEngine()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html', quotes=QUOTES)

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
