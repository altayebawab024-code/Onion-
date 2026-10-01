# -*- coding: utf-8 -*-
"""نظام الإدارة المالية للمكافآت - جامعة البطانة (Gradio Web)."""

import base64
import os
import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd

from database import init_db, get_sections, get_reward_by_id, update_reward
from system_functions import (
    USERNAME,
    PASSWORD,
    add_reward,
    calculator,
    calculate_entitlement,
    delete_reward,
    export_csv,
    export_excel,
    format_number,
    get_dataframe,
    get_greeting,
    get_reward_types,
    get_statistics,
    global_search,
    login,
    search_jobs,
    system_info,
)

APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "logo.png"
if not LOGO_PATH.exists():
    LOGO_PATH = APP_DIR / "logo.png.jpg"


def _logo_uri():
    """تحويل الشعار إلى data-URI ليُعرض بجودة ثابتة داخل الواجهة."""
    if not LOGO_PATH.exists():
        return ""
    mime = "image/png" if LOGO_PATH.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()


def logo_img(size):
    uri = _logo_uri()
    return f'<img class="uni-logo" src="{uri}" alt="شعار جامعة البطانة" style="height:clamp(44px, 9vw, {size}px)">' if uri else ""


def header_html(title_html, size):
    """ترويسة: شعار على اليمين + عنوان في المنتصف + شعار على اليسار."""
    return (
        '<div class="brand-header" dir="rtl">'
        f'{logo_img(size)}<div class="brand-title">{title_html}</div>{logo_img(size)}'
        '</div>'
    )


CSS = """
body, .gradio-container { direction: rtl; }
.gradio-container { max-width: 1400px !important; margin: auto; }
.header-box { text-align: center; padding: 12px; border-radius: 18px; border: 1px solid #ddd; }
.brand-header { display: flex; align-items: center; justify-content: space-between; gap: clamp(6px, 2vw, 16px); }
.brand-title { flex: 1; min-width: 0; text-align: center; }
.brand-title h1 { font-size: clamp(1.05rem, 3.6vw, 2rem) !important; line-height: 1.5; }
.brand-title h2 { font-size: clamp(.95rem, 3vw, 1.5rem) !important; line-height: 1.5; }
.brand-title h3 { font-size: clamp(.85rem, 2.4vw, 1.2rem) !important; line-height: 1.5; }
.brand-title h1, .brand-title h2, .brand-title h3 { margin: 3px 0; overflow-wrap: anywhere; }
.uni-logo { width: auto; max-width: 22vw; object-fit: contain; flex: 0 0 auto; filter: drop-shadow(0 2px 4px rgba(0,0,0,.18)); }
.section-title { font-size: clamp(1.15rem, 4vw, 1.6rem) !important; font-weight: 800 !important; }
.orange-btn button { background: #ff7900 !important; color: white !important; border: none !important; }
.danger-btn button { background: #d93025 !important; color: white !important; }
.success-btn button { background: #188038 !important; color: white !important; }
.info-card { text-align: center; padding: 12px; border: 1px solid #ddd; border-radius: 14px; }

/* ===== تجاوب الشاشات (هاتف / تابلت / حاسوب) ===== */
html, body { overflow-x: hidden; }
.gradio-container { width: 100% !important; padding-left: 12px !important; padding-right: 12px !important; box-sizing: border-box; }
/* التبويبات: تمرير أفقي بدل التكسير */
.tab-wrapper, .tabs > div:first-child, div[role="tablist"] { overflow-x: auto !important; flex-wrap: nowrap !important; -webkit-overflow-scrolling: touch; scrollbar-width: thin; }
div[role="tablist"] button { white-space: nowrap; flex: 0 0 auto; }
/* الجداول: تمرير أفقي داخل الجدول */
.table-wrap, [class*="table-wrap"], .dataframe { max-width: 100%; overflow-x: auto !important; }
/* أهداف لمس مريحة */
button, input, textarea, select { min-height: 44px; }
input, textarea { font-size: 16px !important; } /* يمنع تكبير iOS التلقائي */
.gradio-container .row { flex-wrap: wrap; }

@media (max-width: 1024px) {
  .gradio-container { max-width: 100% !important; }
}
@media (max-width: 768px) {
  .gradio-container { padding-left: 8px !important; padding-right: 8px !important; }
  .header-box { padding: 8px; border-radius: 14px; }
  .gradio-container .row > * { min-width: 100% !important; flex: 1 1 100% !important; }
  .gradio-container button.lg, .gradio-container button.primary, .gradio-container button.secondary, .gradio-container button.stop { width: 100%; }
  .gradio-container h1 { font-size: 1.35rem; }
  .gradio-container h2 { font-size: 1.15rem; }
}
"""


