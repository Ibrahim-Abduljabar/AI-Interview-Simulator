import streamlit as st
from groq import Groq

st.set_page_config(page_title="AI Interviewer", page_icon="🤖", layout="centered")
st.title("🤖 محاكي المقابلات الشخصية بالذكاء الاصطناعي")
st.write("تدرب على المقابلات المهنية؛ سأطرح عليك سؤالاً ونمضي خطوة بخطوة!")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "system", "content": "أنت مسؤول توظيف خبير وقاسي ومحترف. اطرح سؤالاً واحداً فقط في المقابلة الشخصية باللغة العربية وانتظر رد المستخدم لتقييمه ثم طرح السؤال التالي بناءً على إجابته. ابدأ بترحيب وسؤال أول فوراً بشكل مباشر وبدون مقدمات طويلة."}
    ]
if "groq_messages" not in st.session_state:
    st.session_state["groq_messages"] = []

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if len(st.session_state["groq_messages"]) == 0:
    completion = client.chat.completions.create(
        model="llama-3.3-7b-instant",
        messages=st.session_state["chat_history"]
    )
    initial_question = completion.choices[0].message.content
    st.session_state["groq_messages"].append({"role": "assistant", "content": initial_question})

for msg in st.session_state["groq_messages"]:
    if msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
    elif msg["role"] == "user":
        st.chat_message("user").write(msg["content"])

user_answer = st.chat_input("اكتب إجابتك هنا وناقش مسؤول التوظيف...")

if user_answer:
    st.chat_message("user").write(user_answer)
    st.session_state["groq_messages"].append({"role": "user", "content": user_answer})
    st.session_state["chat_history"].append({"role": "user", "content": user_answer})
    
    with st.spinner("جاري التفكير في إجابتك..."):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-7b-instant",
                messages=st.session_state["chat_history"]
            )
            bot_response = completion.choices[0].message.content
            st.session_state["groq_messages"].append({"role": "assistant", "content": bot_response})
            st.session_state["chat_history"].append({"role": "assistant", "content": bot_response})
        except Exception as e:
            st.error(f"حدث خطأ في الاتصال: {e}")
