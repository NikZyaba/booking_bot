from aiogram import Router, types
from keyboards.seats import get_seats_keyboard
from aiogram.filters import Command

router = Router()

# Обработчик для команды /all_seats
@router.message(Command("all_seats"))
async def cmd_show_all_seats(message: types.Message) -> None:
    """Показываем все места по команде /all_seats"""
    keyboard = await get_seats_keyboard()
    await message.answer("📍 Все места в заведении:", reply_markup=keyboard)



# Обработчик для callback с главного меню
@router.callback_query(lambda c: c.data == "cmd_show_all_seats")
async def callback_show_all_seats(callback: types.CallbackQuery) -> None:
    """Показываем все места при нажатии на кнопку в меню"""
    keyboard = await get_seats_keyboard()
    await callback.message.edit_text("📍 Все места в заведении:",reply_markup=keyboard)
    await callback.answer()