import time
import random
import os
from datetime import datetime

# Allow running lightweight tests without installing external deps
TEST_MODE = os.environ.get("TEST_MODE") == "1"

if not TEST_MODE:
    import google.generativeai as genai
    from instagrapi import Client
else:
    genai = None
    Client = None

# ================== CONFIG ==================
USERNAME = "idk_yahia_"
PASSWORD = "yahya200901"
GEMINI_API_KEY = "AIzaSyBWmZkq5mTn7KabPsBtpR8e9NeXciwbM-o"
PHONE_NUMBER = "01228768422"
IS_CLOSED = True
OWNER_NAME = "يحيى"
SIGNATURE = "— يحيى صاحب الاكونت"

# ================== GEMINI SETUP ==================
if not TEST_MODE:
    genai.configure(api_key=GEMINI_API_KEY)

    generation_config = {
        "temperature": 1.1,
        "top_p": 0.95,
        "max_output_tokens": 700
    }

    model = genai.GenerativeModel(
        "models/gemini-2.5-flash",
        generation_config=generation_config
    )
else:
    model = None
# ================== MEMORY ==================
chat_histories = {}
last_replies = {}
last_reply_time = {}
whatsapp_requests = {}

# ================== INSTA ==================
if not TEST_MODE:
    cl = Client()
else:
    cl = None

# ================== LOGIN ==================
def login_insta():
    try:
        if os.path.exists("n0x_session.json"):
            cl.load_settings("n0x_session.json")
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings("n0x_session.json")
        print("🚀 n0x دخل الساحه")
    except:
        cl.login(USERNAME, PASSWORD)

# ================== ANTI SPAM ==================
def should_reply(user_id):
    now = time.time()
    if user_id in last_reply_time:
        if now - last_reply_time[user_id] < 8:
            return False
    last_reply_time[user_id] = now
    return True

# ================== TYPING ==================
def simulate_typing(thread_id):
    try:
        cl.direct_send_seen(thread_id)
    except:
        pass
    
    try:
        cl.direct_send_typing(thread_id)
    except:
        pass

    time.sleep(random.uniform(2.5, 4.5))

