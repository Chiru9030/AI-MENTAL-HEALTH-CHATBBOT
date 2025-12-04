import datetime
import os
import json
from flask import Flask, render_template, request, jsonify, send_file, abort
from dotenv import load_dotenv
from storage_manager import StorageManager
from bot_engine import BotEngine
from io import BytesIO

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
USER_ID = "default_user"

# Initialize
storage = StorageManager()
bot = BotEngine()

# Optional server-side TTS config:
# Two supported server-side flows:
# 1) GOOGLE_APPLICATION_CREDENTIALS env variable pointing to a service account JSON + google-cloud-texttospeech installed
# 2) If not configured, server returns fallback JSON and frontend uses browser TTS.
USE_SERVER_TTS = os.getenv("USE_SERVER_TTS", "0") == "1"

# Try to import google cloud text-to-speech optionally
tts_client = None
if USE_SERVER_TTS:
    try:
        from google.cloud import texttospeech
        tts_client = texttospeech.TextToSpeechClient()
    except Exception as e:
        print("Server TTS requested but google-cloud-texttospeech not available or credentials missing:", e)
        tts_client = None

# Quotes for UI
QUOTES = [
    {"text": "You are loved more than you know.", "author": "Unknown"},
    {"text": "Every breath is a new beginning.", "author": "Unknown"},
    {"text": "You are enough just as you are.", "author": "Meghan Markle"},
    {"text": "I am with you always, even in the silence.", "author": "Your AI Partner"}
]

@app.route('/')
def index():
    return render_template('index.html', quotes=QUOTES)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_message = data.get('message','').strip()
    if not user_message:
        return jsonify({"error":"No message provided"}), 400

    # Load history
    history = storage.get_history(USER_ID)

    # Generate bot response
    # If bot.generate_response expects only (user_msg, history)
    bot_response = bot.generate_response(user_message, history)

    # Save interaction
    timestamp = datetime.datetime.now().isoformat()
    interaction = {"user_msg": user_message, "bot_msg": bot_response, "timestamp": timestamp}
    storage.add_message(USER_ID, interaction)

    # Determine emotion (use bot.detect_emotion)
    emotion = "neutral"
    try:
        emotion = bot.detect_emotion(user_message)
    except Exception:
        emotion = "neutral"

    # Crisis detection
    crisis_flag = bot.check_crisis(user_message)

    return jsonify({"response": bot_response, "emotion": emotion, "crisis": crisis_flag})

@app.route('/api/history', methods=['GET'])
def get_history():
    history = storage.get_history(USER_ID)
    return jsonify({"history": history})

@app.route('/api/clear_memory', methods=['POST'])
def clear_memory():
    # For demo we simply overwrite with empty users object
    try:
        storage._save_encrypted({"users": {}})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def tts():
    """
    Server-side TTS endpoint.
    If server-side TTS is configured (USE_SERVER_TTS=1 and google cloud credentials set),
    this will synthesize audio (MP3) and return as binary.
    Otherwise returns JSON fallback {"fallback": true} so client uses browser TTS.
    """
    data = request.json or {}
    text = data.get("text","").strip()
    if not text:
        return jsonify({"error":"No text provided"}), 400

    if not USE_SERVER_TTS or tts_client is None:
        # tell client to fallback to browser TTS
        return jsonify({"fallback": True, "text": text}), 200

    try:
        from google.cloud import texttospeech
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Wavenet-D")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        mp3_data = response.audio_content
        return send_file(BytesIO(mp3_data), mimetype="audio/mpeg", as_attachment=False, attachment_filename="serena.mp3")
    except Exception as e:
        print("Server TTS error:", e)
        return jsonify({"fallback": True, "text": text}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
