from venv import logger

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta, date

from aiogram.types import CallbackQuery
from aiogram.utils.callback_answer import CallbackAnswer

from keyboards.booking import get_time_selection_keyboard, get_calendar_keyboard, get_seats_for_date_keyboard, \
    get_booking_confirmation_keyboard, get_contact_keyboard
from keyboards.main_menu import get_main_menu

from database.requests import get_seat_by_id, get_booked_times_for_seat, get_user_by_telegram_id

router = Router()


# Создаем машину состояний для процесса брони
class BookingStates(StatesGroup):
    selecting_date = State()  # Выбор даты
    selecting_seat = State()  # Выбор места
    selecting_time = State()  # Выбор времени
    confirming = State()  # Подтверждение
    entering_name = State()  # Ввод имени
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
    import logging
    logger = logging.getLogger(__name__)

    logging.info("Приступили к выбору места")
    seat_id = int(callback.data.split("_")[1])
    await state.update_data(selected_seat_id=seat_id)
    logger.info("Сохранили место")

    logger.info("Получаем дату из state")
    data = await state.get_data()
    selected_date_str = data.get("selected_date")
    logger.info("Дата успешно получена")

    if not selected_date_str:
        logger.error(f"❌ Ошибка: дата не найдена")
        await callback.answer(f"❌ Ошибка: дата не найдена, попробуйте начать бронирование заново", show_alert=True)
        # При ошибке возвращаем в главное меню
        logger.info("Возвращаем в главное меню")
        await callback.message.edit_text("🤖 **Главное меню**\n\nВыберите действие:", reply_markup=get_main_menu(),
                                         parse_mode="Markdown")
        return

    # Преобразовываем строку в формат даты (объект date)
    from datetime import date
    selected_date = date.fromisoformat(selected_date_str)
    logger.info(f"Дата бронирования: {selected_date}")

    # Получаем информацию о месте
    from database.requests import get_seat_by_id
    seat = await get_seat_by_id(seat_id=seat_id)
    logger.info(f"Место получено {seat}")

    if not seat:
        logger.error(f"Место с ID {seat_id} не найдено")
        await callback.answer(f"❌ Место {seat} не найдено", show_alert=True)
        return

    # Показываем выбор времени
    await callback.message.edit_text(
        text=f"🕐 **Выберите время бронирования**\n\n"
             f"📍 Место: *{seat.name}*\n"
             f"📅 Дата: *{selected_date.strftime('%d.%m.%Y')}*\n\n"
             f"🟢 - свободно\n🔴 - занято",
        reply_markup=await get_time_selection_keyboard(seat_id, selected_date),
        parse_mode="Markdown"
    )
    await state.set_state(BookingStates.selecting_time)
    await callback.answer()


