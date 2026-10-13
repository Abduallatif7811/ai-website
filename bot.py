import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_OWNER = os.environ["GITHUB_OWNER"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
PORT = int(os.environ.get("PORT", "10000"))

def make_site(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    instructions = (
        "Create a complete, attractive, responsive single-page website in one self-contained HTML file. "
        "Return ONLY raw HTML, beginning with <!DOCTYPE html>. Include CSS and JavaScript inside the file. "
        "Use accessible semantic HTML, mobile-friendly layout, and no external build tools. "
        "If the request is in Arabic, make the page RTL and use Arabic. User request: " + prompt
    )
    response = requests.post(
        url,
        params={"key": GEMINI_API_KEY},
        json={"contents": [{"parts": [{"text": instructions}]}],
              "generationConfig": {"temperature": 0.6}},
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    html = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if html.startswith("```"):
        html = html.split("\n", 1)[-1]
        if html.endswith("```"):
            html = html[:-3].strip()
    if "<html" not in html.lower() or "<body" not in html.lower():
        raise ValueError("لم يُرجع الذكاء الاصطناعي صفحة HTML كاملة.")
    return html

def publish_site(html: str, site_slug: str) -> str:
    # Publish each generated site as a folder in the repository.
    # A GitHub Pages workflow in this package copies generated folders into
    # a deployable public directory and publishes that directory.
    path = f"generated/{site_slug}/index.html"
    api = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    existing = requests.get(api, headers=headers, timeout=30)
    payload = {
        "message": f"Add AI-generated website {site_slug}",
        "content": __import__("base64").b64encode(html.encode("utf-8")).decode("ascii"),
    }
    if existing.status_code == 200:
        payload["sha"] = existing.json()["sha"]
    elif existing.status_code not in (404,):
        existing.raise_for_status()
    result = requests.put(api, headers=headers, json=payload, timeout=60)
    result.raise_for_status()
    return f"{RENDER_EXTERNAL_URL}/preview/{site_slug}" if RENDER_EXTERNAL_URL else ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا! أرسل وصف الموقع الذي تريد إنشاءه، مثل:\n"
        "صمّم موقعًا عربيًا لمتجر عطور مع قائمة منتجات وزر تواصل.\n\n"
        "ملاحظة: يلزم إعداد مفاتيح الخدمات أولًا، والنشر العام يحتاج إعداد GitHub Pages."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أرسل وصفًا واضحًا للموقع المطلوب. مثال: موقع تعريفي لمكتب هندسي، عربي RTL، "
        "مع أقسام الخدمات والأعمال السابقة والتواصل."
    )

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("هذا البوت مخصص لصاحبه حاليًا.")
        return
    status = await update.message.reply_text("جارٍ إنشاء الموقع، قد يستغرق ذلك دقيقة أو أكثر...")
    try:
        html = make_site(update.message.text)
        slug = f"site-{update.message.message_id}"
        publish_site(html, slug)
        await status.edit_text(
            "تم إنشاء ملف الموقع ورفعه إلى مستودع GitHub.\n"
            f"اسم المجلد: generated/{slug}/\n\n"
            "مهم: الرابط العام لا يصبح جاهزًا إلا بعد إعداد النشر في GitHub Pages."
        )
    except Exception:
        logging.exception("Website generation failed")
        await status.edit_text(
            "تعذّر إنشاء الموقع. راجع إعدادات الخدمات ومفاتيح البيئة في الاستضافة، "
            "ثم جرّب مرة أخرى. لا ترسل مفاتيحك السرية هنا."
        )

async def health(request):
    from telegram import __version__  # noqa
    from telegram.ext import Application
    from aiohttp import web
    return web.Response(text="Bot is running")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))
    if RENDER_EXTERNAL_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}",
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
