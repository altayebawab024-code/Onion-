---
title: نظام مكافآت جامعة البطانة
emoji: 🏛
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
---

# نظام الإدارة المالية للمكافآت - جامعة البطانة

واجهة متجاوبة تعمل على الهاتف والتابلت والحاسوب.

## التشغيل محلياً
```
pip install -r requirements.txt
python app.py
```

## الرفع على استضافة مجانية

### Hugging Face Spaces (الأسهل)
1. أنشئ Space جديداً واختر SDK = Gradio.
2. ارفع كل ملفات هذا المجلد (app.py، requirements.txt، rewards.db، logo.png، ...).
3. سيعمل التطبيق تلقائياً على رابط عام.

### Render.com
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`
- المنفذ يُقرأ تلقائياً من المتغير `PORT`.

## تنبيه مهم
الاستضافات المجانية قد تمسح الملفات المكتوبة عند إعادة التشغيل، لذلك التعديلات
(إضافة/تعديل/حذف) على `rewards.db` قد لا تبقى. استخدم زر «تصدير» للاحتفاظ بنسخة،
وغيّر كلمة مرور المدير في `system_functions.py` قبل النشر.
