import re
from datetime import datetime

import gradio as gr

from data import df, normalize_text


USERNAME = "admin"
PASSWORD = "1234"


def get_greeting():
    hour = datetime.now().hour

    if 5 <= hour < 10:
        return "🌅 صباح الخير"
    elif 10 <= hour < 17:
        return "☀️ نهارك سعيد"
    else:
        return "🌙 مساء الخير"


def login(username, password):
    username = (username or "").strip()
    password = password or ""

    if username == USERNAME and password == PASSWORD:
        greeting = get_greeting()

        message = f"""
# 🎉 تم تسجيل الدخول بنجاح

## {greeting}، {username} 👋

مرحباً بك في مساعد لائحة الحوافز والمكافآت - جامعة البطانة.

يمكنك الآن البحث عن الوظيفة أو استخدام حاسبة المكافآت.
"""

        return (
            gr.update(visible=False),
            gr.update(visible=True),
            message,
            "",
        )

    return (
        gr.update(visible=True),
        gr.update(visible=False),
        "",
        "❌ اسم المستخدم أو رمز الدخول غير صحيح.",
    )


def search_jobs(query):
    query = normalize_text(query)

    if not query:
        return df.iloc[0:0]

    return df[
        df["_وظيفة_بحث"].str.contains(
            query,
            regex=False,
            na=False,
        )
    ]


def format_results(results, title):
    if results.empty:
        return None

    response = f"""
### 🔍 {title}

| المسمى الوظيفي | نوع الاستحقاق / المكافأة | الفئة | ملاحظات |
|---|---|---:|---|
"""

    for _, row in results.iterrows():
        amount = str(row["الفئة_بالجنيه"]).replace("|", "\\|")
        note = str(row["ملاحظات"]).replace("|", "\\|")

        response += (
            f"| {row['وظيفة']} | "
            f"{row['نوع_المكافأة']} | "
            f"{amount} {row['العملة']} | "
            f"{note} |\n"
        )

    response += """

---

📌 المصدر: لائحة المكافآت والحوافز لجامعة البطانة (تعديل 2025م).
"""

    return response


def respond(message, history):
    if not message or not message.strip():
        return "⚠️ يرجى كتابة اسم الوظيفة أولاً."

    results = search_jobs(message)

    if not results.empty:
        return format_results(results, f"نتائج البحث عن: {message}")

    return f"""
❌ لم يتم العثور على سجلات مطابقة لـ **{message}**.

### 🔎 جرّب البحث باستخدام:
- المدير
- الوكيل
- أمين الشؤون العلمية
- عميد الكلية
- نائب عميد الكلية
- المسجل
- الحرس الجامعي
- العمال
"""


def get_reward_types():
    return sorted(df["نوع_المكافأة"].dropna().astype(str).unique().tolist())


def calculate_total(reward_type, jobs_text):
    if not reward_type:
        return "⚠️ اختر نوع المكافأة أولاً."

    if not jobs_text or not jobs_text.strip():
        return "⚠️ اكتب وظيفتين أو أكثر، أو وظيفة واحدة على الأقل."

    # يمكن كتابة الوظائف في أسطر أو فصلها بعلامة +
    jobs = re.split(r"\s*(?:\+|،|,|\n)\s*", jobs_text.strip())
    jobs = [job.strip() for job in jobs if job.strip()]

    if not jobs:
        return "⚠️ لم يتم العثور على وظائف في خانة الحاسبة."

    selected_type = normalize_text(reward_type)
    type_df = df[df["_نوع_بحث"] == selected_type]

    total = 0
    lines = []
    errors = []

    for job in jobs:
        job_norm = normalize_text(job)

        exact = type_df[type_df["_وظيفة_بحث"] == job_norm]

        if exact.empty:
            partial = type_df[
                type_df["_وظيفة_بحث"].str.contains(
                    job_norm,
                    regex=False,
                    na=False,
                )
            ]

            if len(partial) == 1:
                exact = partial

        if exact.empty:
            errors.append(job)
            continue

        if len(exact) > 1:
            errors.append(f"{job} (أكثر من نتيجة)")
            continue

        amount = exact.iloc[0]["الفئة_بالجنيه"]

        if not isinstance(amount, (int, float)):
            errors.append(f"{job} (الفئة ليست رقماً)")
            continue

        amount = float(amount)
        total += amount

        lines.append(
            f"| {exact.iloc[0]['وظيفة']} | "
            f"{amount:,.0f} جنيه |"
        )

    if not lines:
        return """
❌ لم أستطع حساب المجموع.

تأكد من اختيار نوع المكافأة الصحيح، وأن الوظائف لها فئات رقمية.
"""

    result = f"""
## 🧮 نتيجة حاسبة المكافآت

**نوع المكافأة:** {reward_type}

| الوظيفة | الفئة |
|---|---:|
"""

    result += "\n".join(lines)
    result += f"""

### 💰 المجموع الكلي: **{total:,.0f} جنيه**
"""

    if errors:
        result += "\n### ⚠️ لم يتم احتساب:\n"
        for error in errors:
            result += f"- {error}\n"

    return result


def logout():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        "",
        "",
    )
