import os
import requests
import json
import time

# --- НАСТРОЙКИ ---
# Токен бота вы получите от @BotFather
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# Ваш chat_id (узнать можно у @userinfobot)
MY_CHAT_ID = os.environ.get("MY_CHAT_ID")
# Файл, где храним последний обработанный update_id
STATE_FILE = "last_update.txt"
# ----------------

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 5}
    if offset:
        params["offset"] = offset
    resp = requests.get(url, params=params).json()
    return resp.get("result", [])

def load_last_id():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def save_last_id(uid):
    with open(STATE_FILE, "w") as f:
        f.write(str(uid))

def do_search(username):
    """Простой поиск через публичный API whatsmyname (бесплатно, без ключа)"""
    # Используем открытый API, который не требует токена
    url = f"https://whatsmyname.app/api/check?username={username}"
    try:
        resp = requests.get(url, timeout=20)
        data = resp.json()
        # Формат ответа может меняться, поэтому проверяем
        if isinstance(data, dict) and "found" in data:
            return data["found"]
        # Если структура другая, просто вернём всё что есть
        return data
    except Exception as e:
        return f"Ошибка поиска: {e}"

def main():
    last_id = load_last_id()
    updates = get_updates(offset=last_id + 1 if last_id else None)

    for upd in updates:
        last_id = upd["update_id"]
        msg = upd.get("message", {})
        text = msg.get("text", "")
        chat_id = msg.get("chat", {}).get("id")

        if not text or not chat_id:
            continue

        # Проверяем, что пишет именно владелец (для безопасности)
        if str(chat_id) != str(MY_CHAT_ID):
            send_message(chat_id, "⛔ Бот только для владельца.")
            continue

        if text.startswith("/start"):
            send_message(chat_id, "👋 Отправь мне username (без @), я поищу аккаунты.")
        else:
            username = text.strip().lstrip("@")
            if len(username) < 3:
                send_message(chat_id, "❌ Слишком короткий username.")
                continue

            send_message(chat_id, f"🔎 Ищу `{username}`...")
            result = do_search(username)

            # Формируем текстовый ответ
            if isinstance(result, list):
                if not result:
                    send_message(chat_id, f"😕 По `{username}` ничего не найдено.")
                else:
                    lines = [f"✅ Найдено: {len(result)}", ""]
                    for item in result[:50]:  # ограничим 50 строками
                        if isinstance(item, dict):
                            site = item.get("site", "?")
                            link = item.get("url", "")
                            lines.append(f"• {site}: {link}")
                        else:
                            lines.append(f"• {item}")
                    send_message(chat_id, "\n".join(lines))
            else:
                send_message(chat_id, f"📦 Результат:\n```\n{result}\n```")

    save_last_id(last_id)

if __name__ == "__main__":
    main()
