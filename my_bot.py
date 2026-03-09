 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/my_bot.py b/my_bot.py
index 08c1479203fe1e91e3834b7c2ee8c81099b66acb..6cd4f0029db01be2f1b3b6daee1a76990c99fe50 100644
--- a/my_bot.py
+++ b/my_bot.py
@@ -1,186 +1,171 @@
-import telebot
-import requests
-import re
-from datetime import datetime
+import logging
 import os
+import re
 import time
-import logging
+from typing import Any, List, Optional, Tuple
+from urllib.parse import quote_plus
 
-# Отключаем лишние логи
-logging.getLogger('telebot').setLevel(logging.CRITICAL)
+import requests
+import telebot
+
+logging.getLogger("telebot").setLevel(logging.CRITICAL)
 
-TOKEN = os.getenv('BOT_TOKEN')
-NEWS_API_KEY = os.getenv('NEWS_API_KEY')
-WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
+TOKEN = os.getenv("BOT_TOKEN")
 
 if not TOKEN:
     print("❌ BOT_TOKEN не найден!")
-    exit(1)
+    raise SystemExit(1)
 
 bot = telebot.TeleBot(TOKEN)
 print("✅ Бот готов!")
 
-def clean_city_name(city):
-    """Очищаем название города"""
-    city = re.sub(r'[^\w\s]', '', city.lower()).strip()
-    city_mapping = {
-        'москве': 'Москва', 'моск': 'Москва', 'москва': 'Москва',
-        'питере': 'Питер', 'питер': 'Санкт-Петербург', 'пспб': 'Санкт-Петербург',
-        'нью-йорке': 'New York', 'нью-йорк': 'New York', 'нью-йork': 'New York',
-        'флориде': 'Florida', 'флорида': 'Florida',
-        'clearwater': 'Clearwater', 'кливотер': 'Clearwater'
-    }
-    return city_mapping.get(city, city.title())
-
-def get_news(query="мировые"):
-    """📰 Точные новости"""
-    if not NEWS_API_KEY:
-        return "📰 NewsAPI ключ отсутствует"
-    
-    # Убираем лишние слова из запроса
-    clean_query = re.sub(r'(новости|news|что|происходит|события|последние)\s+', '', query.lower())
-    url = f"https://newsapi.org/v2/everything?q={clean_query}&language=ru&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
-    
+
+def normalize_word(text: str) -> str:
+    """Normalize incoming text to one clean token."""
+    return re.sub(r"[^\w\-']", "", text.strip().lower(), flags=re.UNICODE)
+
+
+def detect_language(word: str) -> str:
+    """Return 'ru' if Cyrillic found, otherwise 'en'."""
+    return "ru" if re.search(r"[а-яё]", word, re.IGNORECASE) else "en"
+
+
+def google_translate_data(word: str, source: str, target: str) -> Optional[List[Any]]:
+    """Google unofficial endpoint for translation + dictionary hints."""
+    url = (
+        "https://translate.googleapis.com/translate_a/single"
+        f"?client=gtx&sl={source}&tl={target}&dt=t&dt=bd&q={quote_plus(word)}"
+    )
     try:
-        resp = requests.get(url, timeout=12).json()
-        if resp.get('totalResults', 0) == 0:
-            return f"📰 По теме *'{query}'* новостей нет\n💡 Попробуй: Москва, Florida, США, мир"
-        
-        news = f"📰 *НОВОСТИ {query.upper()}*:\n\n"
-        for i, article in enumerate(resp['articles'], 1):
-            title = article['title'][:85]
-            source = article['source']['name']
-            link = article['url'][:45] + "..." if len(article['url']) > 45 else article['url']
-            news += f"{i}. *{title}*\n_{source}_\n`{link}`\n\n"
-        return news
-    except:
-        return "📰 Ошибка загрузки новостей"
-
-def get_weather(city="Clearwater"):
-    """🌤️ Погода любого города"""
-    if not WEATHER_API_KEY:
-        return "🌤️ WeatherAPI ключ отсутствует"
-    
-    clean_city = clean_city_name(city)
-    url = f"http://api.openweathermap.org/data/2.5/weather?q={clean_city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
-    
+        response = requests.get(url, timeout=12)
+        response.raise_for_status()
+        return response.json()
+    except Exception:
+        return None
+
+
+def extract_translations(payload: List[Any]) -> List[str]:
+    """Extract up to 3 unique translations from Google payload."""
+    candidates: List[str] = []
+
+    if payload and payload[0]:
+        for item in payload[0]:
+            translated = item[0].strip() if item and item[0] else ""
+            if translated:
+                candidates.append(translated)
+
+    if len(candidates) < 3 and len(payload) > 1 and payload[1]:
+        for entry in payload[1]:
+            if isinstance(entry, list) and len(entry) > 1 and isinstance(entry[1], list):
+                for term in entry[1]:
+                    if isinstance(term, str) and term.strip():
+                        candidates.append(term.strip())
+
+    seen = set()
+    unique = []
+    for item in candidates:
+        key = item.lower()
+        if key not in seen:
+            seen.add(key)
+            unique.append(item)
+        if len(unique) == 3:
+            break
+
+    return unique
+
+
+def datamuse_words(rel_type: str, word: str, max_items: int = 5) -> List[str]:
+    """Get related words from Datamuse (rel_syn or rel_ant)."""
     try:
