import time
import requests
import os

# --- КОНФИГУРАЦИЯ ---
# Получаем ключи и ID из переменных окружения (их нужно будет добавить в Railway)
VK_API_KEY = os.getenv("VK_API_KEY")           # Ключ доступа к API ВКонтакте
GROUP_ID = os.getenv("VK_GROUP_ID")            # ID вашего сообщества (числовой)
# -------------------

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С API ---
def search_users(keyword, count=5):
    """Ищет пользователей по ключевому слову через метод users.search"""
    url = "https://api.vk.com/method/users.search"
    params = {
        "q": keyword,                     # Поисковый запрос (например, "мода", "стиль")
        "count": count,                   # Количество пользователей для поиска
        "fields": "id, first_name, last_name", # Какие поля получить о пользователе
        "access_token": VK_API_KEY,
        "v": "5.131"
    }
    try:
        response = requests.get(url, params=params).json()
        if "error" in response:
            print(f"Ошибка поиска: {response['error']['error_msg']}")
            return []
        # Возвращаем список пользователей
        return response.get("response", {}).get("items", [])
    except Exception as e:
        print(f"Ошибка при запросе к API: {e}")
        return []

def is_member(user_id):
    """Проверяет, состоит ли пользователь с user_id в вашем сообществе"""
    url = "https://api.vk.com/method/groups.isMember"
    params = {
        "group_id": GROUP_ID,
        "user_id": user_id,
        "access_token": VK_API_KEY,
        "v": "5.131"
    }
    try:
        response = requests.get(url, params=params).json()
        if "error" in response:
            print(f"Ошибка проверки: {response['error']['error_msg']}")
            return False
        # Если response['response'] == 1, значит пользователь в группе
        return response.get("response", 0) == 1
    except Exception as e:
        print(f"Ошибка при запросе к API: {e}")
        return False

def invite_user(user_id):
    """Отправляет приглашение пользователю вступить в сообщество"""
    url = "https://api.vk.com/method/groups.invite"
    params = {
        "group_id": GROUP_ID,
        "user_id": user_id,
        "access_token": VK_API_KEY,
        "v": "5.131"
    }
    try:
        response = requests.get(url, params=params).json()
        if "error" in response:
            error_msg = response['error']['error_msg']
            # Если пользователь уже получил приглашение или не может его принять
            if "invite" in error_msg.lower() or "already" in error_msg.lower():
                print(f"Не удалось пригласить {user_id}: возможно, уже приглашён или его настройки это запрещают.")
                return False
            else:
                print(f"Ошибка при приглашении {user_id}: {error_msg}")
                return False
        print(f"✅ Приглашение отправлено пользователю {user_id}")
        return True
    except Exception as e:
        print(f"Ошибка при запросе к API: {e}")
        return False

# --- ОСНОВНАЯ ЛОГИКА РАБОТЫ СКРИПТА ---
def invite_people_by_keywords(keywords, invites_per_day=40, pause_seconds=180):
    """
    Основная функция для запуска процесса приглашений.
    keywords: список ключевых слов для поиска (например, ['мода', 'стиль', 'одежда'])
    invites_per_day: лимит приглашений в день (максимум 40)
    pause_seconds: пауза между приглашениями в секундах (минимум 180 секунд = 3 минуты)
    """
    invited_today = 0
    for keyword in keywords:
        if invited_today >= invites_per_day:
            print("Дневной лимит приглашений исчерпан. Завершаем работу.")
            break

        print(f"\n--- Поиск пользователей по ключевому слову: '{keyword}' ---")
        # Ищем до 10 пользователей за раз
        users = search_users(keyword, count=10)
        if not users:
            print(f"По запросу '{keyword}' никого не найдено.")
            continue

        for user in users:
            if invited_today >= invites_per_day:
                break

            user_id = user['id']
            user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}"

            # Проверяем, не состоит ли уже в группе
            if is_member(user_id):
                print(f"Пользователь {user_name} (id: {user_id}) уже в сообществе. Пропускаем.")
                continue

            # Отправляем приглашение
            print(f"Приглашаем {user_name} (id: {user_id})...")
            if invite_user(user_id):
                invited_today += 1
                print(f"Осталось приглашений на сегодня: {invites_per_day - invited_today}")
            else:
                print(f"Не удалось пригласить {user_name}. Возможно, ошибка или лимит.")

            # Делаем паузу между приглашениями, чтобы не нарушать лимиты ВК
            print(f"Ожидание {pause_seconds} секунд перед следующим приглашением...")
            time.sleep(pause_seconds)

    print(f"\nРабота скрипта завершена. Всего отправлено приглашений: {invited_today}")

if __name__ == "__main__":
    # Запускаем процесс приглашений. Здесь можно указать свои ключевые слова.
    keywords_to_search = ["мода", "стиль", "одежда", "тренды", "look"]
    invite_people_by_keywords(keywords_to_search)
