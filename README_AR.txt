بوت تيليجرام لإنشاء صفحة HTML بمساعدة Gemini ورفعها إلى مستودع GitHub.

تنبيه مهم:
- هذه نسخة بداية وليست خدمة نشر كاملة جاهزة دون إعداد.
- لا ترسل BOT_TOKEN أو GEMINI_API_KEY أو GITHUB_TOKEN لأي شخص.
- أنشئ مفاتيح الخدمات بنفسك وأضفها في Environment Variables لدى منصة الاستضافة.
- يجب إعداد GitHub Pages/Workflow منفصل حتى تصبح الصفحات المنشأة متاحة بروابط عامة.
- الخطة المجانية قد تتوقف مؤقتًا أو تفرض حدود استخدام.

الملفات:
- bot.py: كود البوت
- requirements.txt: المكتبات اللازمة

المتغيرات المطلوبة:
BOT_TOKEN
GEMINI_API_KEY
GITHUB_TOKEN
GITHUB_OWNER
GITHUB_REPO
ADMIN_ID
RENDER_EXTERNAL_URL
PORT (اختياري، الافتراضي 10000)
GEMINI_MODEL (اختياري، الافتراضي gemini-2.5-flash)

لا تشارك أي مفاتيح سرية في المحادثة.
