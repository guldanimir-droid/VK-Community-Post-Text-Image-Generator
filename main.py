import os
import time
import requests
import random
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

def generate_short_post(token, attempt=1):
    topics = [
        "как сочетать бежевый с другими цветами",
        "почему oversize подходит не всем",
        "как носить ремень поверх пальто",
        "3 базовые футболки в гардеробе",
        "как выбрать джинсы по фигуре"
    ]
    topic = random.choice(topics)
    prompt = (
        f"Ты — стилист. Напиши короткий совет (2-3 предложения) на тему: {topic}. "
        "Совет должен быть практичным, без общих фраз. Не упоминай, что ты ИИ. Только мода и стиль. "
        "Добавь эмодзи в конце. Длина до 300 символов."
    )
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 500
    }
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=TIMEOUT)
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    forbidden = ["языковая модель", "генеративная", "чувствительные темы", "ограничены", "не обладают собственным мнением"]
    if any(word in text.lower() for word in forbidden) or len(text) < 50:
        if attempt < 3:
            return generate_short_post(token, attempt + 1)
        else:
            return "Подберите базовые вещи: классические джинсы, белую рубашку и удобные кроссовки. Они всегда в моде! 😊"
    return text

def generate_long_article(token, attempt=1):
    topics = [
        "как собрать капсульный гардероб на весну",
        "5 ошибок в повседневном образе",
        "как подобрать обувь к платью",
        "тренды этого года: что носить",
        "как ухаживать за кожаной курткой"
    ]
    topic = random.choice(topics)
    prompt = (
        f"Ты — стилист. Напиши короткую статью (5-7 предложений) на тему: {topic}. "
        "Советы должны быть конкретными, полезными. Не упоминай, что ты ИИ. Только мода. "
        "Разбей на абзацы. Добавь эмодзи. Длина 500-800 символов."
    )
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1200
    }
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=TIMEOUT)
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    forbidden = ["языковая модель", "генеративная", "чувствительные темы", "ограничены", "не обладают собственным мнением"]
    if any(word in text.lower() for word in forbidden) or len(text) < 300:
        if attempt < 3:
            return generate_long_article(token, attempt + 1)
        else:
            return "Капсульный гардероб: выберите 2-3 базовых цвета, добавьте акцентные вещи и качественную обувь. Это сэкономит время и деньги! 💡"
    return text

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
    print("   → Получаем URL для загрузки фото...")
    get_upload_url = f"https://api.vk.com/method/photos.getWallUploadServer?group_id={VK_GROUP_ID}&access_token={VK_TOKEN}&v=5.131"
    resp = requests.get(get_upload_url, timeout=TIMEOUT)
    resp.raise_for_status()
    upload_data = resp.json()
    if "error" in upload_data:
        raise Exception(f"VK API error (getWallUploadServer): {upload_data['error']['error_msg']}")
    upload_url = upload_data["response"]["upload_url"]
    print("   → Загружаем фото на сервер VK...")
    img_data = requests.get(image_url, timeout=TIMEOUT).content
    files = {"photo": ("image.jpg", img_data, "image/jpeg")}
    upload_resp = requests.post(upload_url, files=files, timeout=TIMEOUT)
    upload_resp.raise_for_status()
    upload_result = upload_resp.json()
    if "error" in upload_result:
        raise Exception(f"VK API error (upload): {upload_result['error']}")
    print("   → Сохраняем фото в альбоме сообщества...")
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
    print("   → Публикуем пост на стене...")
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
        print("Сгенерирован короткий совет.")
    else:
        text = generate_long_article(token)
        print("Сгенерирована статья.")
        print(f"Длина статьи: {len(text)} символов")
    
    print("--- НАЧАЛО ТЕКСТА ---")
    print(text)
    print("--- КОНЕЦ ТЕКСТА ---")
    
    image_data = get_random_fashion_image()
    print(f"Фото получено: {image_data['url']}")
    author_line = f"\n\n📷 Фото: {image_data['author_name']} / Unsplash"
    final_text = text + author_line
    
    attachment = upload_photo_to_vk(image_data["url"])
    print("Фото загружено в VK.")
    post_id = publish_to_vk(final_text, attachment)
    print(f"Пост опубликован! ID: {post_id}")

def main():
    schedule = ["short", "long", "short", "long", "short"]
    index = 0
    while True:
        try:
            token = get_gigachat_token()
            post_type = schedule[index % len(schedule)]
            print(f"{datetime.now()}: Публикуем {post_type} пост...")
            create_post(token, post_type)
        except Exception as e:
            print(f"❌ Ошибка при создании поста: {e}")
            import traceback
            traceback.print_exc()
        index += 1
        print("Ждём 8 часов до следующей публикации...")
        time.sleep(8 * 3600)

if __name__ == "__main__":
    main()
