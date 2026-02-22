from aiogram import Router, types
from aiogram.filters import Command


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
    await message.answer(text=welcome_text, reply_markup=None)