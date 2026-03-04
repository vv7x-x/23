"""
personality_engine.py

Defines the base personality for n0x and utilities to adapt tone.
"""
import random


class PersonalityEngine:
    def __init__(self):
        # Base personality attributes
        self.base_personality = {
            "voice": "calm_sarcastic_egyptian_genz",
            "never_say_ai": True,
            "style": "smart_playful_arrogant"
        }

    def apply_personality(self, text: str, profile: dict, intent: str) -> str:
        """Apply personality transformations to a reply template.
        This is rule-based: inserts sarcastic tags, Egyptian slang, and keeps tone.
        """
        # Short transformations based on profile
        res = text
        # If sarcasm level high, add sarcastic punctuation/phrases
        if profile.get("sarcasm_level", 1) >= 3:
            res = self._add_sarcasm(res)

        # If emoji density high, maybe append emoji
        if profile.get("emoji_density", 0) > 0.1 and random.random() < 0.6:
            res += " 😏"

        # Small Egyptian Gen-Z flavor phrases
        if random.random() < 0.4:
            res = self._insert_egyptian_flavor(res)

        # Ensure never say AI
        res = res.replace("I'm an AI", "Nope.")
        return res

    def _add_sarcasm(self, t: str) -> str:
        choices = ["Nice.", "Wow, what a surprise.", "قول كده تاني؟"]
        return t + " " + random.choice(choices)

    def _insert_egyptian_flavor(self, t: str) -> str:
        inserts = ["ya3ni", "yalla", "msh kda?", "bta3tna keda"]
        if random.random() < 0.5:
            return t + " " + random.choice(inserts)
        return random.choice(inserts) + " " + t
