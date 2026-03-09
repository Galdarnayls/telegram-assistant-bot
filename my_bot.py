 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/my_bot.py b/my_bot.py
index 8b137891791fe96927ad78e64b0aad7bded08bdc..393fbe1dc06b54470a3aa087d95985e001a0d8cd 100644
--- a/my_bot.py
+++ b/my_bot.py
@@ -1 +1,251 @@
+import os
+import threading
+from typing import List, Optional
 
+import requests
+import telebot
+from flask import Flask, request
+
+BOT_TOKEN = os.getenv("BOT_TOKEN")
+if not BOT_TOKEN:
+    raise RuntimeError("BOT_TOKEN is not set in environment variables.")
+
+WEBHOOK_URL = os.getenv("WEBHOOK_URL")
+RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")
+RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL")
+RAILWAY_PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_URL")
+PORT = int(os.getenv("PORT", "8080"))
+
+WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
+bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
+app = Flask(__name__)
+
+
+def unique(items: List[str]) -> List[str]:
+    seen = set()
+    result = []
+    for item in items:
+        normalized = item.strip().lower()
+        if not normalized or normalized in seen:
+            continue
+        seen.add(normalized)
+        result.append(item.strip())
+    return result
+
+
+def is_cyrillic(text: str) -> bool:
+    return any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in text)
+
+
+def get_translations(word: str, source_lang: str, target_lang: str, limit: int = 3) -> List[str]:
+    try:
+        response = requests.get(
+            "https://api.mymemory.translated.net/get",
+            params={"q": word, "langpair": f"{source_lang}|{target_lang}"},
+            timeout=10,
+        )
+        response.raise_for_status()
+    except requests.RequestException:
+        return []
+
+    data = response.json()
+    translations: List[str] = []
+
+    main_translation = data.get("responseData", {}).get("translatedText")
+    if main_translation:
+        translations.append(main_translation)
+
+    for match in data.get("matches", []):
+        translated = match.get("translation")
+        if translated:
+            translations.append(translated)
+
+    return unique(translations)[:limit]
+
+
+def get_synonyms(word: str, limit: int = 5) -> List[str]:
+    try:
+        response = requests.get(
+            "https://api.datamuse.com/words",
+            params={"rel_syn": word.lower(), "max": limit},
+            timeout=10,
+        )
+        response.raise_for_status()
+    except requests.RequestException:
+        return []
+
+    return unique([item.get("word", "") for item in response.json()])[:limit]
+
+
+def get_antonyms(word: str, limit: int = 5) -> List[str]:
+    try:
+        response = requests.get(
+            "https://api.datamuse.com/words",
+            params={"rel_ant": word.lower(), "max": limit},
+            timeout=10,
+        )
+        response.raise_for_status()
+    except requests.RequestException:
+        return []
+
+    return unique([item.get("word", "") for item in response.json()])[:limit]
+
+
+def get_standard_example(word: str) -> Optional[str]:
+    try:
+        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
+        response.raise_for_status()
+    except requests.RequestException:
+        return None
+
+    payload = response.json()
+    if not isinstance(payload, list):
+        return None
+
+    for entry in payload:
+        for meaning in entry.get("meanings", []):
+            for definition in meaning.get("definitions", []):
+                example = definition.get("example")
+                if example:
+                    return example
+    return None
+
+
+def get_slang_example(word: str) -> Optional[str]:
+    try:
+        response = requests.get(
+            "https://api.urbandictionary.com/v0/define",
+            params={"term": word},
+            timeout=10,
+        )
+        response.raise_for_status()
+    except requests.RequestException:
+        return None
+
+    payload = response.json()
+    if not isinstance(payload, dict):
+        return None
+
+    for item in payload.get("list", []):
+        example = item.get("example", "").replace("\r", " ").replace("\n", " ").strip()
+        if example:
+            return example
+    return None
+
+
+def format_list(items: List[str], fallback: str) -> str:
+    return ", ".join(items) if items else fallback
+
+
+@bot.message_handler(commands=["start", "help"])
+def send_welcome(message):
+    bot.reply_to(
+        message,
+        (
+            "Hi! Send me a Russian or English word, and I will return:\n"
+            "• 3 translations\n"
+            "• synonyms\n"
+            "• antonyms\n"
+            "• 2 examples (slang + neutral when available)"
+        ),
+    )
+
+
+@bot.message_handler(func=lambda m: True, content_types=["text"])
+def handle_word(message):
+    word = message.text.strip()
+    if not word:
+        bot.reply_to(message, "Please send a word.")
+        return
+
+    source_lang, target_lang = ("ru", "en") if is_cyrillic(word) else ("en", "ru")
+    translations = get_translations(word, source_lang, target_lang)
+
+    english_base = word.lower()
+    if source_lang == "ru" and translations:
+        english_base = translations[0].split(",")[0].strip().lower()
+
+    synonyms = get_synonyms(english_base)
+    antonyms = get_antonyms(english_base)
+    neutral_example = get_standard_example(english_base)
+    slang_example = get_slang_example(english_base)
+
+    examples: List[str] = []
+    if neutral_example:
+        examples.append(f"Neutral: {neutral_example}")
+    if slang_example:
+        examples.append(f"Slang: {slang_example}")
+    while len(examples) < 2:
+        examples.append("No more examples found right now.")
+
+    bot.reply_to(
+        message,
+        (
+            f"Word: {word}\n\n"
+            f"Translations (up to 3): {format_list(translations, 'not found')}\n"
+            f"Synonyms: {format_list(synonyms, 'not found')}\n"
+            f"Antonyms: {format_list(antonyms, 'not found')}\n\n"
+            "Examples:\n"
+            + "\n".join(f"- {example}" for example in examples[:2])
+        ),
+    )
+
+
+@app.get("/")
+def healthcheck():
+    return {"status": "ok", "webhook_path": WEBHOOK_PATH}, 200
+
+
+@app.post(WEBHOOK_PATH)
+def telegram_webhook():
+    content_type = request.headers.get("content-type", "")
+    if not content_type.startswith("application/json"):
+        return "Unsupported Media Type", 415
+
+    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
+    bot.process_new_updates([update])
+    return "", 200
+
+
+def _normalize_base_url(url: str) -> str:
+    clean = url.strip().rstrip("/")
+    if clean.startswith("http://") or clean.startswith("https://"):
+        return clean
+    return f"https://{clean}"
+
+
+def build_webhook_url() -> Optional[str]:
+    if WEBHOOK_URL:
+        base = _normalize_base_url(WEBHOOK_URL)
+    elif RAILWAY_PUBLIC_URL:
+        base = _normalize_base_url(RAILWAY_PUBLIC_URL)
+    elif RAILWAY_STATIC_URL:
+        base = _normalize_base_url(RAILWAY_STATIC_URL)
+    elif RAILWAY_PUBLIC_DOMAIN:
+        base = _normalize_base_url(RAILWAY_PUBLIC_DOMAIN)
+    else:
+        return None
+
+    if base.endswith(WEBHOOK_PATH):
+        return base
+    return f"{base}{WEBHOOK_PATH}"
+
+
+def start_polling_background() -> None:
+    polling_thread = threading.Thread(
+        target=bot.infinity_polling,
+        kwargs={"timeout": 30, "long_polling_timeout": 30},
+        daemon=True,
+    )
+    polling_thread.start()
+
+
+if __name__ == "__main__":
+    webhook_url = build_webhook_url()
+    if webhook_url:
+        bot.remove_webhook()
+        bot.set_webhook(url=webhook_url)
+    else:
+        start_polling_background()
+
+    app.run(host="0.0.0.0", port=PORT)
 
EOF
)
