import os
import json
from cryptography.fernet import Fernet

DATA_FILE = "chat_data.enc"
KEY_FILE = "secret.key"

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

