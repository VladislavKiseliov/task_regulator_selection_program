import hashlib

def calculate_hash(string:str) -> str:
    # Создаем объект хеша
    hash_object = hashlib.sha256()

    # Обновляем хеш с данными из строки
    hash_object.update(string.encode('utf-8'))

    # Получаем хеш-сумму в виде шестнадцатеричной строки
    hash_string = hash_object.hexdigest()

    return hash_string