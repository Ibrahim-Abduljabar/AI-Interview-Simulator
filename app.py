import streamlit as st
import os
import pdfplumber
import re
from groq import Groq
from logsnag import LogSnag

log_client = LogSnag(token=st.secrets["LOGSNAG_TOKEN"], project="ai-interview-simulator")
log_client.track(channel="visits", event="New Visit")

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error("خطأ: لم يتم ضبط مفتاح API_www في الـ Secrets حقت Streamlit")
    st.stop()

MODEL_NAME = "openai/gpt-oss-120b"

if "sessions" not in st.session_state:
    st.session_state.sessions = {"المحادثة 1": {"chat_history": [], "current_question_count": 0, "completed": False}}
if "current_session" not in st.session_state:
    st.session_state.current_session = "المحادثة 1"

with st.sidebar:
    st.title("👨‍💼 إدارة المقابلات")
    all_sessions = list(st.session_state.sessions.keys())
    selected_session = st.selectbox("اختر الجلسة الحالية:", all_sessions, index=all_sessions.index(st.session_state.current_session))
    st.session_state.current_session = selected_session
    
    if st.button("➕ مقابلة جديدة"):
        new_id = f"المحادثة {len(st.session_state.sessions) + 1}"
        st.session_state.sessions[new_id] = {"chat_history": [], "current_question_count": 0, "completed": False}
        st.session_state.current_session = new_id
        st.rerun()

session_data = st.session_state.sessions[st.session_state.current_session]
chat_history = session_data["chat_history"]



st.subheader("📄 يجب رفع السيرة الذاتية للبدء")

uploaded_cv = st.file_uploader("ارفع ملف CV بصيغة PDF أو TXT", type=["pdf", "txt"])
cv_text = ""

if uploaded_cv:
    if uploaded_cv.type == "application/pdf":
        try:
            with pdfplumber.open(uploaded_cv) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        cv_text += text + "\n"
        except Exception:
            st.warning("⚠️ لم نتمكن من قراءة ملف PDF، جرّب ملف TXT")
    else:
        try:
            cv_text = uploaded_cv.read().decode("utf-8")
        except Exception:
            st.warning("⚠️ لم نتمكن من قراءة ملف TXT")

cv_text = re.sub(r'[^\u0600-\u06FF0-9A-Za-z\s.,-]', '', cv_text)


if not cv_text:
    st.warning("⚠️ يجب رفع السيرة الذاتية أولًا قبل بدء المقابلة.")
    st.stop()



SYSTEM_PROMPT = f"""
أنت مسؤول توظيف محترف وخبير في الموارد البشرية والـ HR.
مهمتك هي إجراء مقابلة عمل حقيقية وصارمة وصعبة مع المستخدم.

هذه السيرة الذاتية الخاصة به:
--------------------
{cv_text}
--------------------

استخدمها لتخصيص الأسئلة بدقة عالية.
اطرح سؤالاً واحداً فقط في كل مرة وانتظر إجابة المستخدم قبل الانتقال للسؤال التالي.
لا تخرج عن إطار وظيفة المستخدم المتقدم إليها، واختبر مهاراته التقنية والشخصية بذكاء عميق.
"""



if not chat_history:
    chat_history.append({"role": "system", "content": SYSTEM_PROMPT})
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=chat_history
        )
        initial_bot_q = completion.choices[0].message.content
        chat_history.append({"role": "assistant", "content": initial_bot_q})
        session_data["current_question_count"] = 1
    except Exception as e:
        st.error(f"خطأ في الاتصال بالسيرفر: {e}")

st.title("🚀 محاكي المقابلات بالذكاء الاصطناعي")
st.subheader(f"الحالة: الجلسة النشطة [{st.session_state.current_session}]")

for msg in chat_history:
    if msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])
    elif msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])

if session_data["current_question_count"] >= 10 and not session_data["completed"]:
    st.info("🔄 انتهت الأسئلة الـ 10، جاري إعداد التقييم النهائي لأدائك...")
    
    evaluation_prompt = {"role": "user", "content": "انتهت المقابلة الآن. قم بتحليل كافة الإجابات السابقة للمستخدم بدقة هندسية، وأعطه تقييماً نهائياً يشمل: نقاط القوة، نقاط الضعف، ونسبة القبول المتوقعة في الوظيفة كـ نتيجه إجمالية."}
    eval_history = chat_history + [evaluation_prompt]
    
    with st.spinner("جاري مراجعة إجاباتك وإصدار النتيجة..."):
        try:
            eval_completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=eval_history
            )
            evaluation_result = eval_completion.choices[0].message.content
            
            chat_history.append({"role": "assistant", "content": f"📊 **التقييم النهائي الشامل للمقابلة:**\n\n{evaluation_result}"})
            session_data["completed"] = True
            st.rerun()
        except Exception as e:
            st.error(f"فشل في استخراج التقييم: {e}")

if not session_data["completed"]:
    user_input = st.chat_input("اكتب إجابتك هنا ووجهها للمحاكي...")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        chat_history.append({"role": "user", "content": user_input})
        
        with st.spinner("جاري تحليل إجابتك وتجهيز السؤال التالي..."):
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=chat_history
                )
                bot_response = completion.choices[0].message.content
                chat_history.append({"role": "assistant", "content": bot_response})
                session_data["current_question_count"] += 1
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الطلب: {e}")
else:
    st.success("🎉 اكتملت المقابلة وتم إصدار التقييم بنجاح. يمكنك بدء مقابلة جديدة من القائمة الجانبية.")
