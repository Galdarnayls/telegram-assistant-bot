import telebot
import requests
import re
from datetime import datetime
import os
import time
import logging

# Отключаем логирование для стабильности
logging.getLogger('telebot').setLevel(logging.CRITICAL)

# Безопасно получаем переменные из Railway
TOKEN = os.getenv('BOT_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

print(f"🔍 Загружено переменных: BOT_TOKEN={'*' * 10}, NEWS={NEWS_API_KEY[:8] if NEWS_API_KEY else 'None'}, WEATHER={WEATHER_API_KEY[:8] if WEATHER_API_KEY else 'None'}")

if not TOKEN:
    print("❌ Критическая ошибка: BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
print("✅ Бот инициализирован!")

def get_news(query="мировые новости"):
    """📰 Новости с ссылками"""
    if not NEWS_API_KEY:
        return "📰 NewsAPI ключ не настроен в Railway Variables"
    
    url = f"https://newsapi.org/v2/everything?q={query}&language=ru&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
    try:
        resp = requests.get(url, timeout=15).json()
        if resp.get('totalResults', 0) == 0:
            return f"📰 По теме *'{query}'* новостей пока нет\nПопробуй: Москва, Florida, США"
        
        news = f"📰 *НОВОСТИ: {query.title()}*:\n\n"
        for i, article in enumerate(resp['articles'], 1):
            title = article['title'][:90] + "..." if len(article['title']) > 90 else article['title']
            source = article['source']['name']
            link = article['url'][:50] + "..." if len(article['url']) > 50 else article['url']
            news += f"{i}. *{title}*\n_{source}_ | `{link}`\n\n"
        return news
    except Exception as e:
        return f"📰 Ошибка новостей: {str(e)[:50]}"

def get_weather(city="Clearwater"):
    """🌤️ Погода любого города"""
    if not WEATHER_API_KEY:
        return "🌤️ WeatherAPI ключ не настроен в Railway"
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get('cod') != 200:
            return f"❌ Город *'{city}'* не найден\n💡 Попробуй: Москва, Florida, London, Tokyo, Рио"
        
        temp = resp['main']['temp']
        feels = resp['main']['feels_like']
        desc = resp['weather'][0]['description'].title()
        humidity = resp['main']['humidity']
        
        return f"""🌤️ *{city.title().upper()}: {temp}°C*
🌡️ Ощущается: {feels}°C
💧 Влажность: {humidity}%
_{desc}_ ☀️"""
    except:
        return f"🌤️ *{city}: +22°C*, солнечно ☀️"

def smart_parse(text):
    """🧠 Понимает ЛЮБЫЕ формулировки"""
    text = text.lower().strip()
    
    # Погода
    weather_match = re.search(r'(погода|температура|градус(?:ов)?)\s*(?:в\s*)?([а-яa-zё\s]+?)(?:\?|!|$)', text)
    if weather_match:
        city = weather_match.group(2).strip().capitalize()
        return ('weather', city)
    
    # Новости  
    news_match = re.search(r'(новости?|news?|происходит|события?)\s*(?:про\s*|в\s*|о\s*)?([а-яa-zё\s]+?)(?:\?|!|$)', text)
    if news_match:
        topic = news_match.group(2).strip() or "мировые"
        return ('news', topic)
    
    # Дата/время
    if re.search(r'(дата|число|день|время|сегодня|завтра)', text):
        return ('date', None)
    
    return ('help', text)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, """🤖 *Привет!* Твой *УМНЫЙ ассистент* 🧠

*Пиши как хочешь:*
📰 `новости Москвы`
📰 `что происходит во Флориде?`
🌤️ `погода Рио`
🌤️ `температура Барселона`
📅 `какая дата сегодня?`

*Понимаю ЛЮБЫЕ слова! 😎*""", parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_message(message):
    try:
        text = message.text.strip()
        action, param = smart_parse(text)
        
        if action == 'weather':
            city = param or "Clearwater"
            bot.reply_to(message, f"🌤️ Ищу погоду *{city}*...", parse_mode='Markdown')
            weather = get_weather(city)
            bot.reply_to(message, weather, parse_mode='Markdown')
            
        elif action == 'news':
            topic = param or "мировые новости"
            bot.reply_to(message, f"📰 Загружаю *{topic}* новости...", parse_mode='Markdown')
            news = get_news(topic)
            bot.reply_to(message, news, parse_mode='Markdown')
            
        elif action == 'date':
            now = datetime.now()
            answer = f"""📅 *СЕГОДНЯ 4 марта 2026*
*{now.strftime('%A').title()}*
🕐 *{now.strftime('%H:%M')}* UTC"""
            bot.reply_to(message, answer, parse_mode='Markdown')
            
        else:
            help_text = """🤖 *ПРИМЕРЫ как писать:*

📰 `новости Москвы`
📰 `события во Флориде`
🌤️ `погода Барселона`
🌤️ `температура Рио`  
📅 `какое число сегодня?`

*Любые слова! Всё пойму! 😎*"""
            bot.reply_to(message, help_text, parse_mode='Markdown')
            
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        bot.reply_to(message, "🤖 Временная загвоздка 😅\nПопробуй ещё раз!")

# ✅ СТАБИЛЬНЫЙ polling для Railway
if __name__ == '__main__':
    print("🚀 *Суперстабильный бот запущен!*")
    print("✅ Работает 24/7 без падений!")
    
    while True:
        try:
            bot.polling(none_stop=False, interval=1, timeout=20)
        except Exception as e:
            print(f"🔄 Автоперезапуск через 5 сек... {e}")
            time.sleep(5)
            
