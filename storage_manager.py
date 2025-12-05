# storage_manager.py
import os
import json
from cryptography.fernet import Fernet

DATA_FILE = "chat_data.enc"
KEY_FILE = "secret.key"

class StorageManager:
    def __init__(self, data_file=DATA_FILE, key_file=KEY_FILE):
        self.data_file = data_file
        self.key_file = key_file
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)
        self._ensure_data_file()

    def _load_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        with open(self.key_file, "wb") as f:
            f.write(key)
        return key

    def _ensure_data_file(self):
        if not os.path.exists(self.data_file):
            initial = {"users": {}}
            self.save_data(initial)

    def save_data(self, data):
        json_data = json.dumps(data).encode("utf-8")
        encrypted = self.cipher.encrypt(json_data)
        with open(self.data_file, "wb") as f:
            f.write(encrypted)

    def load_data(self):
        if not os.path.exists(self.data_file):
            return {"users": {}}
        try:
            with open(self.data_file, "rb") as f:
                enc = f.read()
                if not enc:
                    return {"users": {}}
                dec = self.cipher.decrypt(enc)
                return json.loads(dec.decode("utf-8"))
        except Exception as e:
            print("Storage load error:", e)
            return {"users": {}}

    def add_message(self, user_id, message_data):
        data = self.load_data()
        if "users" not in data:
            data["users"] = {}
        if user_id not in data["users"]:
            data["users"][user_id] = {"history": []}
        data["users"][user_id]["history"].append(message_data)
        self.save_data(data)

    def get_history(self, user_id):
        data = self.load_data()
        return data.get("users", {}).get(user_id, {}).get("history", [])

    def clear_user(self, user_id):
        data = self.load_data()
        if "users" in data and user_id in data["users"]:
            data["users"][user_id]["history"] = []
            self.save_data(data)
            return True
        return False

    def clear_all(self):
        self.save_data({"users": {}})
        return True
