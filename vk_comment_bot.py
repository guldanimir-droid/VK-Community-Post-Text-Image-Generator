import time
import os
import random
from datetime import datetime, timedelta
import vk_api
from vk_api.exceptions import ApiError

# --- КОНФИГУРАЦИЯ (читаем из переменных окружения) ---
VK_TOKEN = os.getenv("VK_TOKEN")            # токен сообщества (уже есть)
VK_GROUP_ID = os.getenv("VK_GROUP_ID")      # ID вашего сообщества (число)
KEYWORDS = os.getenv("COMMENT_KEYWORDS", "мода,стиль,образ").split(",")
COMMENT_MESSAGE = os.getenv("COMMENT_MESSAGE", """🔥 Устали ломать голову над своим стилем?

Попробуйте нашего бесплатного AI-стилиста в Telegram: @stil_snap_ai_bot

Оценит ваш образ, даст советы и подберёт гардероб! 👔""")
POSTS_PER_CYCLE = int(os.getenv("POSTS_PER_CYCLE", "10"))
SLEEP_BETWEEN_COMMENTS = int(os.getenv("SLEEP_BETWEEN_COMMENTS", "30"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "14400"))  # 4 часа
# -------------------------------------------------------

def vk_auth():
    try:
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()
        # Проверяем токен
        vk.groups.getById(group_id=VK_GROUP_ID)
        print("[INFO] Авторизация успешна")
        return vk
    except ApiError as e:
        print(f"[ERROR] Ошибка авторизации: {e}")
        exit()

def search_posts(vk, keyword, start_time):
    try:
        response = vk.newsfeed.search(q=keyword, count=POSTS_PER_CYCLE, start_time=start_time, v='5.131')
        return response.get('items', [])
    except ApiError as e:
        print(f"[ERROR] Ошибка поиска постов: {e}")
        return []

def post_comment(vk, owner_id, post_id):
    try:
        vk.wall.createComment(owner_id=owner_id, post_id=post_id, message=COMMENT_MESSAGE)
        print(f"[OK] Комментарий оставлен под постом {owner_id}_{post_id}")
        return True
    except ApiError as e:
        print(f"[ERROR] Не удалось оставить комментарий: {e}")
        return False

def main():
    vk = vk_auth()
    processed_posts = set()
    # Ищем посты за последние 6 часов (чтобы не уходить в глубокое прошлое)
    last_search_time = int((datetime.now() - timedelta(hours=6)).timestamp())
    
    print(f"[INFO] Бот запущен. Ключевые слова: {KEYWORDS}")
    while True:
        try:
            for keyword in KEYWORDS:
                posts = search_posts(vk, keyword.strip(), last_search_time)
                new_posts = 0
                for post in posts:
                    post_id = post['id']
                    owner_id = post['owner_id']
                    post_key = f"{owner_id}_{post_id}"
                    if post_key in processed_posts:
                        continue
                    # Не комментируем свои посты
                    if owner_id == -int(VK_GROUP_ID):
                        processed_posts.add(post_key)
                        continue
                    if post_comment(vk, owner_id, post_id):
                        processed_posts.add(post_key)
                        new_posts += 1
                        time.sleep(SLEEP_BETWEEN_COMMENTS)
                if new_posts:
                    print(f"[INFO] По ключевому слову '{keyword}' прокомментировано {new_posts} постов")
            # Обновляем время поиска
            last_search_time = int(datetime.now().timestamp())
            print(f"[INFO] Цикл завершён. Следующая проверка через {CHECK_INTERVAL//3600} час(ов)")
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"[ERROR] Непредвиденная ошибка: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()