def safe_df(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["id", "القسم", "نوع_المكافأة", "وظيفة", "الفئة_بالجنيه", "العملة", "ملاحظات"])
    return df


def do_login(username, password):
    if login(username, password):
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            f"# 🎉 تم تسجيل الدخول بنجاح\n\n## {get_greeting()}، {username} 👋\n\nمرحباً بك في **مساعد لائحة الحوافز والمكافآت - جامعة البطانة**.\n\nيمكنك الآن استخدام البحث والحاسبة وحساب الاستحقاق وإدارة البيانات والتصدير.",
            "",
        )
    return gr.update(visible=True), gr.update(visible=False), "", "❌ اسم المستخدم أو كلمة المرور غير صحيحة."


def do_logout():
    return gr.update(visible=True), gr.update(visible=False), "", ""


def search_ui(query, reward_type):
    df = search_jobs(query or "", reward_type or "")
    return safe_df(df)


def entitlement_ui(job, reward_type, quantity):
    result = calculate_entitlement(job, reward_type, quantity)
    if not result["ok"]:
        return result["message"]
    row = result["row"]
    return (
        f"### 💰 نتيجة حساب الاستحقاق\n\n"
        f"**الوظيفة:** {row['وظيفة']}\n\n"
        f"**نوع المكافأة:** {row['نوع_المكافأة']}\n\n"
        f"**القيمة للوحدة:** {format_number(result['amount'])} {row['العملة']}\n\n"
        f"**الكمية:** {result['quantity']:g}\n\n"
        f"## الإجمالي: {format_number(result['total'])} {row['العملة']}"
    )


def calculator_ui(expression):
    result = calculator(expression)
    if result["ok"]:
        return f"### النتيجة: **{format_number(result['result'])}**"
    return f"❌ {result['message']}"


def stats_ui():
    s = get_statistics()
    return pd.DataFrame([
        ["📄 إجمالي سجلات المكافآت", s["إجمالي السجلات"]],
        ["👤 عدد الوظائف/البنود", s["عدد الوظائف/البنود المختلفة"]],
        ["📑 أنواع المكافآت", s["عدد أنواع المكافآت"]],
        ["🏢 عدد الأقسام", s["عدد الأقسام"]],
    ], columns=["البيان", "العدد"])


def add_ui(section, reward_type, job, amount, currency, notes):
    try:
        record_id = add_reward(section, reward_type, job, amount, currency, notes)
        return f"✅ تمت إضافة السجل بنجاح. رقم السجل: **{record_id}**", get_dataframe(), stats_ui()
    except Exception as e:
        return f"❌ تعذر الإضافة: {e}", get_dataframe(), stats_ui()


def load_record_ui(record_id):
    try:
        rid = int(record_id)
    except (TypeError, ValueError):
        return "", "", "", "", "", "", "❌ أدخل رقم سجل صحيح."
    row = get_reward_by_id(rid)
    if not row:
        return "", "", "", "", "", "", "❌ لم يتم العثور على السجل."
    return row["القسم"], row["نوع_المكافأة"], row["وظيفة"], row["الفئة_بالجنيه"], row["العملة"], row["ملاحظات"], "✅ تم تحميل السجل."


def update_ui(record_id, section, reward_type, job, amount, currency, notes):
    try:
        rid = int(record_id)
        update_reward(rid, section, reward_type, job, amount, currency, notes)
        return "✅ تم تعديل السجل بنجاح.", get_dataframe(), stats_ui()
    except Exception as e:
        return f"❌ تعذر التعديل: {e}", get_dataframe(), stats_ui()


def delete_ui(record_id):
    try:
        rid = int(record_id)
        ok = delete_reward(rid)
        return ("✅ تم حذف السجل." if ok else "❌ لم يتم العثور على السجل."), get_dataframe(), stats_ui()
    except Exception as e:
        return f"❌ تعذر الحذف: {e}", get_dataframe(), stats_ui()


def export_csv_ui():
    path = Path(tempfile.gettempdir()) / "batana_rewards_export.csv"
    export_csv(path)
    return str(path)


def export_excel_ui():
    path = Path(tempfile.gettempdir()) / "batana_rewards_export.xlsx"
    export_excel(path)
    return str(path)


def refresh_all():
    types = get_reward_types()
    sections = get_sections()
    return safe_df(get_dataframe()), stats_ui(), gr.update(choices=types), gr.update(choices=sections), gr.update(choices=types)


