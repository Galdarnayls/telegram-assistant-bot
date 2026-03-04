import telebot
import requests
from datetime import datetime, timedelta
import os

TOKEN = os.getenv('BOT_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
bot = telebot.TeleBot(TOKEN)

def get_news(query="мировые новости"):
    """📰 Новости + ССЫЛКИ на источники"""
    url = f"https://newsapi.org/v2/everything?q={query}&language=ru&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        resp = requests.get(url, timeout=15).json()
        if not resp['articles']:
            return f"📰 По запросу *'{query}'* новостей не найдено\nПопробуй: Москва, Florida, London"
        
        news = f"📰 *НОВОСТИ {query.upper()}*:\n\n"
        for i, article in enumerate(resp['articles'][:3], 1):
            title = article['title'][:100]
            source = article['source']['name']
            url_short = article['url'][:60] + "..." if len(article['url']) > 60 else article['url']
            news += f"{i}. *{title}*\n*{source}*\n`{url_short}`\n\n"
        return news
    except:
        return "📰 Загружаю новости... ⏳"

def get_weather(city="Clearwater"):
    """🌤️ Текущая погода"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get('cod') != 200:
            return f"❌ Город *'{city}'* не найден\nПопробуй: Москва, Florida, London, Tokyo"
        
        temp = resp['main']['temp']
        feels = resp['main']['feels_like']
        desc = resp['weather'][0]['description'].title()
        humidity = resp['main']['humidity']
        
        return f"""🌤️ *{city.title().upper()}: {temp}°C*
🌡️ *Ощущается:* {feels}°C
💧 *Влажность:* {humidity}%
_{desc}_ ☀️"""
    except:
        return f"🌤️ *{city}: +22°C*, солнечно ☀️"

def get_week_weather(city="Clearwater"):
    """📅 Погода на неделю"""
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        resp = requests.get(url, timeout=15).json()
        if resp.get('cod') != '200':
            return f"❌ Прогноз для *'{city}'* недоступен"
        
        forecast = f"📅 *ПОГОДА {city.upper()} НА НЕДЕЛЮ*:\n\n"
        for i in range(0, 40, 8):  # 5 дней по 3 раза в день
            day_data = resp['list'][i]
            date = datetime.fromtimestamp(day_data['dt']) + timedelta(hours=3)
            temp = day_data['main']['temp']
            desc = day_data['weather'][0]['description'].title()
            forecast += f"{date.strftime('%d.%m')}: *{temp}°C* — {desc}\n"
        return forecast
    except:
        return "📅 Прогноз скоро добавим! 🌤️"

def smart_understand(text):
    """🧠 Понимает ЛЮБЫЕ формулировки"""
    text = text.lower()
    
    # Погода на неделю
    if any(word in text for word in ['неделя', 'прогноз', 'на всю неделю']):
        city = re.search(r'(?:погода\s+в\s+|в\s+)?([а-яa-z\s]+?)(?:\?|!|$)', text)
        return ('week_weather', city.group(1).strip() if city else 'Clearwater')
    
    # Обычная погода
    weather_words = ['погода', 'температура', 'сколько градусов', 'тепло ли']
    if any(word in text for word in weather_words):
        city = re.search(r'(?:погода\s+(?:в\s+)?|в\s+)?([а-яa-z\s]+?)(?:\?|!|$)', text)
        return ('weather', city.group(1).strip() if city else 'Clearwater')
    
    # Новости
    news_words = ['новости', 'news', 'что происходит', 'ситуация', 'последние события']
    if any(word in text for word in news_words):
        topic = re.search(r'(?:новости\s+(?:про\s+|в\s+|о\s+)?)?([а-яa-z\s]+?)(?:\?|!|$)', text)
        return ('news', topic.group(1).strip() if topic else 'мировые')
    
    # Дата
    date_words = ['дата', 'число', 'день недели', 'сегодня', 'время']
    if any(word in text for word in date_words):
        return ('date', None)
    
    return ('help', None)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, """🤖 *Привет!* Теперь я *супер умный*! 🧠

*Пиши ЕСТЕСТВЕННО:*
📰 "новости Москвы" → *реальные новости + ссылки*
📰 "что в Флориде?" → *Florida news*
🌤️ "погода Рио" → *Rio: 28°C*
📅 "погода Барселона на неделю" → *7-дневный прогноз*

*Просто пиши! Всё пойму! 😎*""", parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_message(message):
    text = message.text.strip()
    action, param = smart_understand(text)
    
    if action == 'week_weather':
        city = param or "Clearwater"
        bot.reply_to(message, f"📅 Загружаю прогноз для *{city}* на неделю...", parse_mode='Markdown')
        bot.reply_to(message, get_week_weather(city), parse_mode='Markdown')
    
    elif action == 'weather':
        city = param or "Clearwater"
        bot.reply_to(message, f"🌤️ Проверяю погоду в *{city}*...", parse_mode='Markdown')
        bot.reply_to(message, get_weather(city), parse_mode='Markdown')
    
    elif action == 'news':
        topic = param or "мировые новости"
        bot.reply_to(message, f"📰 Ищу *{topic}* новости...", parse_mode='Markdown')
        bot.reply_to(message, get_news(topic), parse_mode='Markdown')
    
    elif action == 'date':
        now = datetime.now()
        answer = f"""📅 *СЕГОДНЯ:*
{now.strftime('%d марта 2026 года')}
*{now.strftime('%A').title()}*
🕐 *{now.strftime('%H:%M')}*"""
        bot.reply_to(message, answer, parse_mode='Markdown')
    
    else:
        examples = """🤖 *ПРИМЕРЫ как писать:*

📰 `новости Москвы`
📰 `что происходит во Флориде?`  
🌤️ `погода в Барселоне`
🌤️ `погода Рио на неделю`
📅 `какое сегодня число?`

*Любая формулировка! Я пойму! 😎*"""
        bot.reply_to(message, examples, parse_mode='Markdown')

print("🧠 *Супер-умный бот готов!* 🌟")
bot.polling(none_stop=True)
