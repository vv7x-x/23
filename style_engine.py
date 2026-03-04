"""
style_engine.py

Analyze owner's messages per-conversation and build a style profile.
Recalculate every N messages (default 10) using weighted scoring.
"""
import re
import math
from collections import Counter
from typing import Dict


class StyleEngine:
    def __init__(self, memory_manager, recalc_every: int = 10):
        self.memory = memory_manager
        self.recalc_every = recalc_every

    def maybe_recalculate(self, user_id: str):
        # Recalculate profiles for every conversation of the user if needed
        others = self.memory.list_conversations(user_id)
        for other in others:
            owner_count = self.memory.get_owner_message_count(user_id, other)
            if owner_count and owner_count % self.recalc_every == 0:
                profile = self.calculate_profile(user_id, other)
                self.memory.save_profile(user_id, other, profile)

    def calculate_profile(self, user_id: str, other_id: str) -> Dict:
        msgs = self.memory.get_owner_messages(user_id, other_id)
        if not msgs:
            # Default neutral profile
            profile = {
                "emoji_density": 0.0,
                "slang_level": 1,
                "formality_level": 1,
                "average_length": 20,
                "energy_level": 1,
                "sarcasm_level": 1,
            }
            return profile

        total = len(msgs)
        lengths = [len(m) for m in msgs]
        avg_len = int(sum(lengths) / total)

        emoji_count = sum(self._count_emojis(m) for m in msgs)
        emoji_density = emoji_count / max(1, sum(max(1, len(m.split())) for m in msgs))

        slang_score = sum(self._slang_score(m) for m in msgs) / total
        formality = 1.0 - (slang_score / 5.0)

        energy = sum(self._energy_score(m) for m in msgs) / total
        sarcasm = sum(self._sarcasm_score(m) for m in msgs) / total

        profile = {
            "emoji_density": round(emoji_density, 3),
            "slang_level": int(max(0, min(5, round(slang_score)))),
            "formality_level": int(max(0, min(5, round(formality * 5)))),
            "average_length": int(avg_len),
            "energy_level": int(max(0, min(5, round(energy)))),
            "sarcasm_level": int(max(0, min(5, round(sarcasm))))
        }
        return profile

    def _count_emojis(self, text: str) -> int:
        # Very simple emoji detection using common unicode ranges
        return len(re.findall(r"[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\u2600-\u26FF]", text))

    def _slang_score(self, text: str) -> int:
        # basic slang detection: presence of common slang words (English/Arabic translit)
        slang_words = ["brb", "lol", "omg", "ya", "yalla", "habibi", "bsa7", "bt3" ]
        t = text.lower()
        score = 0
        for w in slang_words:
            if w in t:
                score += 1
        # presence of repeated letters as informal marker
        if re.search(r"(.)\1{2,}", text):
            score += 1
        return min(5, score)

    def _energy_score(self, text: str) -> int:
        # exclamation marks and length as proxy for energy
        e = text.count("!") + text.count("؟")
        if len(text) > 120:
            e += 2
        if e <= 0:
            return 1
        return min(5, e)

    def _sarcasm_score(self, text: str) -> int:
        # naive sarcasm detection via punctuation and keywords
        sarcasm_cues = ["sure", "right", "cool", "obviously", "as if"]
        score = 0
        t = text.lower()
        for c in sarcasm_cues:
            if c in t:
                score += 1
        if "..." in text:
            score += 1
        return min(5, score)
