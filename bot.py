import asyncio
import os

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# 1. Загружаем переменные окружения
load_dotenv()

# 2. Настраиваем систему логирования
# 3. Создаем команды бота на главное меню

# 4. Создаем основную функцию запуска бота
async def main():
    bot = Bot(token=os.getenv("TOKEN"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())