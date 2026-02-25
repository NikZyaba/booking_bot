from aiogram import Router, types

from keyboards.main_menu import get_main_menu

router = Router()


@router.callback_query(lambda c: c.data == "main_menu")
async def process_main_menu(callbacks: types.CallbackQuery):
    """Показать главное меню"""
    await callbacks.message.edit_text(
        "🤖 **Главное меню**\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )
    await callbacks.answer()


@router.callback_query(lambda c: c.data == "help")
async def process_help(callbacks: types.CallbackQuery):
    """Показать сообщение помощи"""
    from handlers.start import cmd_help
    await cmd_help(callbacks.message)
    await callbacks.answer()