-        resp = requests.get(url, timeout=10).json()
-        if resp.get('cod') != 200:
-            return f"❌ Город *'{clean_city}'* не найден\n💡 Москва, Florida, London, Рио, Питер"
-        
-        temp = int(resp['main']['temp'])
-        feels = int(resp['main']['feels_like'])
-        desc = resp['weather'][0]['description'].title()
-        humidity = resp['main']['humidity']
-        
-        return f"""🌤️ *{clean_city.upper()}: {temp}°C*
-🌡️ Ощущается: {feels}°C
-💧 Влажность: {humidity}%
-_{desc}_ ☀️"""
-    except:
-        return f"🌤️ *{clean_city}: {22}°C*, солнечно"
-
-def smart_parse(text):
-    """🧠 СУПЕР умный парсер русского"""
-    text = text.lower()
-    
-    # 🌤️ ПОГОДА - все варианты русского
-    weather_patterns = [
-        r'погода\s+(?:в\s+)?(.+?)(?:\?|!)',
-        r'температура\s+(?:в\s+)?(.+?)(?:\?|!)',
-        r'сколько\s+градус(?:ов)?\s+(?:в\s+)?(.+?)(?:\?|!)',
-        r'какая\s+погода\s+(?:в\s+)?(.+?)(?:\?|!)'
-    ]
-    
-    for pattern in weather_patterns:
-        match = re.search(pattern, text)
-        if match:
-            city = clean_city_name(match.group(1))
-            return ('weather', city)
-    
-    # 📰 НОВОСТИ - все варианты
-    news_patterns = [
-        r'(новости?|что\s+происходит|события?|последние\s+новости)\s+(?:про\s+|в\s+|о\s+)?(.+?)(?:\?|!)',
-        r'новости\s+(.+?)(?:\?|!)',
-        r'что\s+(?:в|про)\s+(.+?)(?:\?|!)'
-    ]
-    
-    for pattern in news_patterns:
-        match = re.search(pattern, text)
-        if match:
-            topic = match.group(1).strip()
-            return ('news', topic)
-    
-    # 📅 ДАТА/ВРЕМЯ
-    date_patterns = ['дата', 'число', 'день', 'время', 'сегодня']
-    if any(pattern in text for pattern in date_patterns):
-        return ('date', None)
-    
-    return ('help', None)
-
-@bot.message_handler(commands=['start', 'help'])
-def start(message):
-    bot.reply_to(message, """🤖 *Привет!* Твой УМНЫЙ ассистент 🧠
-
-*Пиши ЛЮБЫМИ словами:*
-📰 `погода в Москве`
-📰 `новости Флориды`
-🌤️ `температура Рио`
-📅 `какая дата?`
-
-*ПОНИМАЮ ВСЁ! 😎*""", parse_mode='Markdown')
-
-@bot.message_handler(content_types=['text'])
-def handle_message(message):
-    """ОДИН ответ - НИКОГДА дважды"""
-    chat_id = message.chat.id
-    text = message.text.strip()
-    
-    # НЕ отвечаем повторно на то же сообщение
+        url = f"https://api.datamuse.com/words?{rel_type}={quote_plus(word)}&max={max_items}"
+        data = requests.get(url, timeout=10).json()
+        return [item["word"] for item in data if item.get("word")]
+    except Exception:
+        return []
+
+
+def build_examples(word_en: str) -> Tuple[str, str]:
+    """Return one casual/slang and one neutral example."""
+    slang = f"That new playlist is {word_en} — no cap, I can't stop replaying it."
+    neutral = f"I used the word '{word_en}' in a meeting to describe the idea clearly."
+    return slang, neutral
+
+
+def build_word_card(user_word: str) -> str:
+    clean_word = normalize_word(user_word)
+    if not clean_word:
+        return "Напиши одно слово на русском или английском, и я разберу его."
+
+    src_lang = detect_language(clean_word)
+    target_lang = "en" if src_lang == "ru" else "ru"
+
+    payload = google_translate_data(clean_word, src_lang, target_lang)
+    if not payload:
+        return "Не удалось получить перевод. Попробуй ещё раз через пару секунд."
+
+    translations = extract_translations(payload)
+    if not translations:
+        return "Не нашёл переводов для этого слова. Попробуй другую форму слова."
+
+    # For synonyms/antonyms we need an English anchor word.
+    anchor_en = translations[0] if src_lang == "ru" else clean_word
+    anchor_en = anchor_en.lower()
+
+    synonyms = datamuse_words("rel_syn", anchor_en)
+    antonyms = datamuse_words("rel_ant", anchor_en)
+
+    slang_ex, neutral_ex = build_examples(anchor_en)
+
+    translation_block = "\n".join(
+        [f"{idx}. {val}" for idx, val in enumerate(translations[:3], 1)]
+    )
+    synonym_block = ", ".join(synonyms[:5]) if synonyms else "не нашёл"
+    antonym_block = ", ".join(antonyms[:5]) if antonyms else "не нашёл"
+
+    return (
+        f"📘 Слово: *{clean_word}*\n"
+        f"🌍 Язык: *{src_lang.upper()}*\n\n"
+        f"🔤 *3 перевода:*\n{translation_block}\n\n"
+        f"🔁 *Синонимы (EN):* {synonym_block}\n"
+        f"↔️ *Антонимы (EN):* {antonym_block}\n\n"
+        f"💬 *Примеры:*\n"
+        f"• Slang: _{slang_ex}_\n"
+        f"• Neutral: _{neutral_ex}_"
+    )
+
+
+@bot.message_handler(commands=["start", "help"])
+def start(message: telebot.types.Message) -> None:
+    bot.reply_to(
+        message,
+        (
+            "Привет! Я бот для изучения американского английского 🇺🇸\n\n"
+            "Отправь *одно слово* на русском или английском, и я дам:\n"
+            "• 3 перевода\n"
+            "• синонимы\n"
+            "• антонимы\n"
+            "• 2 примера (slang + neutral)"
+        ),
+        parse_mode="Markdown",
+    )
+
+
+@bot.message_handler(content_types=["text"])
+def handle_message(message: telebot.types.Message) -> None:
     try:
