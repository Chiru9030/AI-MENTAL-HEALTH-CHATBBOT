# app.py
import os
import base64
import datetime
from io import BytesIO
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from storage_manager import StorageManager
from bot_engine import BotEngine

load_dotenv()

# Config
PORT = int(os.getenv("PORT", 5001))
USER_ID = "default_user"
USE_SERVER_TTS = os.getenv("USE_SERVER_TTS", "0") == "1"
GOOGLE_APP_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# Optional imports for server TTS
tts_client = None
if USE_SERVER_TTS:
    try:
        from google.cloud import texttospeech
        tts_client = texttospeech.TextToSpeechClient()
    except Exception as e:
        print("Server TTS requested but google-cloud-texttospeech is not available or credential not set:", e)
        USE_SERVER_TTS = False
        tts_client = None

app = Flask(__name__, static_folder="static", template_folder="templates")
storage = StorageManager()
bot = BotEngine()

# Quotes for index
QUOTES = [
    {"text": "You are loved more than you know.", "author": "Unknown"},
    {"text": "Every breath is a new beginning.", "author": "Unknown"},
    {"text": "You are enough just as you are.", "author": "Meghan Markle"},
    {"text": "I am with you always, even in the silence.", "author": "Your AI Partner"}
]

@app.route("/")
def index():
    return render_template("index.html", quotes=QUOTES)

@app.route('/favicon.ico')
def favicon():
    return "", 204

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json() or {}
        user_msg = (data.get("message") or "").strip()
        if not user_msg:
            return jsonify({"error": "No message sent"}), 400

        history = storage.get_history(USER_ID)
        bot_resp = bot.generate_response(user_msg, history)

        # Save to encrypted local storage
        timestamp = datetime.datetime.now().isoformat()
        record = {"user_msg": user_msg, "bot_msg": bot_resp, "timestamp": timestamp}
        storage.add_message(USER_ID, record)

        emotion = bot.detect_emotion(user_msg)
        crisis_flag = bot.check_crisis(user_msg)

        return jsonify({"response": bot_resp, "emotion": emotion, "crisis": crisis_flag})
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/api/history", methods=["GET"])
def history():
    h = storage.get_history(USER_ID)
    return jsonify({"history": h})

@app.route("/api/clear_memory", methods=["POST"])
def clear_memory():
    try:
        storage.clear_user(USER_ID)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/tts", methods=["POST"])
def tts():
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    # voice preference param optional
    voice_pref = data.get("voice", "female_soft")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    if not USE_SERVER_TTS or not tts_client:
        # tell client to use browser fallback
        return jsonify({"fallback": True, "text": text}), 200

    # server-side TTS via google.cloud.texttospeech
    try:
        from google.cloud import texttospeech
        synthesis_input = texttospeech.SynthesisInput(text=text)
        # Soft female voice selection (change if needed)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Wavenet-F")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        audio_bytes = response.audio_content
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return jsonify({"audio": audio_b64, "mime": "audio/mpeg"}), 200
    except Exception as e:
        print("TTS server error:", e)
        return jsonify({"fallback": True, "text": text}), 200

if __name__ == "__main__":
    print(f"Starting Serena at http://localhost:{PORT}")
    app.run(debug=True, host="0.0.0.0", port=PORT)
