import streamlit as st
from google import generativeai as genai
from typing import List, Dict, Optional
import os
import time
from dotenv import load_dotenv
from system_prompts import SYSTEM_PROMPT_EN, SYSTEM_PROMPT_MN

# Set Streamlit page config FIRST
st.set_page_config(page_title="AUM Chatbot", page_icon="🎓")

# Load environment variables from .env file
load_dotenv()

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDgCFK3pqAsPLaq2EcqWM-SlVLm5fY5a-g")

# Language toggle in sidebar
if "language" not in st.session_state:
    st.session_state.language = "English"

st.sidebar.title("🌐 Language")
st.session_state.language = st.sidebar.radio("Choose your language / Хэлээ сонгоно уу:", ["English", "Mongolian"], index=0 if st.session_state.language == "English" else 1)

# Suggested questions
SUGGESTED_QUESTIONS = {
    "English": [
        "What programs does AUM offer?",
        "When is the next entrance exam?",
        "What scholarships are available?",
        "How can I transfer to study in the USA?",
        "What student activities are available?"
    ],
    "Mongolian": [
        "AUM ямар хөтөлбөрүүд санал болгодог вэ?",
        "Дараагийн элсэлтийн шалгалт хэзээ вэ?",
        "Ямар тэтгэлэгүүд байдаг вэ?",
        "АНУ-д шилжин суралцахын тулд би юу хийх ёстой вэ?",
        "Ямар оюутны үйл ажиллагаа байдаг вэ?"
    ]
}

try:
    st.image("aum_logo.png", width=150)
except FileNotFoundError:
    st.warning("Logo image not found.")


# Detect language
def detect_language(text: str) -> str:
    mongolian_chars = set('өүңөүйцукенгшщзхъфывапролджэячсмитьбюӨҮҢЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ')
    return "Mongolian" if sum(1 for c in text if c in mongolian_chars) > len(text) * 0.15 else "English"

# Get system prompt
def get_system_prompt(text: str) -> str:
    return SYSTEM_PROMPT_MN if detect_language(text) == "Mongolian" else SYSTEM_PROMPT_EN

# Initialize Gemini
def initialize_gemini_client(api_key: str) -> Optional[genai.GenerativeModel]:
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-pro")
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return None

# Response cache
CHAT_HISTORY_CACHE = {}

def get_response_from_cache(prompt: str, lang: str) -> Optional[str]:
    return CHAT_HISTORY_CACHE.get(f"{lang}:{prompt.lower().strip()}")

def save_response_to_cache(prompt: str, response: str, lang: str):
    CHAT_HISTORY_CACHE[f"{lang}:{prompt.lower().strip()}"] = response

# Get Gemini response
GENERAL_INFO_EN = """
**🎓 Welcome to the American University of Mongolia (AUM)!**

Here’s what you need to know:

- 📘 AUM offers 100% English-language programs in Mongolia
- 🇺🇸 You can transfer to the USA through our 2+2 program
- 🎯 Entrance Exam 2025: April 26, 11:00 AM (register by April 25)
- 🎓 Scholarships up to 100% for top scorers
- 🌍 No TOEFL, IELTS, or SAT required for international students
- 🏀 Student life includes clubs, sports, events, and trips
- 💼 Internship and career support while you study

For more, visit **[www.aum.edu.mn](http://www.aum.edu.mn)** or ask me specific questions!
"""

GENERAL_INFO_MN = """
**🎓 Америкийн Их Сургууль (AUM)-д тавтай морил!**

Үндсэн мэдээлэл:

- 📘 AUM нь 100% англи хэлээр сургалт явуулдаг
- 🇺🇸 2+2 хөтөлбөрөөр АНУ-д шилжин суралцах боломжтой
- 🎯 Элсэлтийн шалгалт: 4-р сарын 26-нд 11:00 (бүртгэл 4-р сарын 25 хүртэл)
- 🎓 Шалгалтын тэтгэлэг: 100% хүртэл
- 🌍 Гадаад оюутнуудад TOEFL, IELTS, SAT шаардлагагүй
- 🏀 Клуб, спорт, үйл ажиллагаа, аяллуудтай оюутны амьдрал
- 💼 Суралцах хугацаандаа дадлага, карьерт дэмжлэг

Нэмэлт мэдээлэл авах бол **[www.aum.edu.mn](http://www.aum.edu.mn)** руу орж эсвэл надаас асуугаарай!
"""

def is_general_info_request(text: str) -> bool:
    keywords = [
        "medeelel", "medeelel avii", "medeelel avyaa", "medeelel ogooch",
        "мэдээлэл", "мэдээлэл авъя", "мэдээлэл авий", "мэдээлэл өгөөч"
    ]
    text = text.lower().strip()
    return any(k in text for k in keywords)

def get_gemini_response(model: genai.GenerativeModel, messages: List[Dict[str, str]], prompt: str) -> str:
    lang = detect_language(prompt)

    # 🔁 Handle general info shortcut
if is_general_info_request(prompt):
     return GENERAL_INFO_MN if lang == "Mongolian" else GENERAL_INFO_EN


    # ✅ Use cache if available
    cached = get_response_from_cache(prompt, lang)
    if cached:
        return cached

    # 🧠 Construct prompt with history
    history = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages)
    full_prompt = f"{get_system_prompt(prompt)}\n\n{history}\n\nUser: {prompt}"

    try:
        response = model.generate_content(full_prompt)
        result = response.text
        save_response_to_cache(prompt, result, lang)
        return result
    except Exception as e:
        st.error(f"Error: {e}")
        return "Уучлаарай, алдаа гарлаа." if lang == "Mongolian" else "Sorry, something went wrong."


# Display suggested questions
def display_suggested_questions(lang: str) -> Optional[str]:
    clicked = None
    with st.expander("💬 Suggested Questions", expanded=True):
        cols = st.columns(2)
        for i, col in enumerate(cols):
            for q in SUGGESTED_QUESTIONS[lang][i::2]:
                if col.button(q):
                    clicked = q
    return clicked

# Main app
def main():
    st.title("🎓 American University of Mongolia Virtual Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        welcome = "**👋 Welcome! Ask me anything about AUM.**" if st.session_state.language == "English" else "**👋 Сайн байна уу! AUM-ийн талаар хүссэн зүйлээ асуугаарай.**"
        st.session_state.messages.append({"role": "assistant", "content": welcome})

    model = initialize_gemini_client(GEMINI_API_KEY)
    if not model:
        st.stop()

    lang = st.session_state.language

    clicked_question = display_suggested_questions(lang)
    if clicked_question:
        st.session_state.messages.append({"role": "user", "content": clicked_question})
        with st.chat_message("user"):
            st.markdown(clicked_question)
        with st.chat_message("assistant"):
            response = get_gemini_response(model, st.session_state.messages[:-1], clicked_question)
            placeholder = st.empty()
            display_text = ""
            for char in response:
                display_text += char
                placeholder.markdown(display_text)
                time.sleep(0.03)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("What would you like to know?" if lang == "English" else "Та юу мэдэхийг хүсч байна?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            response = get_gemini_response(model, st.session_state.messages[:-1], prompt)
            placeholder = st.empty()
            display_text = ""
            for char in response:
                display_text += char
                placeholder.markdown(display_text)
                time.sleep(0.03)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