# ================== AI LOGIC ==================
def get_n0x_reply(user_id, user_message):

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    user_lower = user_message.lower()

    # ================== Gender detection ==================
    def determine_gender(text):
        t = text.lower()
        female_markers = ["بنت", "ست", "انثى", "أنا بنت", "انا بنت", "girl", "female", "her", "she", "حبيبتي", "اخت"]
        male_markers = ["ولد", "راجل", "انا ولد", "أنا ولد", "boy", "male", "him", "he", "اخ"]

        for w in female_markers:
            if w in t:
                return "female"

        for w in male_markers:
            if w in t:
                return "male"

        return "unknown"

    gender = determine_gender(user_message)
    if gender == "female":
        salutations = ["يا قمر", "يا أمورة", "يا ست الكل"]
    elif gender == "male":
        salutations = ["يا وحش", "يا برنس", "يا صاح"]
    else:
        salutations = ["يا زميلي", "يا عمدة"]
    sal = random.choice(salutations)

    whatsapp_keywords = [
        "واتس", "واتساب", "whatsapp",
        "رقمك", "رقم", "كلمك برا",
        "نتكلم برا", "ابعت رقمك"
    ]

    is_whatsapp_request = any(word in user_lower for word in whatsapp_keywords)

    # ================== لو طلب الواتس ==================
    if is_whatsapp_request:

        if user_id not in whatsapp_requests:
            whatsapp_requests[user_id] = 0

        whatsapp_requests[user_id] += 1
        count = whatsapp_requests[user_id]

        if count == 1:
            return f"يا عمدة 😏 طالما طلبت باحترام... اهو الرقم: {PHONE_NUMBER}"

        elif count == 2:
            return f"يا وحش هو انت فاكرني بنك؟ 😂 ما هو {PHONE_NUMBER} لسه متبعت من شوية!"

        elif count == 3:
            return f"يا برنس هتحفظه معايا؟ 😏 اكتب ورايا: {PHONE_NUMBER}"

        else:
            return f"{sal} الرقم بقى قصة حب؟ 😂 خلاص اعمله خلفية: {PHONE_NUMBER} \n{SIGNATURE}"

    # ================== رد عادي ==================
    context = "\n".join(chat_histories[user_id][-6:])

    prompt = f"""
أنت n0x.
شخصيتك مستقلة، ساخر، ذكي، دمك خفيف، ومش بتكرر نفسك.
ممنوع تحط رقم واتس نهائي غير لو المستخدم طلبه صراحة.
نادِ المستخدم بألقاب زي: يا عمدة، يا وحش، يا برنس، يا زميلي.
خليك طبيعي وكأنك شخص حقيقي مش AI.

سياق:
{context}

المستخدم: {user_message}
رد n0x:
"""

    try:
        # If running in TEST_MODE or model isn't available, return a simple canned reply
        if TEST_MODE or model is None:
            simulated = f"{sal} نسخة اختبارية: وصلت رسالتك — \"{user_message}\"\n{SIGNATURE}"
            if "مين" in user_lower or "من انت" in user_lower or "مين صاحب" in user_lower:
                simulated = simulated + f"\n{SIGNATURE}"
            return simulated
        # If account is closed, give a creative 'قافل' reply and include owner signature
        closed_keywords = ["متاح", "متاحة", "تقدر", "available", "online", "متكلم", "تكلم", "هل انت"]
        if IS_CLOSED and any(k in user_lower for k in closed_keywords):
            closed_msgs = [
                f"{sal} انا قافل دلوقتي 😴\nمافيش دردشة حالياً، سيب رسالتك و{OWNER_NAME} هيرجع لك بعدين.",
                f"{sal} الحساب قافل ومفصول عن الدنيا 📴\nلو الموضوع عاجل سيب رسالة، {OWNER_NAME} هيشوفها وقت الفلوس 😅"
            ]
            return random.choice(closed_msgs) + f"\n{SIGNATURE}"

        for attempt in range(3):
            response = model.generate_content(prompt)
            reply = response.text.strip()

            if user_id in last_replies and reply == last_replies[user_id]:
                continue

            last_replies[user_id] = reply
            chat_histories[user_id].extend([
                f"مستخدم: {user_message}",
                f"n0x: {reply}"
            ])

            # append owner signature for clarity when user asks who
            if "مين" in user_lower or "من انت" in user_lower or "مين صاحب" in user_lower:
                reply = reply + f"\n\n{SIGNATURE}"

            return reply

        return "يا زميلي مخي عمل لودينج ثانية 😅"

    except Exception as e:
        print("Gemini Error:", e)
        return "الذكاء الصناعي خد بريك خمس ثواني 😎"

# ================== MAIN LOOP ==================
def run_n0x():
    login_insta()
    print("👀 n0x بيراقب الدايركت...")

    while True:
        try:
            threads = cl.direct_threads(selected_filter="unread")

            for thread in threads:
                thread_id = thread.id
                messages = cl.direct_messages(thread_id, amount=1)

                if not messages:
                    continue

                msg = messages[0]

                if msg.user_id != cl.user_id and msg.text:

                    if not should_reply(msg.user_id):
                        continue

                    print(f"\n📩 [{datetime.now().strftime('%H:%M:%S')}] رسالة من {msg.user_id}")
                    print("💬", msg.text)

                    simulate_typing(thread_id)

                    reply = get_n0x_reply(msg.user_id, msg.text)

                    cl.direct_send(reply, thread_ids=[thread_id])

                    try:
                        cl.direct_thread_read_state(thread_id, msg.id)
                    except:
                        pass

                    print("📤 رد n0x:", reply[:80])

                    time.sleep(random.uniform(4, 7))

            time.sleep(5)

        except Exception as e:
            print("⚠️ n0x بيشرب شاي:", e)
            time.sleep(15)

# ================== START ==================
if __name__ == "__main__":
    # Safe testing mode: run sample inputs locally without logging into Instagram
    if os.environ.get("TEST_MODE") == "1":
        samples = [
            "انا بنت",
            "انا ولد",
            "ممكن اتكلم؟",
            "هات رقمك واتس",
            "مين صاحب الحساب؟",
            "ازيك"
        ]
        for s in samples:
            print("\n>> رسالة:", s)
            print(get_n0x_reply("local_test_user", s))
    else:
        run_n0x()