@router.callback_query(F.data.startswith("select_time"), BookingStates.selecting_time)
async def process_time_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора времени бронирования"""
    import logging
    logger = logging.getLogger(__name__)

    # Извлекаем дату (формат select_time_1200)
    time_str = callback.data.split("_")[2]
    # Преобразовываем в норм формат (12:00)
    selected_time = f"{time_str[:2]}:{time_str[2:]}"
    logger.info(f"Выбрано время {selected_time}")

    # Получаем данные из состояний
    data = await state.get_data()
    selected_date_str = data.get("selected_date")
    selected_seat_id = data.get("selected_seat_id")

    # Проверяем наличие необходимых данных
    if not selected_date_str or not selected_seat_id:
        logger.error("Отсутствуют данные о дате или месте")
        await callback.answer("❌ Ошибка: данные не найдены. Пожалуйста, начните бронирование заново.",
                              show_alert=True)
        await callback.message.edit_text("🤖 **Главное меню**\n\nВыберите действие:",
                                         reply_markup=get_main_menu(), parse_mode="Markdown")
        await state.clear()
        return

    # Преобразуем дату из строки
    selected_date = date.fromisoformat(selected_date_str)

    # Получаем информацию о месте
    seat = await get_seat_by_id(selected_seat_id)
    if not seat:
        logger.error(f"Место с ID {selected_seat_id} не найдено")
        await callback.answer("❌ Место не найдено", show_alert=True)
        await callback.message.edit_text(
            "🤖 **Главное меню**\n\nВыберите действие:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    # Проверяем, свободно ли место на выбранное время
    booked_times = await get_booked_times_for_seat(selected_seat_id, selected_date)

    if selected_time in booked_times:
        logger.warning(
            f"Попытка забронировать занятое время: место {seat.name}, "
            f"дата {selected_date}, время {selected_time}")
        await callback.answer(text="❌ К сожалению, это время уже занято.\nПожалуйста, выберите другое время.",
                              show_alert=True)

        await callback.message.edit_text(
            text=f"🕐 **Выберите время бронирования**\n\n"
                 f"📍 Место: *{seat.name}*\n"
                 f"📅 Дата: *{selected_date.strftime('%d.%m.%Y')}*\n\n"
                 f"🟢 - свободно\n🔴 - занято",
            reply_markup=await get_time_selection_keyboard(selected_seat_id, selected_date),
            parse_mode="Markdown")
        return

    # Сохраняем выбранное время в состояние
    await state.update_data(
        selected_time=selected_time,
        seat_name=seat.name
    )

    logger.info(f"Время {selected_time} для места {seat.name} сохранено")

    # Получаем информацию о пользователе
    user = await get_user_by_telegram_id(callback.from_user.id)

    # Формируем сообщение с подтверждением
    confirmation_text = (
        f"📝 **Подтверждение бронирования**\n\n"
        f"📍 Место: *{seat.name}*\n"
        f"📅 Дата: *{selected_date.strftime('%d.%m.%Y')}*\n"
        f"🕐 Время: *{selected_time}*\n\n"
    )

    # Если у пользователя есть телефон, показываем его
    if user and user.telephone_number:
        confirmation_text += f"📱 Телефон: *{user.telephone_number}*\n\n"
    else:
        confirmation_text += f"⚠️ *Внимание:* Для бронирования потребуется указать номер телефона\n\n"

    confirmation_text += (
        f"✅ *Проверьте данные* и подтвердите бронирование.\n"
        f"После подтверждения вы получите QR-код для входа."
    )

    await callback.message.edit_text(
        text=confirmation_text,
        reply_markup=get_booking_confirmation_keyboard(),
        parse_mode="Markdown"
    )

    # Устанавливаем состояние подтверждения
    await state.set_state(BookingStates.confirming)

    await callback.answer("✅ Время выбрано. Проверьте детали бронирования.")


@router.callback_query(F.data == "confirm_booking", BookingStates.confirming)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    """Подтверждение бронирования и создание заказа"""

    from qr.create_booking_order import create_booking_order

    # Получаем данные из состояний
    data = await state.get_data()
    selected_date_str = data.get("selected_date")
    selected_seat_id = data.get("selected_seat_id")
    selected_time = data.get("selected_time")
    seat_name = data.get("seat_name")

    # Проверяем наличие всех данных
    if not all([selected_date_str, selected_seat_id, selected_time, seat_name]):
        logger.error("Отсутствуют данные для подтверждения бронирования")
        await callback.answer("❌ ОШИБКА! Данные не найдены. Начните бронирование заново!", show_alert=True)
        await callback.message.edit_text(text="🤖 **Главное меню**\n\nВыберите действие:",
                                         reply_markup=get_main_menu(),
                                         parse_mode="Markdown")
        await state.clear()
        return
    selected_date = date.fromisoformat(selected_date_str)
    # Еще раз проверяем, что время все еще свободно (на случай, если другой пользователь успел забронировать)
    booked_times = await get_booked_times_for_seat(selected_seat_id, selected_date)

    if selected_time in booked_times:
        logger.warning(f"Время {selected_time} для места {selected_seat_id} уже занято в момент подтверждения")
        await callback.answer(text="❌ К сожалению, это время уже занято другим пользователем.\n"
                                   "Пожалуйста, выберите другое время.",
                              show_alert=True)

        # Выбор времени
        seat = await get_seat_by_id(selected_seat_id)
        await callback.message.edit_text(
            text=f"🕐 **Выберите время бронирования**\n\n"
                 f"📍 Место: *{seat.name if seat else 'неизвестно'}*\n"
                 f"📅 Дата: *{selected_date.strftime('%d.%m.%Y')}*\n\n"
                 f"🟢 - свободно\n🔴 - занято",
            reply_markup=await get_time_selection_keyboard(selected_seat_id, selected_date),
            parse_mode="Markdown"
        )
        await state.set_state(BookingStates.selecting_time)
        return

    # Получаем пользователя
    user = await get_user_by_telegram_id(callback.from_user.id)

    if not user:
        logger.error(f"Пользователь {callback.from_user.id} не найден в БД")
        await callback.answer(text="❌ Ошибка: пользователь не найден. Пожалуйста, используйте /start", show_alert=True)
        await state.clear()
        return

    # Проверяем наличие телефона
    if not user.telephone_number:
        # Создаем клавиатуру для отправки контакта
        contact_keyboard = get_contact_keyboard()

        await state.update_data(pending_booking=True)
        await state.set_state(BookingStates.entering_phone)

        await callback.message.edit_text(
            text="📱 **Для подтверждения бронирования необходимо указать номер телефона**\n\n"
                 "Пожалуйста, нажмите кнопку ниже, чтобы отправить ваш номер телефона.\n\n"
                 "Это необходимо для связи с вами и для входа в ресторан.",
            reply_markup=None,
            parse_mode="Markdown")

        await callback.message.answer(
            "Нажмите кнопку ниже, чтобы отправить номер телефона:",
            reply_markup=contact_keyboard)

        await callback.answer()
        return

    # Если телефон есть, создаем заказ
    await create_booking_order(callback=callback,
                               state=state,
                               user=user,
                               seat_id=selected_seat_id,
                               seat_name=seat_name,
                               selected_date=selected_date,
                               selected_time=selected_time)


@router.message(BookingStates.entering_phone, F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    """
    Обработка отправки контакта (номера телефона)
    """
    import logging
    from aiogram.types import ReplyKeyboardRemove
    from database.requests import update_user_phone
    from qr.create_booking_order import create_booking_order
    from datetime import date

    logger = logging.getLogger(__name__)

    # Получаем номер телефона из контакта
    phone_number = message.contact.phone_number

    # Обновляем номер телефона пользователя
    user = await update_user_phone(message.from_user.id, phone_number)

    if not user:
        logger.error(f"Не удалось обновить телефон для {message.from_user.id}")
        await message.answer(
            "❌ Ошибка при сохранении номера телефона. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    logger.info(f"Номер телефона {phone_number} сохранен для пользователя {message.from_user.id}")

    # Получаем данные из состояния
    data = await state.get_data()

    if data.get("pending_booking"):
        # Если было ожидание бронирования, продолжаем
        selected_date_str = data.get("selected_date")
        selected_seat_id = data.get("selected_seat_id")
        selected_time = data.get("selected_time")
        seat_name = data.get("seat_name")

        if all([selected_date_str, selected_seat_id, selected_time, seat_name]):
            selected_date = date.fromisoformat(selected_date_str)

            # Создаем mock callback для использования существующей функции
            from unittest.mock import AsyncMock

            class MockCallback:
                def __init__(self, message, from_user):
                    self.message = message
                    self.from_user = from_user
                    self.answer = AsyncMock()

            mock_callback = MockCallback(message, message.from_user)

            await create_booking_order(
                callback=mock_callback,
                state=state,
                user=user,
                seat_id=selected_seat_id,
                seat_name=seat_name,
                selected_date=selected_date,
                selected_time=selected_time
            )

            # Удаляем клавиатуру с контактом
            await message.answer(
                "✅ Спасибо! Ваш номер сохранен.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            logger.error("Отсутствуют данные бронирования после ввода телефона")
            await message.answer(
                "❌ Ошибка: данные бронирования не найдены. Пожалуйста, начните заново.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
    else:
        # Просто обновили телефон
        await message.answer(
            "✅ Номер телефона успешно сохранен!",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()


@router.message(BookingStates.entering_phone)
async def process_invalid_phone(message: types.Message, state: FSMContext):
    """
    Обработка некорректного ввода при ожидании телефона
    """
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "📱 Пожалуйста, используйте кнопку ниже для отправки номера телефона.\n\n"
        "Это необходимо для подтверждения бронирования.",
        reply_markup=contact_keyboard
    )
