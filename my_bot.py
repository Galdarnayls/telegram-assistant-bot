import telebot
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 Привет! Я твой ассистент!\n\nСпрашивай:\n• Какая дата?\n• Погода?\n• Новости?\n• Что угодно 😎")

@bot.message_handler(content_types=['text'])
def handle_message(message):
    text = message.text.lower()
    
    # Дата и время
    if any(word in text for word in ['дата', 'число', 'время', 'день']):
        today = datetime.now().strftime("📅 %d.%m.%Y, %A")
        bot.reply_to(message, f"Сегодня {today}")
        return
    
    # День недели
    if 'день недели' in text:
        day = datetime.now().strftime("%A")
        bot.reply_to(message, f"Сегодня {day} 🎉")
        return
    
    # Простые ответы
    responses = {
        'привет': '👋 Привет! Чем помочь?',
        'погода': '🌤️ На улице +15°C, солнечно ☀️',
        'спасибо': 'Пожалуйста! 😊',
        'новости': '📰 Последние новости:\n• Иран: переговоры\n• США: выборы'
    }
    
    for key, value in responses.items():
        if key in text:
            bot.reply_to(message, value)
            return
    
    # Универсальный ответ
    bot.reply_to(message, "🤖 Отвечаю на твой вопрос!\n\nСегодня 4 марта 2026, среда 📅\nСпрашивай что угодно! 😎")

print("🤖 Бот запущен!")
bot.polling(none_stop=True)
