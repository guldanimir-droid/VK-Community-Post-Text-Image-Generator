import os
import time
import requests
import random
import logging
import threading
from datetime import datetime

# ---------- ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ----------
CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
SCOPE = "GIGACHAT_API_PERS"

VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
# -----------------------------------------

TIMEOUT = 30
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- ФУНКЦИИ ДЛЯ GIGACHAT ----------
def get_gigachat_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Authorization": f"Basic {AUTH_KEY}",
        "RqUID": CLIENT_ID,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    payload = {"scope": SCOPE, "grant_type": "client_credentials"}
    resp = requests.post(url, headers=headers, data=payload, verify=False, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["access_token"]

def generate_short_post(token):
    topics = ["сочетание цветов", "капсульный гардероб", "тренды сезона", "уход за одеждой", "модные аксессуары"]
    topic = random.choice(topics)
    prompt = (
        f"Напиши короткий полезный совет по стилю на тему: {topic}. "
        "Без лишних слов, только совет. Используй дружелюбный тон, добавь эмодзи. "
        "Не добавляй ссылки и не упоминай другие сервисы. Длина: 200-400 символов."
    )
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 600
    }
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=TIMEOUT)
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    if not text or len(text) < 50 or "языковая модель" in text.lower():
        return generate_short_post(token)
    return text

def generate_long_article(token):
    topics = ["как определить свой тип фигуры", "базовый гардероб на все сезоны", "история маленького черного платья",
              "тренды предстоящего сезона", "как сочетать принты", "уход за разными тканями", "как выбрать джинсы по фигуре"]
    topic = random.choice(topics)
    prompt = (
        f"Напиши небольшую статью для блога о моде на тему: {topic}. "
        "Стиль — экспертный, но простой и дружелюбный. Разбей текст на короткие абзацы. "
        "Добавь полезные советы, примеры. Не используй ссылки и не упоминай ботов. "
        "Длина: 800-1500 символов. Используй эмодзи для оживления текста."
    )
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85,
        "max_tokens": 2000
    }
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=TIMEOUT)
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    if not text or len(text) < 300 or "языковая модель" in text.lower():
        return generate_long_article(token)
    return text

# ---------- ФУНКЦИИ ДЛЯ КАРТИНОК ----------
def get_random_fashion_image():
    query = random.choice(["fashion", "style", "outfit", "clothes", "streetwear", "elegant"])
    url = f"https://api.unsplash.com/photos/random?query={query}&orientation=landscape&client_id={UNSPLASH_ACCESS_KEY}"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return {
        "url": data["urls"]["regular"],
        "author_name": data["user"]["name"],
        "author_link": data["user"]["links"]["html"]
    }

