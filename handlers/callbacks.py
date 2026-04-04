from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, date

from keyboards.main_menu import get_main_menu
from handlers.seats import get_seats_keyboard
from keyboards.booking import (
    get_calendar_keyboard,
    get_seats_for_date_keyboard,
    get_time_selection_keyboard
)
from database.requests import get_seat_by_id

router = Router()


@router.callback_query(lambda c: c.data == "main_menu")
async def process_main_menu(callbacks: types.CallbackQuery, state: FSMContext):  # Добавил state для очистки
    """Показать главное меню"""
    # Очищаем состояние при возврате в главное меню
    await state.clear()

    await callbacks.message.edit_text("🤖 **Главное меню**\n\nВыберите действие:", reply_markup=get_main_menu(), parse_mode="Markdown")
    await callbacks.answer()


@router.callback_query(lambda c: c.data == "help")
async def process_help(callbacks: types.CallbackQuery):
    """Показать сообщение помощи"""
    from handlers.start import cmd_help
    await cmd_help(callbacks.message)
    await callbacks.answer()


@router.callback_query(lambda c: c.data == "cmd_show_all_seats")
async def callback_show_all_seats(callback: types.CallbackQuery) -> None:
    """Показываем все места при нажатии на кнопку в меню"""
    from handlers.seats import cmd_show_all_seats
    await cmd_show_all_seats(callback.message)
    await callback.answer()


@router.callback_query(F.data == "back_to_date")
async def back_to_date(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору даты"""
    from handlers.booking import BookingStates

    current_date = datetime.now()

    await callback.message.edit_text(
        text="📅 **Выберите дату бронирования**",
        reply_markup=get_calendar_keyboard(year=current_date.year, month=current_date.month), parse_mode="Markdown")
    await state.set_state(BookingStates.selecting_date)
    await callback.answer()


@router.callback_query(F.data == "back_to_seats")
async def back_to_seats(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору места"""
    from handlers.booking import BookingStates

    data = await state.get_data()

    if 'selected_date' in data:
        selected_date = date.fromisoformat(data['selected_date'])

        await callback.message.edit_text(
            text="🪑 **Выберите место**\n\n"
                 f"📅 Дата: *{selected_date.strftime('%d.%m.%Y')}*",
            reply_markup=await get_seats_for_date_keyboard(selected_date), parse_mode="Markdown")
        await state.set_state(BookingStates.selecting_seat)
    else:
        # Если дата не найдена, возвращаемся в главное меню
        await callback.message.edit_text(
            "🤖 **Главное меню**\n\n"
            "Произошла ошибка. Начните заново.", reply_markup=get_main_menu(), parse_mode="Markdown")
        await state.clear()

    await callback.answer()


@router.callback_query(F.data == "back_to_times")
async def back_to_times(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору времени"""
    from handlers.booking import BookingStates

    data = await state.get_data()

    if 'selected_date' in data and 'selected_seat_id' in data:
        selected_date = date.fromisoformat(data['selected_date'])
        seat_id = data['selected_seat_id']
        seat = await get_seat_by_id(seat_id)

        if seat:
            await callback.message.edit_text(
                text=f"🕐 **Выберите время бронирования**\n\n"
                     f"📍 Место: *{seat.name}*\n"
                     f"📅 Дата: *{selected_date.strftime('%d.%m.%Y')}*\n\n"
                     f"🟢 - свободно\n🔴 - занято",
                reply_markup=await get_time_selection_keyboard(seat_id, selected_date), parse_mode="Markdown")
            await state.set_state(BookingStates.selecting_time)
        else:
            await callback.answer("❌ Место не найдено", show_alert=True)
            await state.clear()
    else:
        await callback.answer("❌ Ошибка: данные не найдены", show_alert=True)
        await state.clear()

    await callback.answer()


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: types.CallbackQuery, state: FSMContext):
    """Отмена бронирования"""
    await state.clear()
    await callback.message.edit_text(
        text="❌ **Бронирование отменено**\n\n"
             "Вы можете начать заново через главное меню.", reply_markup=get_main_menu(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    """Игнорирование неактивных кнопок"""
    await callback.answer("❌ Это действие недоступно", show_alert=True)