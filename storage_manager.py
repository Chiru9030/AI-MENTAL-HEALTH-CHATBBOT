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

    # --------------------------------------
    # KEY MANAGEMENT
    # --------------------------------------
    def _load_or_create_key(self):
        """Loads the encryption key or creates a new one if missing."""
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                return f.read()

        # Create a new encryption key
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

    # --------------------------------------
    # FILE INITIALIZATION
    # --------------------------------------
    def _ensure_data_file(self):
        """Ensures encrypted data file exists with proper structure."""
        if not os.path.exists(DATA_FILE):
            initial = {"users": {}}
            self._save_encrypted(initial)

    # --------------------------------------
    # INTERNAL ENCRYPTED SAVE/LOAD
    # --------------------------------------
    def _save_encrypted(self, data):
        try:
            raw = json.dumps(data).encode()
            encrypted = self.cipher.encrypt(raw)
            with open(DATA_FILE, "wb") as f:
                f.write(encrypted)
        except Exception as e:
            print("Storage Save Error:", e)

    def _load_encrypted(self):
        """Reads encrypted data and safely returns decrypted JSON."""
        if not os.path.exists(DATA_FILE):
            return {"users": {}}

        try:
            with open(DATA_FILE, "rb") as f:
                encrypted = f.read()
                if not encrypted:
                    return {"users": {}}

            decrypted = self.cipher.decrypt(encrypted).decode()
            return json.loads(decrypted)

        except Exception as e:
            print("Storage Load Error:", e)
            return {"users": {}}

    # --------------------------------------
    # PUBLIC METHODS USED BY APP/BOT
    # --------------------------------------
    def add_message(self, user_id, msg):
        """Adds a new chat message for a user."""
        data = self._load_encrypted()

        if user_id not in data["users"]:
            data["users"][user_id] = {"history": []}

        data["users"][user_id]["history"].append(msg)
        self._save_encrypted(data)

    def get_history(self, user_id):
        """Returns chat history for a user."""
        data = self._load_encrypted()
        return data.get("users", {}).get(user_id, {}).get("history", [])
