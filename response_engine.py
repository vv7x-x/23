"""
response_engine.py

Generates replies using templates, style profiles, and intent.
Implements anti-spam responses and whatsapp request handling.
"""
import random
from typing import Dict


class ResponseEngine:
    def __init__(self, memory_manager, style_engine, personality_engine):
        self.memory = memory_manager
        self.style = style_engine
        self.personality = personality_engine

        # Base template pools per intent
        self.templates = {
            "greeting": [
                "هاى، عامل ايه؟",
                "يا اهلا، اي اخبارك؟",
                "هلو — خير؟"
            ],
            "flirting": [
                "مش معقول، بتحاول تجيب مني؟",
                "انت بتتكلم ازاي، ده خادش للحياء 😏",
                "بس خلاص، هتعبنا كده" 
            ],
            "asking_for_whatsapp": [
                # Must never send number automatically
                "ممكن اعرف ليه محتاج الواتس؟",
                "انا ماسح إنستا ومبخش كتير، ممكن تقول السبب؟",
                "لو عايز تبعت صور بلاش واتس، ابعت هنا" 
            ],
            "spam": [
                "مش محتاج دلوقتي، بلاش سبام.",
                "تباطل بقى، spam مش مسموح هنا." 
            ],
            "joke": [
                "هاها، صح.",
                "ضحكت من قلبي (تقريبا)." 
            ],
            "serious_question": [
                "تمام: هجاوب عليك ببساطة.",
                "خليك واضح أكتر عشان ارد." 
            ],
            "boring_small_talk": [
                "ايه تحب تدردش؟",
                "مش فاضي دلوقتي بس اكتب" 
            ],
            "small_talk": [
                "كويس، و انت؟",
                "حلو الكلام دا، كمل" 
            ]
        }

    def generate_reply(self, user_id: str, other_id: str, incoming_text: str, intent: str) -> str:
        # Load or compute profile
        profile = self.memory.load_profile(user_id, other_id)
        if not profile:
            profile = self.style.calculate_profile(user_id, other_id)
            self.memory.save_profile(user_id, other_id, profile)

        pool = self.templates.get(intent) or self.templates.get("small_talk")
        template = random.choice(pool)

        # Apply variations
        reply = self._fill_template(template, incoming_text, profile, intent)
        reply = self._apply_energy_and_length(reply, profile)
        reply = self.personality.apply_personality(reply, profile, intent)
        return reply

    def _fill_template(self, template: str, incoming: str, profile: Dict, intent: str) -> str:
        # Simple variable substitution and contextual tweaks
        t = template
        if "{name}" in t:
            # crude name extraction
            name = incoming.split()[0] if incoming else ""
            t = t.replace("{name}", name)
        return t

    def _apply_energy_and_length(self, text: str, profile: Dict) -> str:
        # If owner tends to short replies, shorten
        avg = profile.get("average_length", 40)
        if avg < 30 and len(text) > avg:
            return text.split('.')[0][:avg] + '.'
        return text

    def handle_whatsapp_request(self, user_id: str, other_id: str, count: int) -> str:
        # Never send number automatically. If explicit consent request (count high), escalate sarcasm.
        if count == 1:
            return "لو فعلا محتاج، قول السبب وانا اشوف." 
        if count <= 3:
            return "انا ماسح إنستا ومبخش كتير — مش حابة اشارك رقمي كده." 
        # escalation
        return "بتكرر طلب الواتس؟ خلاص انت قليل الادب — مش هبعت رقمك." 

    def handle_spam(self, user_id: str, other_id: str) -> str:
        # Gentle roast
        roasts = [
            "توقف عن الspam بقى يا عم.",
            "لو عندك حاجة مهمة قولها بدل الـ spam.",
            "خلاص، عملتلك بلوك مؤقت (مش حقيقي بس)."
        ]
        return random.choice(roasts)
