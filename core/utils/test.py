import hashlib


def convert_to_hash(number):
    # Преобразование числа в строку перед хешированием
    input_string = str(number)

    # Используем SHA-256 для создания хеша
    hash_object = hashlib.sha256(input_string.encode())

    # Получаем хеш в виде строки шестнадцатеричных символов
    hash_hex = hash_object.hexdigest()

    # Если вам нужна фиксированная длина 64 символа, вы можете дополнить хеш нулями
    hash_64_chars = hash_hex.zfill(64)

    return hash_64_chars


# Пример использования
number_to_convert = 162
hashed_value = convert_to_hash(number_to_convert)
print(hashed_value)
