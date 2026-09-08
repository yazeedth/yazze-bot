"""
بوت تليجرام مساعد شخصي - مربوط بـ Google Gemini (مجاني)
=========================================================

قبل التشغيل، لازم تركب المكتبات التالية:
pip install python-telegram-bot google-generativeai --break-system-packages

وتحط المفاتيح في متغيرات البيئة (Environment Variables):
TELEGRAM_BOT_TOKEN  -> توكن البوت من BotFather
GEMINI_API_KEY      -> مفتاح Gemini من Google AI Studio
"""

import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------- الإعدادات ----------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError(
        "لازم تحط TELEGRAM_BOT_TOKEN و GEMINI_API_KEY كمتغيرات بيئة قبل التشغيل!"
    )

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # نموذج سريع ومجاني

# إعداد تسجيل الأحداث (اختياري، يساعدك تشوف الأخطاء)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# نحتفظ بذاكرة محادثة بسيطة لكل مستخدم (تختفي إذا البوت أعاد التشغيل)
user_sessions = {}


# ---------- أوامر البوت ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = model.start_chat(history=[])
    await update.message.reply_text(
        "أهلاً فيك! 👋\n"
        "أنا مساعدك الشخصي، اسألني عن أي شي - ألعاب، برمجة، أو أي معلومة تبغاها.\n\n"
        "أوامر مفيدة:\n"
        "/start - يبدأ محادثة جديدة (ينسى القديمة)\n"
        "/help - يعرض هذي الرسالة"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "بس اكتب سؤالك عادي وأنا بجاوبك.\n"
        "لو تبغى تبدأ محادثة جديدة استخدم /start"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # لو ما عنده جلسة محادثة، سوي له وحدة جديدة
    if user_id not in user_sessions:
        user_sessions[user_id] = model.start_chat(history=[])

    chat = user_sessions[user_id]

    # نرسل "يكتب..." عشان يبين للمستخدم إن البوت شغال
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = chat.send_message(user_text)
        reply_text = response.text
    except Exception as e:
        logging.error(f"خطأ من Gemini: {e}")
        reply_text = "عذراً، صار خطأ بسيط، جرب مرة ثانية بعد شوي 🙏"

    # تليجرام يقبل رسائل حتى 4096 حرف، إذا الرد أطول نقسمه
    for i in range(0, len(reply_text), 4000):
        await update.message.reply_text(reply_text[i:i + 4000])


# ---------- تشغيل البوت ----------
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ البوت شغال الحين... اضغط Ctrl+C عشان توقفه")
    app.run_polling()


if __name__ == "__main__":
    main()
