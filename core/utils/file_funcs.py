import random


async def random_line(filepath: str, delete: bool = True):
    with open(filepath, 'r') as file:
        keys = file.readlines()

    if not keys:
        return False
    random_key = random.choice(keys)
    if delete:
        keys.remove(random_key)

        with open(filepath, 'w') as file:
            file.writelines(keys)

    return random_key.strip()


async def add_line(filepath: str, line: str):
    with open(filepath, 'a') as file:
        file.write(f"{line}\n")