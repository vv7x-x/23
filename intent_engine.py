"""
intent_engine.py

Rule-based intent detection per the requirements. No external AI.
"""
import re


class IntentEngine:
    def __init__(self):
        # simple regex rules for intents
        self.greetings = re.compile(r"\b(hi|hello|hey|salaam|سلام|yo)\b", re.I)
        self.whatsapp = re.compile(r"(whatsap|wahtsapp|whatsapp|واتساب|واتس|رقم|phone|num)", re.I)
        self.flirt = re.compile(r"\b(love|😍|beautiful|pretty|hot|bae|crush)\b", re.I)
        self.spam_like = re.compile(r"^(free|visit|click|buy|http|www\.)", re.I)
        self.joke = re.compile(r"\b(joke|lol|😂|🤣)\b", re.I)
        self.serious = re.compile(r"\b(why|how|when|where|what|serious|really)\b", re.I)

    def detect(self, text: str) -> str:
        t = text.strip()
        if not t:
            return "boring_small_talk"
        if self.spam_like.search(t):
            return "spam"
        if self.whatsapp.search(t):
            # if explicit 'send number' pattern
            if re.search(r"(send|give|share).*(whatsapp|number|num|رقم)", t, re.I):
                return "asking_for_whatsapp"
            return "asking_for_whatsapp"
        if self.greetings.search(t):
            return "greeting"
        if self.flirt.search(t):
            return "flirting"
        if self.joke.search(t):
            return "joke"
        if self.serious.search(t):
            return "serious_question"
        # fallback simple rules
        if len(t.split()) <= 3:
            return "boring_small_talk"
        return "small_talk"
