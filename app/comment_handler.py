import requests
import openai
import time
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VK_API_KEY = os.getenv("VK_API_KEY")
GROUP_ID = os.getenv("VK_GROUP_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def get_comments(last_comment_id=0):
    url = "https://api.vk.com/method/wall.getComments"
    params = {
        "owner_id": -int(GROUP_ID),
        "need_likes": 0,
        "count": 100,
        "access_token": VK_API_KEY,
        "v": "5.131"
    }
    resp = requests.get(url, params=params).json()
    if "error" in resp:
        logger.error(f"Ошибка получения комментариев: {resp}")
        return []
    return resp.get("response", {}).get("items", [])

def reply_to_comment(comment_id, post_id, message):
    url = "https://api.vk.com/method/wall.createComment"
    params = {
        "owner_id": -int(GROUP_ID),
        "post_id": post_id,
        "reply_to_comment": comment_id,
        "message": message,
        "access_token": VK_API_KEY,
        "v": "5.131"
    }
    resp = requests.get(url, params=params).json()
    if "error" in resp:
        logger.error(f"Ошибка ответа: {resp}")
    else:
        logger.info(f"Ответили на комментарий {comment_id}")

def generate_reply(comment_text):
    prompt = f"Ты — администратор модного сообщества. Пользователь написал: '{comment_text}'. Придумай вежливый, дружелюбный ответ (до 150 символов), поблагодари или дай короткий совет по стилю."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def process_comments_loop():
    processed_ids = set()
    while True:
        comments = get_comments()
        for comment in comments:
            if comment["id"] not in processed_ids and comment.get("text"):
                reply = generate_reply(comment["text"])
                reply_to_comment(comment["id"], comment["post_id"], reply)
                processed_ids.add(comment["id"])
                time.sleep(3)  # пауза между ответами
        time.sleep(60)  # проверяем каждую минуту
