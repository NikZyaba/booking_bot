import asyncio
import os
from time import sleep

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import time

# 1. Загружаем переменные окружения
load_dotenv()

# 2. Настраиваем систему логирования
# 3. Создаем команды бота на главное меню

# 4. Создаем основную функцию запуска бота
async def main():
    bot = Bot(token=os.getenv("TOKEN"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    print("Бот готов к запуску")

    try:
        # Блок с регистрацией роутеров
        from handlers.start import router as start_router
        from handlers.callbacks import router as callbacks_router


        dp.include_router(start_router)
        dp.include_router(callbacks_router)

        # Ставим время сна для отладки процессов (режим разработки)
        time.sleep(1)
        print("______________Роутеры зарегистрированы____________________")
    except Exception as e:
        return f"Произошла ошибка при загрузке роутеров {e}"

    # Ставим время сна для отладки процессов (режим разработки)
    time.sleep(1)
    print("______________Бот запущен____________________")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())