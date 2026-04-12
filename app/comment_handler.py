import time
import requests
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
VK_API_KEY = os.getenv("VK_API_KEY")      # Ключ доступа VK API (с правами на чтение комментариев)
GROUP_ID = os.getenv("VK_GROUP_ID")

TIMEOUT = 30

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

def generate_reply(comment_text):
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
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
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
        "owner_id": f"-{GROUP_ID}",
        "count": count,
        "access_token": VK_API_KEY,
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
        "owner_id": f"-{GROUP_ID}",
        "post_id": post_id,
        "count": 100,
        "access_token": VK_API_KEY,
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
        "owner_id": f"-{GROUP_ID}",
        "post_id": post_id,
        "reply_to_comment": comment_id,
        "message": message,
        "access_token": VK_API_KEY,
        "v": "5.131"
    }
    resp = requests.get(url, params=params, timeout=TIMEOUT).json()
    if "error" in resp:
        logger.error(f"Ошибка ответа: {resp}")
    else:
        logger.info(f"Ответили на комментарий {comment_id}")

def process_comments_loop():
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
                    # Не отвечаем на свои комментарии (от сообщества)
                    if comment.get("from_id", 0) < 0:
                        continue
                    if comment.get("text"):
                        reply = generate_reply(comment["text"])
                        reply_to_comment(comment_id, post_id, reply)
                        processed_ids.add(comment_id)
                        time.sleep(3)  # пауза между ответами
        except Exception as e:
            logger.error(f"Ошибка в цикле обработки комментариев: {e}")
        time.sleep(60)  # проверяем раз в минуту
