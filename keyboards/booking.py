from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta


def get_date_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора даты"""
    buttons = []

    # Текущая дата + 30 дней
    for i in range(30):
        date = datetime.now() + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y")
        buttons.append([InlineKeyboardButton(text=date_str, callback_data=f"select_date_{date.strftime('%Y%m%d')}")])
        # Дополняем кнопки навигации
        buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"),
            InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")
        ])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_time_selection_keyboard(seat_id: int, selected_date: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора свободного времени"""

    time_slots = ["12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]

    buttons = []
    #Разбиваю по три кнопки в ряду
    for i in range(0, len(time_slots), 3):
        row = []
        for time in time_slots[i:i+3]:
            # Тут проверка на бронь места (свободно-ли)
            is_free = True  # Заглушка (придумал только так)
            emoji = "🟢" if is_free else "🔴"
            row.append(InlineKeyboardButton(text=f"{emoji} {time}",
                                            callback_data=f"select_time_{time.replace(':', '')}"))

        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_dates"),
        InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения бронирования"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_times"),
            InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")
        ]
    ])

def get_phone_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура пропуска ввода телефона"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Без номера телефона", callback_data="skip_phone")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_confirmation")]
    ])