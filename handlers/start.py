from aiogram import Router, types
from aiogram.filters import Command

# Импорты кнопок
from keyboards.main_menu import get_main_menu

# Импорты времени
from datetime import date

# Запросы в БД
from database.requests import get_user_by_telegram_id, create_user

# Импорт логов
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # Получаем данные пользователя из Telegram
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    # Проверяем, есть ли пользователь в БД
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        # Создаем нового пользователя
        try:
            user = await create_user(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                telephone_number=None,  # Телефон пока не знаем
                date_registry=date.today()  # Дата регистрации - сегодня
            )

            # Логируем создание нового пользователя
            logger.info(f"✅ Новый пользователь создан: {telegram_id} (@{username})")

            welcome_text = (
                f"👋 Привет, {first_name or 'друг'}!\n"
                f"Рады видеть вас впервые в нашем ресторане!\n\n"
                f"Вас приветствует телеграмм бот компании XXX 'XXXX'\n\n"
                f"⚡ Доступные команды:\n"
                f"/all_seats - запросить все места ресторана\n"
                f"/my_orders - мои заказы\n"
                f"/make_order - забронировать новое место\n\n"
                f"📱 Для бронирования нам понадобится ваш номер телефона.\n"
                f"Вы укажете его при заказе места."
            )

        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя {telegram_id}: {e}")
            await message.answer(
                "😔 Произошла ошибка при регистрации. Пожалуйста, попробуйте позже."
            )
            return
    else:
        # Обновляем информацию о пользователе (имя могло измениться)
        # Это можно сделать позже через отдельную функцию обновления

        welcome_text = (
            f"👋 С возвращением, {first_name or 'друг'}!\n"
            f"Рады снова видеть вас в нашем ресторане!\n\n"
            f"⚡ Доступные команды:\n"
            f"/all_seats - запросить все места ресторана\n"
            f"/my_orders - мои заказы\n"
            f"/make_order - забронировать новое место"
        )

    # Отправляем приветственное сообщение с меню
    await message.answer(text=welcome_text, reply_markup=get_main_menu())

@router.message(Command("help"))
async def cmd_help(message:types.Message):
    help_text = (
        f"Эта команда описывает основные команды бота\n"
        "⚡ Доступные команды:\n"
        "/all_seats - запросить все места ресторана\n"
        "/my_orders - мои заказы\n"
        "/make_order - забронировать новое место\n"
        "/seat_by_date - показать места по дате\n"
        "Пока многие функции находятся в разработке"
    )

    await message.answer(text=help_text, reply_markup=get_main_menu())