# تهيئة قاعدة البيانات قبل تشغيل الواجهة
init_db()
reward_types = get_reward_types()
sections = get_sections()

with gr.Blocks(title="مساعد لائحة الحوافز والمكافآت - جامعة البطانة") as demo:
    with gr.Column(visible=True) as login_page:
        with gr.Column(elem_classes=["header-box"]):
            gr.HTML(header_html("<h1>🏛 جامعة البطانة</h1><h2>💰 نظام الإدارة المالية للمكافآت</h2><h3>🔐 تسجيل الدخول إلى النظام</h3>", 130))
        username = gr.Textbox(label="👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
        password = gr.Textbox(label="🔑 كلمة المرور", placeholder="أدخل كلمة المرور", type="password")
        login_button = gr.Button("🔐 تسجيل الدخول", variant="primary")
        login_message = gr.Markdown()

    with gr.Column(visible=False) as main_page:
        with gr.Column(elem_classes=["header-box"]):
            gr.HTML(header_html("<h1>💰 نظام الإدارة المالية للمكافآت</h1><h3>جامعة البطانة</h3>", 100))
        with gr.Row():
            greeting_box = gr.Markdown()
            logout_button = gr.Button("🚪 خروج", variant="stop", scale=0, min_width=120)

        gr.Markdown("**يمكنك البحث في اللائحة، حساب الاستحقاق، استخدام الحاسبة، إدارة السجلات، مراجعة الإحصائيات وتصدير البيانات.**")

        with gr.Tabs():
            with gr.Tab("🔎 البحث"):
                gr.Markdown("## 🔎 البحث في لائحة المكافآت", elem_classes=["section-title", "rtl"])
                with gr.Row():
                    search_box = gr.Textbox(label="اسم الوظيفة أو البند", placeholder="مثال: المدير")
                    search_type = gr.Dropdown(choices=reward_types, label="نوع المكافأة", value=None)
                search_btn = gr.Button("🔎 بحث", elem_classes=["orange-btn"])
                search_table = gr.Dataframe(value=safe_df(global_search("")), interactive=False, wrap=True)
                search_btn.click(search_ui, inputs=[search_box, search_type], outputs=search_table)
                search_box.submit(search_ui, inputs=[search_box, search_type], outputs=search_table)

            with gr.Tab("🧮 الآلة الحاسبة"):
                gr.Markdown("## 🧮 الآلة الحاسبة", elem_classes=["section-title", "rtl"])
                gr.Markdown("يمكنك إجراء العمليات الحسابية مثل: `420000 + 350000` أو `70000 × 5`.")
                calc_box = gr.Textbox(label="العملية الحسابية", placeholder="اكتب العملية هنا...")
                calc_btn = gr.Button("🧮 احسب", elem_classes=["orange-btn"])
                calc_result = gr.Markdown()
                calc_btn.click(calculator_ui, inputs=calc_box, outputs=calc_result)

            with gr.Tab("💰 حساب الاستحقاق"):
                gr.Markdown("## 💰 حساب استحقاق وظيفة", elem_classes=["section-title", "rtl"])
                gr.Markdown("اختر الوظيفة ونوع المكافأة وأدخل العدد لحساب الإجمالي.")
                ent_job = gr.Textbox(label="👤 الوظيفة", placeholder="مثال: المدير")
                ent_type = gr.Dropdown(choices=reward_types, label="📑 نوع المكافأة")
                ent_qty = gr.Number(label="🔢 العدد", value=1, minimum=0.01)
                ent_btn = gr.Button("💰 حساب الاستحقاق", elem_classes=["orange-btn"])
                ent_result = gr.Markdown()
                ent_btn.click(entitlement_ui, inputs=[ent_job, ent_type, ent_qty], outputs=ent_result)

            with gr.Tab("➕ إضافة وظيفة"):
                gr.Markdown("## ➕ إضافة وظيفة / بند جديد", elem_classes=["section-title", "rtl"])
                add_section = gr.Dropdown(choices=sections, label="🏢 القسم", allow_custom_value=True)
                add_type = gr.Dropdown(choices=reward_types, label="📑 نوع المكافأة", allow_custom_value=True)
                add_job = gr.Textbox(label="👤 الوظيفة / البند")
                add_amount = gr.Textbox(label="💵 قيمة المكافأة")
                add_currency = gr.Textbox(label="💱 العملة", value="جنيه")
                add_notes = gr.Textbox(label="📝 ملاحظات", lines=3)
                add_btn = gr.Button("➕ إضافة", elem_classes=["success-btn"])
                add_msg = gr.Markdown()
                add_btn.click(add_ui, inputs=[add_section, add_type, add_job, add_amount, add_currency, add_notes], outputs=[add_msg, search_table])

            with gr.Tab("📊 الإحصائيات"):
                gr.Markdown("## 📊 إحصائيات النظام", elem_classes=["section-title", "rtl"])
                refresh_stats = gr.Button("📊 تحديث الإحصائيات", elem_classes=["orange-btn"])
                stats_table = gr.Dataframe(value=stats_ui(), interactive=False)
                refresh_stats.click(stats_ui, outputs=stats_table)

            with gr.Tab("📋 إدارة البيانات"):
                gr.Markdown("## 📋 جميع بيانات اللائحة", elem_classes=["section-title", "rtl"])
                all_data = gr.Dataframe(value=safe_df(get_dataframe()), interactive=False, wrap=True)
                refresh_data = gr.Button("🔄 تحديث البيانات")
                refresh_data.click(lambda: get_dataframe(), outputs=all_data)
                gr.Markdown("### ✏️ تعديل سجل")
                edit_id = gr.Number(label="رقم السجل", precision=0)
                load_btn = gr.Button("📥 تحميل السجل")
                edit_section = gr.Textbox(label="القسم")
                edit_type = gr.Textbox(label="نوع المكافأة")
                edit_job = gr.Textbox(label="الوظيفة")
                edit_amount = gr.Textbox(label="القيمة")
                edit_currency = gr.Textbox(label="العملة")
                edit_notes = gr.Textbox(label="الملاحظات", lines=2)
                load_msg = gr.Markdown()
                load_btn.click(load_record_ui, inputs=edit_id, outputs=[edit_section, edit_type, edit_job, edit_amount, edit_currency, edit_notes, load_msg])
                update_btn = gr.Button("💾 حفظ التعديل", elem_classes=["success-btn"])
                update_msg = gr.Markdown()
                update_btn.click(update_ui, inputs=[edit_id, edit_section, edit_type, edit_job, edit_amount, edit_currency, edit_notes], outputs=[update_msg, all_data, stats_table])
                gr.Markdown("### 🗑️ حذف سجل")
                delete_id = gr.Number(label="رقم السجل للحذف", precision=0)
                delete_btn = gr.Button("🗑️ حذف", elem_classes=["danger-btn"])
                delete_msg = gr.Markdown()
                delete_btn.click(delete_ui, inputs=delete_id, outputs=[delete_msg, all_data, stats_table])

            with gr.Tab("📤 التصدير"):
                gr.Markdown("## تصدير البيانات", elem_classes=["section-title", "rtl"])
                gr.Markdown("يمكنك حفظ بيانات النظام في ملفات CSV أو Excel.")
                export_csv_btn = gr.Button("📄 تصدير CSV", elem_classes=["orange-btn"])
                export_csv_file = gr.File(label="ملف CSV")
                export_csv_btn.click(export_csv_ui, outputs=export_csv_file)
                export_excel_btn = gr.Button("📊 تصدير Excel", elem_classes=["orange-btn"])
                export_excel_file = gr.File(label="ملف Excel")
                export_excel_btn.click(export_excel_ui, outputs=export_excel_file)

            with gr.Tab("ℹ️ معلومات النظام"):
                gr.Markdown("## ℹ️ معلومات النظام", elem_classes=["section-title", "rtl"])
                info = system_info()
                gr.Markdown("\n".join([f"**{k}:** {v}" for k, v in info.items()]))
                gr.Markdown("### 🔐 الأمان\nاسم المستخدم الافتراضي: `admin`\n\nكلمة المرور محفوظة داخل ملف `system_functions.py` ولا تظهر في واجهة الدخول.")

        # متغيرات داخلية مستخدمة قبل تعريفها في بعض callbacks
        # stats_table موجودة في تبويب الإحصائيات، وGradio يسمح بالإشارة إليه بعد إنشائه فقط.

    login_button.click(do_login, inputs=[username, password], outputs=[login_page, main_page, greeting_box, login_message])
    logout_button.click(do_logout, outputs=[login_page, main_page, greeting_box, login_message])

if __name__ == "__main__":
    # يعمل محلياً وعلى الاستضافات المجانية (Hugging Face Spaces / Render / Railway ...)
    # المنفذ يُقرأ من المتغير PORT إن وُجد، وإلا يُستخدم 7860.
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", os.environ.get("GRADIO_SERVER_PORT", 7860))),
        inbrowser=not os.environ.get("SPACE_ID") and not os.environ.get("PORT"),
        share=False,
        css=CSS,
        theme=gr.themes.Soft(),
        head='<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">',
    )
