from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta, date

from aiogram.types import CallbackQuery
from aiogram.utils.callback_answer import CallbackAnswer

from keyboards.booking import get_date_selection_keyboard, get_time_selection_keyboard

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
    await callback.message.edit_text(text="📅 Выберите дату бронирования:", reply_markup=get_date_selection_keyboard())
    await state.set_state(BookingStates.selecting_date)
    await callback.answer()

@router.callback_query(F.data.startswith("select_date_"))
async def process_date_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    # Потом тут будет обработка календаря
    pass

@router.callback_query(F.data.startswith("seat_"))
async def process_seat_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор определенного места"""
    seat_id = int(callback.data.split("_")[1])
    await state.update_data(selected_seat_id=seat_id)

    # Показать доступное время на эту дату
    # --------------------------- потом будет клавиатура----------------------------------
    await callback.message.edit_text(text="🕐 Выберите время бронирования:", reply_markup=None)
    await state.set_state(BookingStates.selecting_time)