-        action, param = smart_parse(text)
-        
-        if action == 'weather':
-            city = param or "Clearwater"
-            weather = get_weather(city)
-            bot.reply_to(message, weather, parse_mode='Markdown')
-            
-        elif action == 'news':
-            topic = param or "мировые"
-            news = get_news(topic)
-            bot.reply_to(message, news, parse_mode='Markdown')
-            
-        elif action == 'date':
-            now = datetime.now()
-            answer = f"""📅 *4 марта 2026*
-*{now.strftime('%A').title()}*
-🕐 *{now.strftime('%H:%M')}*"""
-            bot.reply_to(message, answer, parse_mode='Markdown')
-            
-        else:
-            examples = """🤖 *ПРИМЕРЫ РУССКОГО:*
-
-📰 `погода в Москве`
-📰 `новости Флориды`  
-🌤️ `температура Барселона`
-📅 `какое сегодня число?`
-
-*ВСЕ формы пойму! 😎*"""
-            bot.reply_to(message, examples, parse_mode='Markdown')
-            
-    except Exception as e:
-        print(f"❌ Ошибка: {e}")
-        bot.reply_to(message, "😅 Момент, перезагружаюсь...")
-
-# ✅ СТАБИЛЬНЫЙ ЗАПУСК
-if __name__ == '__main__':
-    print("🚀 УМНЫЙ БОТ ЗАПУЩЕН!")
-    print("✅ Работает 24/7 без падений!")
-    
+        answer = build_word_card(message.text)
+        bot.reply_to(message, answer, parse_mode="Markdown")
+    except Exception as exc:
+        print(f"❌ Ошибка: {exc}")
+        bot.reply_to(message, "Словарь временно недоступен. Попробуй ещё раз.")
+
+
+if __name__ == "__main__":
+    print("🚀 Бот запущен!")
+
     while True:
         try:
             bot.polling(none_stop=False, interval=1, timeout=20)
-        except Exception as e:
-            print(f"🔄 Перезапуск: {e}")
+        except Exception as exc:
+            print(f"🔄 Перезапуск: {exc}")
             time.sleep(5)
 
EOF
)
