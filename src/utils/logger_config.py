import logging
import datetime
import os  # Import the 'os' module

def setup_logger(filename):
    # Создаем логгер
    logger = logging.getLogger("App")
    logger.setLevel(logging.DEBUG)

    # Формат сообщений
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Обработчик для записи в файл
    file_handler = logging.FileHandler(filename, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    logger.addHandler(file_handler)

    return logger

def create_log_file():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(log_dir, f"app_log_{current_time}.log")

    try:
        with open(filename, "x", encoding="utf-8") as f:
            f.write(f"Программа запущена: {current_time}\n")
        return filename  # <--- ДОБАВИТЬ ЭТО (возвращаем путь после создания файла)
    except FileExistsError:
        return filename
    except Exception as e:
        print(f"Ошибка при создании лога: {e}") # Для отладки
        return filename