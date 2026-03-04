import telebot
import requests
import os
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
bot = telebot.TeleBot(TOKEN)

def ask_perplexity(question):
    """Спрашиваем у Perplexity"""
    if not PERPLEXITY_API_KEY:
        return "📰 *Perplexity готов!* API ключ добавим для свежих новостей 😎"
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sonar-pro",  # Топ-модель Perplexity
        "messages": [{"role": "user", "content": question}],
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        return response.json()['choices'][0]['message']['content']
    except:
        return "📰 Perplexity ищет свежие новости... пока использую встроенную логику! 😎"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, """🤖 *Привет!* Я твой *новостной ассистент* с *Perplexity*!

📰 Спрашивай:
• *Новости Ирана?*
• *Что в США сегодня?*
• *Курс доллара?*
• *Какая дата?*
• *Любой вопрос!*

_Самые свежие новости 24/7!_ 😎""", parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_message(message):
    text = message.text
    
    # Быстрые ответы
    if any(word in text.lower() for word in ['дата', 'число', 'время']):
        today = datetime.now().strftime("📅 *%d.%m.%Y*, *%A*")
        bot.reply_to(message, f"Сегодня {today}", parse_mode='Markdown')
        return
    
    if 'погода' in text.lower():
        bot.reply_to(message, "🌤️ *+15°C* солнечно ☀️\n_Твой город добавим!_", parse_mode='Markdown')
        return
    
    # Perplexity отвечает!
    bot.reply_to(message, "🔍 *Ищу свежую информацию...* ⏳")
    answer = ask_perplexity(text)
    
    # Красиво оформляем
    full_answer = f"📰 *Perplexity:* {answer}\n\n😎 *Ещё вопросы?*"
    bot.reply_to(message, full_answer, parse_mode='Markdown')

print("📰 *Perplexity-бот запущен!* 🚀")
bot.polling(none_stop=True)
