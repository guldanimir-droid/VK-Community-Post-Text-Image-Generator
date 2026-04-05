import os
import time
import json
import requests
import random
from datetime import datetime

# ---------- ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ (RAILWAY) ----------
CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
SCOPE = "GIGACHAT_API_PERS"

VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
# ----------------------------------------------------

def get_gigachat_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Authorization": f"Basic {AUTH_KEY}",
        "RqUID": CLIENT_ID,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    payload = {"scope": SCOPE, "grant_type": "client_credentials"}
    resp = requests.post(url, headers=headers, data=payload, verify=False)
    resp.raise_for_status()
    return resp.json()["access_token"]

def generate_post_text(token):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    topics = ["цветовые сочетания", "капсульный гардероб", "тренды сезона", "уход за одеждой", "модные аксессуары"]
    system_prompt = (
        "Ты — профессиональный SMM-менеджер сообщества о моде и стиле. "
        "Напиши пост для ВКонтакте на тему моды. Тон — экспертный, дружелюбный. "
        "Пост должен содержать полезный совет и заканчиваться призывом попробовать бота-стилиста: @stil_snap_ai_bot. "
        "Используй эмодзи, делай пост живым. Не добавляй в текст упоминания про Unsplash или автора фото, это будет отдельно."
    )
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Создай пост на тему: {random.choice(topics)}. Сегодня {datetime.now().strftime('%d.%m.%Y')}."}
        ],
        "temperature": 0.8,
        "max_tokens": 800
    }
    resp = requests.post(url, headers=headers, json=payload, verify=False)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def get_random_fashion_image():
    """Получает URL случайного фото моды с Unsplash и данные автора"""
    query = random.choice(["fashion", "style", "outfit", "clothes", "streetwear", "elegant"])
    url = f"https://api.unsplash.com/photos/random?query={query}&orientation=landscape&client_id={UNSPLASH_ACCESS_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return {
        "url": data["urls"]["regular"],
        "author_name": data["user"]["name"],
        "author_link": data["user"]["links"]["html"]
    }

def upload_photo_to_vk(image_url):
    get_upload_url = f"https://api.vk.com/method/photos.getWallUploadServer?group_id={VK_GROUP_ID}&access_token={VK_TOKEN}&v=5.131"
    resp = requests.get(get_upload_url)
    resp.raise_for_status()
    upload_url = resp.json()["response"]["upload_url"]
    img_data = requests.get(image_url).content
    files = {"photo": ("image.jpg", img_data, "image/jpeg")}
    upload_resp = requests.post(upload_url, files=files)
    upload_resp.raise_for_status()
    upload_data = upload_resp.json()
    save_url = "https://api.vk.com/method/photos.saveWallPhoto"
    params = {
        "group_id": VK_GROUP_ID,
        "photo": upload_data["photo"],
        "server": upload_data["server"],
        "hash": upload_data["hash"],
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    save_resp = requests.post(save_url, data=params)
    save_resp.raise_for_status()
    photo_info = save_resp.json()["response"][0]
    return f"photo{photo_info['owner_id']}_{photo_info['id']}"

def publish_to_vk(text, attachment):
    vk_url = "https://api.vk.com/method/wall.post"
    params = {
        "owner_id": f"-{VK_GROUP_ID}",
        "from_group": 1,
        "message": text,
        "attachments": attachment,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    resp = requests.post(vk_url, params=params)
    resp.raise_for_status()
    result = resp.json()
    if "error" in result:
        raise Exception(f"VK error: {result['error']['error_msg']}")
    return result["response"]["post_id"]

def main():
    print(f"{datetime.now()}: Начинаем создание поста...")
    token = get_gigachat_token()
    post_text = generate_post_text(token)
    print("Текст сгенерирован.")
    
    image_data = get_random_fashion_image()
    print(f"Фото получено: {image_data['url']}")
    author_line = f"\n\n📷 Фото: {image_data['author_name']} / Unsplash"
    final_text = post_text + author_line
    
    attachment = upload_photo_to_vk(image_data["url"])
    print("Фото загружено в VK.")
    
    post_id = publish_to_vk(final_text, attachment)
    print(f"Пост опубликован! ID: {post_id}")

if __name__ == "__main__":
    while True:
        main()
        print("Ждём 8 часов до следующей публикации...")
        time.sleep(8 * 3600)