def upload_photo_to_vk(image_url):
    logger.info("   → Получаем URL для загрузки фото...")
    get_upload_url = f"https://api.vk.com/method/photos.getWallUploadServer?group_id={VK_GROUP_ID}&access_token={VK_TOKEN}&v=5.131"
    resp = requests.get(get_upload_url, timeout=TIMEOUT)
    resp.raise_for_status()
    upload_data = resp.json()
    if "error" in upload_data:
        raise Exception(f"VK API error (getWallUploadServer): {upload_data['error']['error_msg']}")
    upload_url = upload_data["response"]["upload_url"]
    logger.info("   → Загружаем фото на сервер VK...")
    img_data = requests.get(image_url, timeout=TIMEOUT).content
    files = {"photo": ("image.jpg", img_data, "image/jpeg")}
    upload_resp = requests.post(upload_url, files=files, timeout=TIMEOUT)
    upload_resp.raise_for_status()
    upload_result = upload_resp.json()
    if "error" in upload_result:
        raise Exception(f"VK API error (upload): {upload_result['error']}")
    logger.info("   → Сохраняем фото в альбоме сообщества...")
    save_url = "https://api.vk.com/method/photos.saveWallPhoto"
    params = {
        "group_id": VK_GROUP_ID,
        "photo": upload_result["photo"],
        "server": upload_result["server"],
        "hash": upload_result["hash"],
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    save_resp = requests.post(save_url, data=params, timeout=TIMEOUT)
    save_resp.raise_for_status()
    save_result = save_resp.json()
    if "error" in save_result:
        raise Exception(f"VK API error (saveWallPhoto): {save_result['error']['error_msg']}")
    photo_info = save_result["response"][0]
    return f"photo{photo_info['owner_id']}_{photo_info['id']}"

def publish_to_vk(text, attachment):
    logger.info("   → Публикуем пост на стене...")
    vk_url = "https://api.vk.com/method/wall.post"
    data = {
        "owner_id": f"-{VK_GROUP_ID}",
        "from_group": 1,
        "message": text,
        "attachments": attachment,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    resp = requests.post(vk_url, data=data, timeout=TIMEOUT)
    resp.raise_for_status()
    result = resp.json()
    if "error" in result:
        raise Exception(f"VK API error (wall.post): {result['error']['error_msg']}")
    return result["response"]["post_id"]

def create_post(token, post_type):
    if post_type == "short":
        text = generate_short_post(token)
        logger.info("Сгенерирован короткий совет.")
    else:
        text = generate_long_article(token)
        logger.info("Сгенерирована статья.")
    
    logger.info("--- НАЧАЛО ТЕКСТА ---")
    logger.info(text)
    logger.info("--- КОНЕЦ ТЕКСТА ---")
    
    image_data = get_random_fashion_image()
    logger.info(f"Фото получено: {image_data['url']}")
    author_line = f"\n\n📷 Фото: {image_data['author_name']} / Unsplash"
    final_text = text + author_line
    
    attachment = upload_photo_to_vk(image_data["url"])
    logger.info("Фото загружено в VK.")
    post_id = publish_to_vk(final_text, attachment)
    logger.info(f"Пост опубликован! ID: {post_id}")

def posting_loop():
    schedule = ["short", "long", "short", "long", "short"]
    index = 0
    while True:
        try:
            token = get_gigachat_token()
            post_type = schedule[index % len(schedule)]
            logger.info(f"{datetime.now()}: Публикуем {post_type} пост...")
            create_post(token, post_type)
        except Exception as e:
            logger.error(f"Ошибка при публикации: {e}")
        index += 1
        logger.info("Ждём 8 часов до следующей публикации...")
        time.sleep(8 * 3600)

# ---------- ОБРАБОТЧИК КОММЕНТАРИЕВ ----------
def generate_comment_reply(comment_text):
    token = get_gigachat_token()
    prompt = (
        f"Ты — администратор модного сообщества. Пользователь написал: '{comment_text}'. "
        "Придумай вежливый, дружелюбный ответ (до 150 символов). Поблагодари или дай короткий совет по стилю. "
        "Не упоминай, что ты бот. Используй эмодзи. Ответ должен быть уместным и полезным."
    )
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 150
    }
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    reply = data["choices"][0]["message"]["content"].strip()
    if not reply:
        return "Спасибо за комментарий! 😊"
    return reply

def get_recent_posts(count=5):
    url = "https://api.vk.com/method/wall.get"
    params = {
        "owner_id": f"-{VK_GROUP_ID}",
        "count": count,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    resp = requests.get(url, params=params, timeout=TIMEOUT).json()
    if "error" in resp:
        logger.error(f"Ошибка получения постов: {resp}")
        return []
    return resp.get("response", {}).get("items", [])

def get_comments_for_post(post_id):
    url = "https://api.vk.com/method/wall.getComments"
    params = {
        "owner_id": f"-{VK_GROUP_ID}",
        "post_id": post_id,
        "count": 100,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    resp = requests.get(url, params=params, timeout=TIMEOUT).json()
    if "error" in resp:
        logger.error(f"Ошибка получения комментариев для поста {post_id}: {resp}")
        return []
    return resp.get("response", {}).get("items", [])

def reply_to_comment(comment_id, post_id, message):
    url = "https://api.vk.com/method/wall.createComment"
    params = {
        "owner_id": f"-{VK_GROUP_ID}",
        "post_id": post_id,
        "reply_to_comment": comment_id,
        "message": message,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    resp = requests.get(url, params=params, timeout=TIMEOUT).json()
    if "error" in resp:
        logger.error(f"Ошибка ответа: {resp}")
    else:
        logger.info(f"Ответили на комментарий {comment_id}")

def comments_loop():
    processed_ids = set()
    while True:
        try:
            posts = get_recent_posts(count=5)
            for post in posts:
                post_id = post["id"]
                comments = get_comments_for_post(post_id)
                for comment in comments:
                    comment_id = comment.get("id")
                    if comment_id in processed_ids:
                        continue
                    if comment.get("from_id", 0) < 0:  # пропускаем комментарии от сообщества
                        continue
                    if comment.get("text"):
                        reply = generate_comment_reply(comment["text"])
                        reply_to_comment(comment_id, post_id, reply)
                        processed_ids.add(comment_id)
                        time.sleep(3)
        except Exception as e:
            logger.error(f"Ошибка в цикле обработки комментариев: {e}")
        time.sleep(60)

# ---------- ЗАПУСК ВСЕХ ПОТОКОВ ----------
def main():
    t1 = threading.Thread(target=posting_loop, daemon=True)
    t1.start()
    logger.info("Автопостинг запущен.")

    t2 = threading.Thread(target=comments_loop, daemon=True)
    t2.start()
    logger.info("Обработчик комментариев запущен.")

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
