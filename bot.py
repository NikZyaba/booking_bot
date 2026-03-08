import asyncio

# Для внешних программ ОС
import os
import sys
import logging
import subprocess

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# 1. Загружаем переменные окружения
load_dotenv()

# 2. Настраиваем систему логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 3. Делаем миграции до запуска бота
async def run_alembic_migrations():
    """Запуск миграций Alembic перед стартом бота"""
    try:
        logger.info("Применение миграций базы данных...")

        # Запускам alembic upgrade head
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))  # Корневая папка проекта
        )
        if result.returncode == 0:
            logger.info("✅ Миграции успешно применены")
            if result.stdout:
                logger.debug(f"Вывод: {result.stdout}")
        else:
            logger.error(f"❌ Ошибка при применении миграций: {result.stderr}")
            raise Exception("Failed to apply migrations")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при миграциях: {e}")
        sys.exit(1)

# 3. Создаем команды бота на главное меню
async def set_bot_commands(bot: Bot):
    """Установка команд бота"""
    from aiogram.types import BotCommand, BotCommandScopeDefault

    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="all_seats", description="Все места"),
        BotCommand(command="my_orders", description="Мои заказы"),
        BotCommand(command="make_order", description="Забронировать место"),
    ]

    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("🚀 Бот запускается...")

    # Применяем миграции
    await run_alembic_migrations()
    # Устанавливаем команды бота
    await set_bot_commands(bot)

    logger.info("✅ Бот готов к работе!")


# 4. Создаем основную функцию запуска бота
async def main():
    bot = Bot(token=os.getenv("TOKEN"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем обработчик запуска
    dp.startup.register(on_startup)

    logger.info("Бот готов к запуску")

    try:
        # Регистрация роутеров
        from handlers.start import router as start_router
        from handlers.callbacks import router as callbacks_router
        from  handlers.seats import router as seats_router
        from handlers.booking import router as booking_router

        dp.include_router(start_router)
        dp.include_router(callbacks_router)
        dp.include_router(seats_router)
        dp.include_router(booking_router)

        logger.info("✅ Роутеры зарегистрированы")
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке роутеров: {e}")
        return

    logger.info("🚀 Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())