import os
import time
import json
import requests
from datetime import datetime

# Переменные окружения (устанавливаются в Railway)
CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
SCOPE = "GIGACHAT_API_PERS"  # фиксированное значение

VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")

def get_gigachat_token():
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
    response = requests.post(url, headers=headers, data=payload, verify=False)
    response.raise_for_status()
    return response.json()["access_token"]

def generate_post(token):
    """Генерация поста через GigaChat"""
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
    response = requests.post(url, headers=headers, json=payload, verify=False)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def publish_to_vk(text):
    """Публикация поста в VK"""
    vk_url = "https://api.vk.com/method/wall.post"
    params = {
        "owner_id": f"-{VK_GROUP_ID}",
        "from_group": 1,
        "message": text,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    response = requests.post(vk_url, params=params)
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise Exception(f"VK error: {result['error']['error_msg']}")
    return result["response"]["post_id"]

def main():
    print("Начинаем создание поста...")
    token = get_gigachat_token()
    post_text = generate_post(token)
    print(f"Сгенерирован пост:\n{post_text}\n")
    post_id = publish_to_vk(post_text)
    print(f"Пост опубликован! ID: {post_id}")

if __name__ == "__main__":
    main()
    # Бесконечный цикл для публикации раз в сутки
    while True:
        time.sleep(86400)  # 24 часа
        main()
