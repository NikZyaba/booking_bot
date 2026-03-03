from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.requests import get_all_seats, get_available_seats


async def get_seats_keyboard() -> InlineKeyboardMarkup:
    """Все места в заведении"""

    # Получаем все места в заведении
    seats = await get_all_seats()
    # Создаем клавиатуру
    keyboard_buttons = []

    for seat in seats:

        # Создаем кнопку для каждого места
        button = InlineKeyboardButton(
            text=f"{seat.name}",
            callback_data=f"get_seat_{seat.id}"
        )
        keyboard_buttons.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

async def get_available_seats_keyboard() -> InlineKeyboardMarkup:
    """Получить все доступные места в заведении"""

    # Получаем места в заведении еще не заказанные
    seats = await get_available_seats()

    keyboard_buttons = []

    for seat in seats:
        button = InlineKeyboardButton(
            text=f"🟢 {seat.name}",
            callback_data=f"select_seat_{seat.id}"  # другой callback для бронирования
        )
        keyboard_buttons.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


async def get_seats_by_status_keyboard(show_booked: bool = True) -> InlineKeyboardMarkup:
    """
    Создаем клавиатуру с возможностью фильтрации по статусу
    """
    seats = await get_all_seats()

    keyboard_buttons = []

    for seat in seats:
        # Пропускаем занятые места, если не нужно их показывать
        if not show_booked and seat.is_booked:
            continue

        # Выбираем эмодзи
        if seat.is_booked:
            emoji = "🔴"
            callback = f"booked_seat_{seat.id}"
        else:
            emoji = "🟢"
            callback = f"free_seat_{seat.id}"

        button = InlineKeyboardButton(
            text=f"{emoji} {seat.name}",
            callback_data=callback
        )
        keyboard_buttons.append([button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)



