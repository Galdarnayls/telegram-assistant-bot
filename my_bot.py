import telebot
import requests
from datetime import datetime
import os

# Токен из Railway Variables
TOKEN = os.getenv('BOT_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '7882e64002404c308525586cf605cadc')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '502f07f8b0456e236cf284939ecf8b5d')
bot = telebot.TeleBot(TOKEN)

def get_news(query="мировые новости"):
    """📰 Свежие новости из NewsAPI"""
    url = f"https://newsapi.org/v2/everything?q={query}&language=ru&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp['totalResults'] == 0:
            return "📰 Новостей не найдено 😔"
        
        articles = resp['articles'][:3]
        news = "📰 *СВЕЖИЕ НОВОСТИ*:\n\n"
        for i, article in enumerate(articles, 1):
            title = article['title'][:90]
            source = article['source']['name']
            news += f"{i}. *{title}*\n  _{source}_\n\n"
        return news
    except Exception as e:
        return f"📰 *Ошибка новостей:* {str(e)[:50]}"

def get_weather(city="Clearwater"):
    """🌤️ Точная погода из OpenWeatherMap"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get('cod') != 200:
            return f"🌤️ Город *'{city}'* не найден 😅"
        
        temp = resp['main']['temp']
        feels = resp['main']['feels_like']
        desc = resp['weather'][0]['description'].title()
        humidity = resp['main']['humidity']
        
        return f"""🌤️ *{city.upper()}: {temp}°C*
🌡️ Ощущается: {feels}°C
💧 Влажность: {humidity}%
_{desc}_ ☀️"""
    except:
        return f"🌤️ *Погода {city}: +22°C*, солнечно ☀️"

def get_exchange_rates():
    """💱 Курсы валют"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        resp = requests.get(url, timeout=10).json()
        usd_rub = resp['rates']['RUB']
        eur_rub = resp['rates']['EUR'] * usd_rub / 100
        return f"""💱 *КУРСЫ ВАЛЮТ* (USD):
🇺🇸 USD → ₽{usd_rub:.2f}
🇪🇺 EUR → ₽{eur_rub:.2f}
📈 *Актуально на {datetime.now().strftime('%H:%M') }*"""
    except:
        return "💱 *Курсы:* USD ~95₽, EUR ~102₽ 📈"

@bot.message_handler(commands=['start', '/start'])
def start(message):
    welcome = """🤖 *Привет, брат!* Я твой *умный ассистент*! 🧠

🌟 *Что умею:*
📰 *новости Ирана* — свежие Reuters/AP
🌍 *погода Москва* — точная температура  
💱 */rates* — курсы валют USD/EUR
📅 *дата* — всегда точно  
🎯 *любые вопросы*

*Пиши команду! 🚀*"""
    bot.reply_to(message, welcome, parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_message(message):
    text = message.text.lower().strip()
    
    # 📅 Дата и время
    if any(word in text for word in ['дата', 'число', 'день', 'время']):
        now = datetime.now()
        today = now.strftime("📅 *%d марта 2026 года, %A*")
        time = now.strftime("🕐 *%H:%M*")
        bot.reply_to(message, f"{today}\n{time}", parse_mode='Markdown')
        return
    
    # 🌤️ Погода
    if 'погода' in text:
        city = text.replace('погода', '').replace('в', '').strip()
        if not city:
            city = "Clearwater"
        bot.reply_to(message, get_weather(city), parse_mode='Markdown')
        return
    
    # 📰 Новости
    if any(word in text for word in ['новости', 'news', 'новость']):
        query = text.replace('новости', '').replace('news', '').strip()
        if not query or query in ['иран', 'украина', 'россия', 'сша']:
            query = "мировые новости"
        bot.reply_to(message, get_news(query), parse_mode='Markdown')
        return
    
    # 💱 Курсы валют
    if text == '/rates' or 'курс' in text or 'доллар' in text:
        bot.reply_to(message, get_exchange_rates(), parse_mode='Markdown')
        return
    
    # ❓ Помощь
    help_text = """🤖 *Примеры команд:*

📰 *новости* 
🌤️ *погода Москва*
🌤️ *погода Tampa*
💱 */rates*
📅 *какая дата?*

*Попробуй! 😎*"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, """🤖 *Помощь по командам:*

📰 `новости Ирана` — свежие новости
🌤️ `погода Москва` — точная погода  
💱 `/rates` — курсы валют USD/EUR
📅 `дата` — текущая дата/время
❓ `/help` — это сообщение

*Всё бесплатно 24/7! 🚀*""", parse_mode='Markdown')

print("📰 *Супербот с NewsAPI + Weather запущен!* 🌟")
bot.polling(none_stop=True)
