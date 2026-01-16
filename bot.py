import os
import telebot
from openai import OpenAI

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip()  # es: iptv_group_assistant_bot (senza @)

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN env var")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY env var")
if not BOT_USERNAME:
    raise RuntimeError("Missing BOT_USERNAME env var (without @)")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode=None)
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Sei un assistente per un gruppo Telegram.
Rispondi SOLO quando vieni taggato.

Stile:
- Italiano predefinito (altre lingue solo se richieste)
- Educato, neutro, professionale
- Risposte brevi (max 4-5 righe)
- Se non sai qualcosa, dillo chiaramente

Regole:
- Non fornire link, contatti o prezzi
- Non discutere pagamenti/attivazioni
- Non incoraggiare attività illegali o rischiose
- Niente polemiche: de-escalation sempre
"""

def is_mentioned(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return f"@{BOT_USERNAME.lower()}" in t

@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_message(message):
    text = message.text or ""
    if not is_mentioned(text):
        return

    # pulizia: rimuove il tag dal testo
    cleaned = text.replace(f"@{BOT_USERNAME}", "").replace(f"@{BOT_USERNAME.lower()}", "").strip()
    if not cleaned:
        bot.reply_to(message, "Dimmi pure cosa ti serve 🙂 (scrivi la domanda dopo il tag)")
        return

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": cleaned},
            ],
        )
        answer = resp.choices[0].message.content.strip()
        if not answer:
            answer = "Ok — puoi riformulare la richiesta in una frase?"
        bot.reply_to(message, answer)
    except Exception:
        bot.reply_to(message, "Ops, al momento ho un problema tecnico. Riprova tra poco.")

bot.infinity_polling(skip_pending=True)
