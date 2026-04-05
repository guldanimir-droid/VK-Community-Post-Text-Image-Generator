import os
import time
import base64
import json
import requests
import random
from datetime import datetime
from typing import List, Dict, Any

# ===================== НАСТРОЙКИ =====================
# !!! ВСТАВЬТЕ ВАШИ ДАННЫЕ СЮДА !!!
CLIENT_ID = "019d2da0-5e49-7ccc-bc86-17c4b0473e1a"  # Ваш Client ID
AUTH_KEY = "MDE5ZDJkYTAtNWU0OS03Y2NjLWJjODYtMTdjNGIwNDczZTFhOjE4NjllYmU5LTVhNTMtNDFmZi1iNGY5LTUyYTY4ZjcxNmU5YQ=="  # Ваш Authorization Key
SCOPE = "GIGACHAT_API_PERS"  # Ваш Scope

# Настройки VK
VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")
# =====================================================

def get_gigachat_token() -> str:
    """Получение токена доступа к GigaChat API"""
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Authorization": f"Basic {AUTH_KEY}",
        "RqUID": CLIENT_ID,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    payload = {
        "scope": SCOPE,
        "grant_type": "client_credentials"
    }

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения токена GigaChat: {e}")
        if response:
            print(f"Ответ сервера: {response.text}")
        raise

def generate_post_content(token: str) -> Dict[str, Any]:
    """Генерация поста через GigaChat API"""
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    system_prompt = (
        "Ты — профессиональный SMM-менеджер сообщества о моде и стиле. "
        "Напиши пост для ВКонтакте на тему моды. Тон поста — экспертный, но дружелюбный. "
        "Пост должен содержать полезный совет (например, как сочетать цвета, что надеть, тренды сезона) "
        "и заканчиваться призывом попробовать бота-стилиста в Telegram: @stil_snap_ai_bot. "
        "Используй эмодзи, делай пост живым и вовлекающим."
    )

    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Создай пост на тему моды. Сегодня {datetime.now().strftime('%d.%m.%Y')}. Используй случайную тему из списка: цветовые сочетания, капсульный гардероб, тренды сезона, уход за одеждой, модные аксессуары."}
        ],
        "temperature": 0.8,
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        result = response.json()
        post_text = result["choices"][0]["message"]["content"]
        return {"text": post_text}
    except requests.exceptions.RequestException as e:
        print(f"Ошибка генерации поста: {e}")
        if response:
            print(f"Ответ сервера: {response.text}")
        raise

def upload_to_vk(group_id: str, post_data: Dict[str, Any]) -> None:
    """Публикация поста в VK"""
    vk_url = "https://api.vk.com/method/wall.post"
    params = {
        "owner_id": f"-{group_id}",
        "from_group": 1,
        "message": post_data["text"],
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    try:
        response = requests.post(vk_url, params=params)
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            print(f"Ошибка VK API: {result['error']['error_msg']}")
        else:
            print(f"Пост опубликован! ID: {result['response']['post_id']}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка публикации в VK: {e}")
        if response:
            print(f"Ответ сервера: {response.text}")
        raise

def main():
    print("Начинаем создание поста...")
    try:
        token = get_gigachat_token()
        post = generate_post_content(token)
        print(f"Сгенерирован пост:\n{post['text']}\n")
        upload_to_vk(VK_GROUP_ID, post)
        print("Пост успешно опубликован!")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
    # Бесконечный цикл для ежедневного запуска
    while True:
        time.sleep(86400)  # 24 часа
        main()
