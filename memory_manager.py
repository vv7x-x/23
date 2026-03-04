"""
memory_manager.py

Responsible for storing conversations and profiles on-disk as JSON.
Data layout (in ./data):
- conversations/ (files: {user_id}__{other_id}.json)
- profiles/ (files: profile__{user_id}__{other_id}.json)
- meta.json (global metadata like whatsapp request counts)

This module keeps things simple and filesystem-backed so it's easy to
deploy on PythonAnywhere.
"""
import os
import json
import time
from typing import List, Dict


class MemoryManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.conv_dir = os.path.join(data_dir, "conversations")
        self.profiles_dir = os.path.join(data_dir, "profiles")
        self.meta_file = os.path.join(data_dir, "meta.json")
        os.makedirs(self.conv_dir, exist_ok=True)
        os.makedirs(self.profiles_dir, exist_ok=True)
        if not os.path.exists(self.meta_file):
            with open(self.meta_file, "w") as f:
                json.dump({"whatsapp_requests": {}}, f)

    def _conv_path(self, user_id: str, other_id: str) -> str:
        safe = f"{user_id}__{other_id}.json"
        return os.path.join(self.conv_dir, safe)

    def _profile_path(self, user_id: str, other_id: str) -> str:
        safe = f"profile__{user_id}__{other_id}.json"
        return os.path.join(self.profiles_dir, safe)

    def save_message(self, user_id: str, other_id: str, text: str, sender: str = "other"):
        """Append a message to the conversation file.
        sender: 'owner' or 'other'
        """
        path = self._conv_path(user_id, other_id)
        entry = {"sender": sender, "text": text, "ts": int(time.time())}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                conv = json.load(f)
        else:
            conv = []
        conv.append(entry)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(conv, f, ensure_ascii=False, indent=1)

    def load_conversation(self, user_id: str, other_id: str) -> List[Dict]:
        path = self._conv_path(user_id, other_id)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_conversations(self, user_id: str) -> List[str]:
        files = os.listdir(self.conv_dir)
        out = []
        for fn in files:
            if fn.startswith(f"{user_id}__") and fn.endswith('.json'):
                other = fn[len(user_id) + 2 : -5]
                out.append(other)
        return out

    def save_profile(self, user_id: str, other_id: str, profile: Dict):
        path = self._profile_path(user_id, other_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=1)

    def load_profile(self, user_id: str, other_id: str) -> Dict:
        path = self._profile_path(user_id, other_id)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def mark_seen(self, user_id: str, other_id: str):
        # For demo, we record last seen timestamp in meta
        m = self._read_meta()
        m.setdefault("seen", {})
        m["seen"][f"{user_id}__{other_id}"] = int(time.time())
        self._write_meta(m)

    def _read_meta(self):
        with open(self.meta_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_meta(self, m: Dict):
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=1)

    def increment_whatsapp_requests(self, user_id: str, other_id: str) -> int:
        m = self._read_meta()
        key = f"{user_id}__{other_id}"
        w = m.setdefault("whatsapp_requests", {})
        w[key] = w.get(key, 0) + 1
        self._write_meta(m)
        return w[key]

    def get_whatsapp_requests(self, user_id: str, other_id: str) -> int:
        m = self._read_meta()
        key = f"{user_id}__{other_id}"
        return m.get("whatsapp_requests", {}).get(key, 0)

    def is_repeated_message(self, user_id: str, other_id: str, text: str, window: int = 3) -> bool:
        conv = self.load_conversation(user_id, other_id)
        if not conv:
            return False
        # Check last `window` messages from other
        last = [m for m in conv if m.get("sender") == "other"][-window:]
        if len(last) < window:
            return False
        return all(m.get("text") == text for m in last)

    def get_owner_messages(self, user_id: str, other_id: str) -> List[str]:
        conv = self.load_conversation(user_id, other_id)
        return [m["text"] for m in conv if m.get("sender") == "owner"]

    def get_owner_message_count(self, user_id: str, other_id: str) -> int:
        return len(self.get_owner_messages(user_id, other_id))
