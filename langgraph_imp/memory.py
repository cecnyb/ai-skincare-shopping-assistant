import json
import os
import threading
import time
from typing import Any, Dict


class SimpleMemoryStore:
    """
    JSON-like store keyed by user_id. Supports:
      - path=None → in-memory only (ephemeral)
      - reset_on_start=True → truncate file on init
      - namespace="..." → isolate sessions inside one file
    """
    """ JSON file keyed by user_id. Structure: { "<user_id>": { "profile": { "skin_type": "dry|oily|combination|sensitive|normal", "concerns": ["redness","acne",...], "allergies": ["fragrance","alcohol",...], "pref_ingredients": ["niacinamide","ceramide",...], "avoid_ingredients": ["retinol",...], "budget_krw_max": 30000, "brand_prefs": ["BrandA","BrandB"] }, "history": [ {"role":"user","text":"..."}, {"role":"agent","text":"..."} ], "meta": {"created_ts": 0, "updated_ts": 0} }, ... } """
    def __init__(self, path: str | None = "memory_store.json", history_max: int = 8,
                 reset_on_start: bool = False, namespace: str = ""):
        self.path = path
        self.history_max = history_max
        self.namespace = namespace  # optional session/app instance id
        self._lock = threading.Lock()
        self._data = {}  # used when path is None (RAM only)

        if self.path is None:
            # Ephemeral mode: no disk I/O at all
            return

        # File-backed mode
        if reset_on_start and os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({}, f)

        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_all(self) -> Dict[str, Any]:
        if self.path is None:
            return self._data
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_all(self, data: Dict[str, Any]) -> None:
        if self.path is None:
            self._data = data
            return
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def _ns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # if namespace is set, isolate each app reload/instance under that key
        if not self.namespace:
            return data
        if self.namespace not in data:
            data[self.namespace] = {}
        return data[self.namespace]

    def get_user(self, user_id: str) -> Dict[str, Any]:
        with self._lock:
            data = self._load_all()
            root = self._ns(data)
            if user_id not in root:
                root[user_id] = {
                    "profile": {},
                    "history": [],
                    "meta": {"created_ts": time.time(), "updated_ts": time.time()},
                }
                self._save_all(data)
            return root[user_id]

    def save_user(self, user_id: str, payload: Dict[str, Any]) -> None:
        with self._lock:
            data = self._load_all()
            root = self._ns(data)
            root[user_id] = payload
            root[user_id]["meta"]["updated_ts"] = time.time()
            # trim history
            hist = root[user_id].get("history", [])
            if len(hist) > self.history_max:
                root[user_id]["history"] = hist[-self.history_max:]
            self._save_all(data)

    def reset_all(self) -> None:
        """Clear everything (current namespace only if set)."""
        with self._lock:
            if self.path is None:
                self._data = {} if not self.namespace else {self.namespace: {}}
                return
            data = {} if not self.namespace else {self.namespace: {}}
            self._save_all(data)
