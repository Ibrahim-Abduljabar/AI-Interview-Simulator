import streamlit as st
from groq import Groq
import time

# 1. إعدادات الصفحة وجعل التخطيط عريض ليناسب واجهة الشات والسايدبار
st.set_page_config(
    page_title="AI Interview Simulator",
    page_icon="🤖",
    layout="wide"
)

# 2. اتصال الـ API بمكتبة Groq
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# 3. تهيئة هيكلة المحادثات المتعددة في الـ Session State
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}  # حفظ المحادثات بصيغة {اسم_المحادثة: قائمة_الرسائل}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# --- الـ Sidebar الجانبي للتنقل وإنشاء المحادثات الجديدة ---
with st.sidebar:
    st.write("### 📂 إدارة المقابلات")
    
    # زر إنشاء مقابلة جديدة
    if st.button("➕ ابدأ مقابلة جديدة", use_container_width=True):
        chat_id = f"مقابلة {len(st.session_state.all_chats) + 1} - {time.strftime('%H:%M')}"
        st.session_state.all_chats[chat_id] = [
            {"role": "system", "content": "أنت خبير توظيف ومسؤول HR محترف. مهمتك هي إجراء مقابلة شخصية صارمة وقوية مع المستخدم لمعرفة كفاءته للوظيفة التي يختارها. قم بطرح سؤال واحد فقط في كل مرة، وانتظر إجابة المستخدم، وتفاعل معها ثم اطرح السؤال التالي بكل ذكاء واحترافية وبشكل عسكري حازم باللغة العربية."}
        ]
        st.session_state.current_chat = chat_id
        st.rerun()

    st.divider()
    st.write("#### 📜 تاريخ المقابلات السابقة:")
    
    # قائمة التنقل بين المقابلات
    if st.session_state.all_chats:
        for chat_name in list(st.session_state.all_chats.keys()):
            if st.button(chat_name, use_container_width=True, key=f"nav_{chat_name}"):
                st.session_state.current_chat = chat_name
                st.rerun()
    else:
        st.caption("لا توجد مقابلات نشطة حالياً. اضغط على الزر بالأعلى للبدء!")

# --- الواجهة الرئيسية للمحادثة المستهدفة ---
if st.session_state.current_chat:
    current_chat_name = st.session_state.current_chat
    messages = st.session_state.all_chats[current_chat_name]
    
    # حساب عدد الرسائل (باستثناء رسالة الـ system)
    # كل سؤال وجواب يعتبر رسالتين، فنقسم على 2 أو نحسب الـ user والـ assistant فقط
    user_assistant_msgs = [m for m in messages if m["role"] in ["user", "assistant"]]
    msg_count = len(user_assistant_msgs)
    
    # ترويسة المقابلة مع العداد الصارم
    st.write(f"### 🤖 محاكي المقابلات الشخصية بالذكاء الاصطناعي")
    st.info(f"📋 أنت الآن في: **{current_chat_name}** | ⏱️ العداد الصارم للرسائل: **{msg_count} / 15**")
    st.divider()
    
    # تفعيل السؤال الأول التلقائي إذا كانت المحادثة تحتوي على الـ system فقط
    if len(messages) == 1:
        with st.spinner("⏳ جاري بدء المقابلة وتجهيز السؤال الأول..."):
            try:
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages
                )
                initial_question = completion.choices[0].message.content
                messages.append({"role": "assistant", "content": initial_question})
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ في استدعاء السؤال الأول: {e}")

    # عرض صندوق الشات وعرض الرسائل السابقة بشكل انسيابي محترف
    for msg in messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(msg["content"])

    # --- منطق التحكم بالحد الأقصى 15 رسالة وإصدار التقييم النهائي ---
    if msg_count >= 15:
        st.warning("🚨 انتهى الوقت المخصص للمقابلة! تم الوصول للحد الأقصى (15 رسالة).")
        
        # التحقق مما إذا كان التقييم تم إصداره مسبقاً لمنع التكرار عند إعادة التشغيل
        if messages[-1].get("is_report") is not True:
            with st.spinner("📊 جاري تحليل أداءك وإصدار تقرير التقييم النهائي الشامل..."):
                try:
                    evaluation_prompt = """
                    انتهت المقابلة الشخصية. بصفتك خبير الـ HR، قم بتحليل المحادثة السابقة بالكامل واكتب تقريراً نهائياً شاملاً للمستخدم باللغة العربية يحتوي على:
                    1. تقييم عام لأداء المرشح ونقاط القوة التي أظهرها في إجاباته.
                    2. نقاط الضعف أو الأخطاء التي وقع فيها وكيف يصححها.
                    3. تقييم نهائي من 10 لمدى جاهزيته للوظيفة.
                    4. القرار النهائي (مقبول / مرفوض مع التوجيه).
                    """
                    # إرسال تاريخ الشات كاملاً مع موجه التقييم
                    eval_messages = messages + [{"role": "system", "content": evaluation_prompt}]
                    
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=eval_messages
                    )
                    report_content = completion.choices[0].message.content
                    
                    # حفظ التقرير في الذاكرة لتثبيته بالشاشة وعرضه
                    messages.append({"role": "assistant", "content": report_content, "is_report": True})
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ أثناء إصدار التقرير: {e}")
    else:
        # شريط إدخال نص المستخدم (متاح فقط إذا كان العداد تحت الـ 15)
        user_answer = st.chat_input("اكتب إجابتك هنا وناقش مسؤول التوظيف...")
        
        if user_answer:
            # إضافة إجابة المستخدم للـ Session State
            messages.append({"role": "user", "content": user_answer})
            
            # استدعاء رد مسؤول التوظيف الجديد من Groq
            with st.spinner("🤔 جاري تحليل إجابتك وصياغة السؤال التالي..."):
                try:
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages
                    )
                    bot_response = completion.choices[0].message.content
                    messages.append({"role": "assistant", "content": bot_response})
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ في السيرفر: {e}")
else:
    # شاشة ترحيبية عند فتح البرنامج لأول مرة
    st.write("### 👋 مرحباً بك في محاكي المقابلات المطور!")
    st.info("قم بإنشاء مقابلة جديدة من القائمة الجانبية (Sidebar) في اليسار لتبدأ طحن الأسئلة واختبار قدراتك فوراً!")
