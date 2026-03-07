from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu():
    """Основное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📍 Все места", callback_data="cmd_show_all_seats"),
        ],
        [
            InlineKeyboardButton(text="📅 Забронировать новое место", callback_data="create_order"),
        ],
        [
            InlineKeyboardButton(text="📋 Мои брони", callback_data="my_orders"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ])
    return keyboard