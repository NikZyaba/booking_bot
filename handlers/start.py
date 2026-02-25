from aiogram import Router, types
from aiogram.filters import Command

# Импорты кнопок
from keyboards.main_menu import get_main_menu


router = Router()

@router.message(Command("start"))
async def cmd_start(message:types.Message):

    # Получаем имя пользователя, указанный в ТГ
    first_name = message.from_user.first_name
    welcome_text = (
        f"👋 Привет, {first_name or 'друг'}\n"
        f"Вас приветствует телеграмм бот компании XXX 'XXXX'\n\n"
        "⚡ Доступные команды:\n"
        "/all_seats - запросить все места ресторана\n"
        "/my_orders - мои заказы\n"
        "/make_order - забронировать новое место\n"
    )
    # Потом будет клавиатура для меню----------------------↓
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
    # Потом будет клавиатура для меню-------------------↓
    await message.answer(text=help_text, reply_markup=get_main_menu())