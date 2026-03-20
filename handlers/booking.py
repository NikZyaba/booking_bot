from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta, date

from aiogram.types import CallbackQuery
from aiogram.utils.callback_answer import CallbackAnswer

from keyboards.booking import get_date_selection_keyboard, get_time_selection_keyboard, get_calendar_keyboard, get_seats_for_date_keyboard

router = Router()

# Создаем машину состояний для процесса брони
class BookingStates(StatesGroup):
    selecting_date = State()  # Выбор даты
    selecting_seat = State()  # Выбор места
    selecting_time = State()  # Выбор времени
    confirming = State()      # Подтверждение
    entering_name = State()   # Ввод имени
    entering_phone = State()  # Ввод телефона


@router.callback_query(F.data == "create_order")
async def start_booking(callback: types.CallbackQuery, state: FSMContext):
    """Начало бронирования (экран выбора даты)"""
    current_date = datetime.now()

    await callback.message.edit_text(
        text="📅 **Выберите дату бронирования**\n\n"
             f"Доступны даты на ближайшие 30 дней",
        reply_markup=get_calendar_keyboard(current_date.year, current_date.month),
        parse_mode="Markdown"
    )
    await state.set_state(BookingStates.selecting_date)
    await callback.answer()


@router.callback_query(F.data.startswith("calendar_"))
async def process_calendar_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка навигации по календарю и выбор даты"""
    import logging
    logger = logging.getLogger(__name__)

    # Проверяем состояние
    current_state = await state.get_state()
    logger.info(f"process_calendar_callback - текущее состояние: {current_state}")

    # Если состояние не selecting_date, игнорируем
    if current_state != BookingStates.selecting_date.state:
        await callback.answer("❌ Сначала выберите дату из календаря", show_alert=True)
        return

    action = callback.data.split("_")
    logger.info(f"Разобранный callback: {action}")

    if len(action) < 2:
        await callback.answer("❌ Ошибка формата", show_alert=True)
        return

    if action[1] == "nav":
        # Навигация по месяцам
        year = int(action[2])
        month = int(action[3])

        # Обновляем календарь
        await callback.message.edit_text(
            text="📅 **Выберите дату бронирования**",
            reply_markup=get_calendar_keyboard(year, month),
            parse_mode="Markdown"
        )
        await callback.answer()

    elif action[1] == "day":
        # Выбрана конкретная дата
        year = int(action[2])
        month = int(action[3])
        day = int(action[4])

        selected_date = date(year, month, day)
        current_date = date.today()
        max_date = current_date + timedelta(days=30)

        # Валидация даты
        if selected_date < current_date:
            await callback.answer("❌ Нельзя выбрать дату в прошлом", show_alert=True)
            return

        if selected_date > max_date:
            await callback.answer("❌ Нельзя выбрать дату более чем через 30 дней", show_alert=True)
            return

        # Сохраняем выбранную дату
        await state.update_data(selected_date=selected_date.isoformat())
        logger.info(f"Дата сохранена: {selected_date}")

        # Получаем клавиатуру с местами
        seats_keyboard = await get_seats_for_date_keyboard(selected_date)

        # Переходим к выбору места
        await callback.message.edit_text(
            text="🪑 **Выберите место**\n\n"
                 f"📅 Дата: *{selected_date.strftime('%d.%m.%Y')}*",
            reply_markup=seats_keyboard,
            parse_mode="Markdown"
        )
        await state.set_state(BookingStates.selecting_seat)
        await callback.answer()

    else:
        logger.warning(f"Неизвестный тип callback: {action[1]}")
        await callback.answer("❌ Неизвестная команда", show_alert=True)

@router.callback_query(F.data.startswith("seat_"), BookingStates.selecting_seat)
async def process_seat_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор определенного места"""
    seat_id = int(callback.data.split("_")[1])
    await state.update_data(selected_seat_id=seat_id)

    # Показать доступное время на эту дату
    # --------------------------- потом будет клавиатура----------------------------------
    await callback.message.edit_text(text="🕐 Выберите время бронирования:", reply_markup=get_time_selection_keyboard)
    await state.set_state(BookingStates.selecting_time)

