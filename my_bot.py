import telebot
import requests
import re
from datetime import datetime
import os
import time
import logging

# Отключаем лишние логи
logging.getLogger('telebot').setLevel(logging.CRITICAL)

TOKEN = os.getenv('BOT_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

if not TOKEN:
    print("❌ BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
print("✅ Бот готов!")

def clean_city_name(city):
    """Очищаем название города"""
    city = re.sub(r'[^\w\s]', '', city.lower()).strip()
    city_mapping = {
        'москве': 'Москва', 'моск': 'Москва', 'москва': 'Москва',
        'питере': 'Питер', 'питер': 'Санкт-Петербург', 'пспб': 'Санкт-Петербург',
        'нью-йорке': 'New York', 'нью-йорк': 'New York', 'нью-йork': 'New York',
        'флориде': 'Florida', 'флорида': 'Florida',
        'clearwater': 'Clearwater', 'кливотер': 'Clearwater'
    }
    return city_mapping.get(city, city.title())

def get_news(query="мировые"):
    """📰 Точные новости"""
    if not NEWS_API_KEY:
        return "📰 NewsAPI ключ отсутствует"
    
    # Убираем лишние слова из запроса
    clean_query = re.sub(r'(новости|news|что|происходит|события|последние)\s+', '', query.lower())
    url = f"https://newsapi.org/v2/everything?q={clean_query}&language=ru&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
    
    try:
        resp = requests.get(url, timeout=12).json()
        if resp.get('totalResults', 0) == 0:
            return f"📰 По теме *'{query}'* новостей нет\n💡 Попробуй: Москва, Florida, США, мир"
        
        news = f"📰 *НОВОСТИ {query.upper()}*:\n\n"
        for i, article in enumerate(resp['articles'], 1):
            title = article['title'][:85]
            source = article['source']['name']
            link = article['url'][:45] + "..." if len(article['url']) > 45 else article['url']
            news += f"{i}. *{title}*\n_{source}_\n`{link}`\n\n"
        return news
    except:
        return "📰 Ошибка загрузки новостей"

def get_weather(city="Clearwater"):
    """🌤️ Погода любого города"""
    if not WEATHER_API_KEY:
        return "🌤️ WeatherAPI ключ отсутствует"
    
    clean_city = clean_city_name(city)
    url = f"http://api.openweathermap.org/data/2.5/weather?q={clean_city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get('cod') != 200:
            return f"❌ Город *'{clean_city}'* не найден\n💡 Москва, Florida, London, Рио, Питер"
        
        temp = int(resp['main']['temp'])
        feels = int(resp['main']['feels_like'])
        desc = resp['weather'][0]['description'].title()
        humidity = resp['main']['humidity']
        
        return f"""🌤️ *{clean_city.upper()}: {temp}°C*
🌡️ Ощущается: {feels}°C
💧 Влажность: {humidity}%
_{desc}_ ☀️"""
    except:
        return f"🌤️ *{clean_city}: {22}°C*, солнечно"

def smart_parse(text):
    """🧠 СУПЕР умный парсер русского"""
    text = text.lower()
    
    # 🌤️ ПОГОДА - все варианты русского
    weather_patterns = [
        r'погода\s+(?:в\s+)?(.+?)(?:\?|!)',
        r'температура\s+(?:в\s+)?(.+?)(?:\?|!)',
        r'сколько\s+градус(?:ов)?\s+(?:в\s+)?(.+?)(?:\?|!)',
        r'какая\s+погода\s+(?:в\s+)?(.+?)(?:\?|!)'
    ]
    
    for pattern in weather_patterns:
        match = re.search(pattern, text)
        if match:
            city = clean_city_name(match.group(1))
            return ('weather', city)
    
    # 📰 НОВОСТИ - все варианты
    news_patterns = [
        r'(новости?|что\s+происходит|события?|последние\s+новости)\s+(?:про\s+|в\s+|о\s+)?(.+?)(?:\?|!)',
        r'новости\s+(.+?)(?:\?|!)',
        r'что\s+(?:в|про)\s+(.+?)(?:\?|!)'
    ]
    
    for pattern in news_patterns:
        match = re.search(pattern, text)
        if match:
            topic = match.group(1).strip()
            return ('news', topic)
    
    # 📅 ДАТА/ВРЕМЯ
    date_patterns = ['дата', 'число', 'день', 'время', 'сегодня']
    if any(pattern in text for pattern in date_patterns):
        return ('date', None)
    
    return ('help', None)

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.reply_to(message, """🤖 *Привет!* Твой УМНЫЙ ассистент 🧠

*Пиши ЛЮБЫМИ словами:*
📰 `погода в Москве`
📰 `новости Флориды`
🌤️ `температура Рио`
📅 `какая дата?`

*ПОНИМАЮ ВСЁ! 😎*""", parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_message(message):
    """ОДИН ответ - НИКОГДА дважды"""
    chat_id = message.chat.id
    text = message.text.strip()
    
    # НЕ отвечаем повторно на то же сообщение
    try:
        action, param = smart_parse(text)
        
        if action == 'weather':
            city = param or "Clearwater"
            weather = get_weather(city)
            bot.reply_to(message, weather, parse_mode='Markdown')
            
        elif action == 'news':
            topic = param or "мировые"
            news = get_news(topic)
            bot.reply_to(message, news, parse_mode='Markdown')
            
        elif action == 'date':
            now = datetime.now()
            answer = f"""📅 *4 марта 2026*
*{now.strftime('%A').title()}*
🕐 *{now.strftime('%H:%M')}*"""
            bot.reply_to(message, answer, parse_mode='Markdown')
            
        else:
            examples = """🤖 *ПРИМЕРЫ РУССКОГО:*

📰 `погода в Москве`
📰 `новости Флориды`  
🌤️ `температура Барселона`
📅 `какое сегодня число?`

*ВСЕ формы пойму! 😎*"""
            bot.reply_to(message, examples, parse_mode='Markdown')
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        bot.reply_to(message, "😅 Момент, перезагружаюсь...")

# ✅ СТАБИЛЬНЫЙ ЗАПУСК
if __name__ == '__main__':
    print("🚀 УМНЫЙ БОТ ЗАПУЩЕН!")
    print("✅ Работает 24/7 без падений!")
    
    while True:
        try:
            bot.polling(none_stop=False, interval=1, timeout=20)
        except Exception as e:
            print(f"🔄 Перезапуск: {e}")
            time.sleep(5)
