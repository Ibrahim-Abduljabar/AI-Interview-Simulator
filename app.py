import streamlit as st
from groq import Groq

st.set_page_config(page_title="AI Interviewer", page_icon="🤖", layout="centered")
st.title("🤖 محاكي المقابلات الشخصية بالذكاء الاصطناعي")
st.write("تدرب على المقابلات المهنية؛ سأطرح عليك سؤالاً ونمضي خطوة بخطوة!")

# 1. تهيئة الذاكرة وحفظ الجلسة
if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
        {"role": "system", "content": "أنت مساعد ذكاء اصطناعي متطور وأداة تدريبية مخصصة لمحاكاة المقابلات الشخصية وتأهيل المتقدمين. عرّف المستخدم في أول رسالة بوضوح أنك روبوت وأداة تدريبية ذكية، ثم اطرح عليه سؤالاً مهنياً واحداً باللغة العربية بأسلوب محترم ومشجع، وانتظر رده لتقييمه ومساعدته على تطوير مهاراته ثم طرح السؤال التالي."}
    ]
if "messages" not in st.session_state:
    st.session_state["messages"] = []

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 2. توليد أول سؤال إذا كان الشات فارغاً
if len(st.session_state["messages"]) == 0:
    with st.spinner("جاري بدء المقابلة..."):
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state["chat_history"]
        )
        initial_question = completion.choices[0].message.content
        st.session_state["messages"].append({"role": "assistant", "content": initial_question})
        st.session_state["chat_history"].append({"role": "assistant", "content": initial_question})

# 3. عرض كل رسائل الشات المخزنة أولاً لمنع اختفائها عند الـ Rerun
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# 4. استقبال المدخلات الجديدة من المستخدم
user_answer = st.chat_input("اكتب إجابتك هنا وناقش مسؤول التوظيف...")

if user_answer:
    # حفظ وعرض إجابة المستخدم فوراً
    st.session_state["messages"].append({"role": "user", "content": user_answer})
    st.session_state["chat_history"].append({"role": "user", "content": user_answer})
    
    # إجبار الواجهة على عرض رسالة المستخدم قبل طلب الرد من الـ API
    st.rerun()

# 5. إذا كانت آخر رسالة من المستخدم، نطلب الرد من Groq
if len(st.session_state["messages"]) > 0 and st.session_state["messages"][-1]["role"] == "user":
    with st.spinner("جاري التفكير في إجابتك وطرح السؤال التالي..."):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state["chat_history"]
            )
            bot_response = completion.choices[0].message.content
            st.session_state["messages"].append({"role": "assistant", "content": bot_response})
            st.session_state["chat_history"].append({"role": "assistant", "content": bot_response})
            st.rerun()
        except Exception as e:
            st.error(f"حدث خطأ في الاتصال: {e}")
