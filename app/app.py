import threading
import time
import os
import logging
from post_generator import run_posting_loop   # ваш существующий модуль
from comment_handler import process_comments_loop
from invite_manager import invite_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Запускаем все сервисы в отдельных потоках
    t1 = threading.Thread(target=run_posting_loop, daemon=True)
    t2 = threading.Thread(target=process_comments_loop, daemon=True)
    t3 = threading.Thread(target=invite_loop, daemon=True)
    
    t1.start()
    t2.start()
    t3.start()
    
    # Основной поток просто спит
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
