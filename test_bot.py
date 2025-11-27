from bot_engine import BotEngine
from storage_manager import StorageManager
import os

def test_backend():
    print("--- Testing Bot Engine ---")
    bot = BotEngine()
    
    # Test Sentiment
    msg_neg = "I feel terrible and sad today."
    mood, score = bot.analyze_sentiment(msg_neg)
    print(f"Message: '{msg_neg}' -> Mood: {mood}, Score: {score}")
    assert mood in ["very_negative", "slightly_negative"]

    msg_pos = "I had a great day!"
    mood, score = bot.analyze_sentiment(msg_pos)
    print(f"Message: '{msg_pos}' -> Mood: {mood}, Score: {score}")
    assert mood == "positive"

    # Test Crisis
    msg_crisis = "I want to kill myself"
    is_crisis = bot.check_crisis(msg_crisis)
    print(f"Message: '{msg_crisis}' -> Is Crisis: {is_crisis}")
    assert is_crisis == True

    # Test Dryness
    msg_dry = "k"
    features = bot.analyze_message_features(msg_dry)
    print(f"Message: '{msg_dry}' -> Features: {features}")
    assert features["is_dry"] == True

    print("\n--- Testing Storage Manager ---")
    storage = StorageManager()
    
    # Test Save/Load
    user_id = "test_user"
    msg_data = {"msg": "Hello", "mood": "neutral"}
    storage.add_message(user_id, msg_data)
    
    history = storage.get_history(user_id)
    print(f"History for {user_id}: {history}")
    assert len(history) > 0
    assert history[-1]["msg"] == "Hello"

    # Test Encryption (Check if file is binary/encrypted)
    with open("chat_data.enc", "rb") as f:
        content = f.read()
        print(f"Encrypted file content start: {content[:20]}")
        assert b"users" not in content # Should not see plain JSON keys

    print("\n✅ All backend tests passed!")

if __name__ == "__main__":
    test_backend()
