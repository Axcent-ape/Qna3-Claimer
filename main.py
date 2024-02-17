import random
from core.qna3 import Qna3
from core.utils import random_line, logger, add_line
import asyncio
from data import config


async def retry_function(func, thread, *args, **kwargs):
    while True:
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Поток {thread} | Ошибка выполнения функции {func.__name__}: {e}")
            await asyncio.sleep(30)


async def QNA(thread):
    logger.info(f"Поток {thread} | Начал работу")
    while True:
        act = await random_line('data/accounts.txt')
        if not act: break

        if '::' in act:
            private_key, proxy = act.split('::')
        else:
            private_key = act
            proxy = None

        qna = Qna3(key=private_key, proxy=proxy)

        if await retry_function(qna.login, thread):
            points = await qna.get_points_to_claim()
            if points >= config.MINIMUM_POINTS:
                status, tx_hash, points = await qna.claim_points()

                if status:
                    logger.success(f"Поток {thread} | Заклеймил {points} поинтов! {qna.web3_utils.acct.address}:{tx_hash}")
                    await add_line('data/checked_accounts.txt', f"{qna.web3_utils.acct.key.hex()}:{points}")
                else:
                    logger.error(f"Поток {thread} | Не заклеймил {points} поинтов! {qna.web3_utils.acct.address}:{tx_hash}")
            else:
                logger.warning(f"Поток {thread} | На аккаунте {qna.web3_utils.acct.address} мешьше {config.MINIMUM_POINTS} поитов ({points})")
                await add_line('data/checked_accounts.txt', f"{qna.web3_utils.acct.key.hex()}:{points}")

        await qna.logout()
        await sleep(thread)

    logger.info(f"Поток {thread} | Закончил работу")


async def sleep(thread):
    rt = random.randint(50, 60)
    logger.info(f"Поток {thread} | Спит {rt} c.")

    await asyncio.sleep(rt)


async def main():
    print("Автор софта: https://t.me/ApeCryptor")

    thread_count = int(input("Введите кол-во потоков: "))
    # thread_count = 1
    tasks = []
    for thread in range(1, thread_count+1):
        tasks.append(asyncio.create_task(QNA(thread)))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
