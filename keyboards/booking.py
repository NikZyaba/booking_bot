from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, date, timedelta
import calendar
from database.requests import get_booked_times_for_seat




async def get_time_selection_keyboard(seat_id: int, selected_date: date) -> InlineKeyboardMarkup:
    """Клавиатура для выбора свободного времени"""

    time_slots = ["12:00", "13:00", "14:00", "15:00", "16:00",
                  "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]

    # Получаем забронированные времена из БД
    booked_times = await get_booked_times_for_seat(seat_id, selected_date)

    buttons = []
    # Разбиваю по три кнопки в ряду
    for i in range(0, len(time_slots), 3):
        row = []
        for time in time_slots[i:i + 3]:
            # Проверяем, свободно ли время
            is_free = time not in booked_times
            emoji = "🟢" if is_free else "🔴"

            # Если время занято, делаем кнопку неактивной
            if is_free:
                callback_data = f"select_time_{time.replace(':', '')}"
            else:
                callback_data = "ignore"

            row.append(InlineKeyboardButton(
                text=f"{emoji} {time}",
                callback_data=callback_data
            ))

        if row:  # Добавляем только непустые ряды
            buttons.append(row)

    # Добавляем кнопки навигации
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад к местам", callback_data="back_to_seats"),
        InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_seats_for_date_keyboard(selected_date: date) -> InlineKeyboardMarkup:
    """Клавиатура для выбора места на конкретную дату"""
    from database.requests import get_all_seats, get_booked_times_for_seat

    seats = await get_all_seats()

    time_slots = ["12:00", "13:00", "14:00", "15:00", "16:00",
                  "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]
    total_slots = len(time_slots)

    buttons = []

    for seat in seats:
        # Получаем забронированные времена для этого места
        booked_times = await get_booked_times_for_seat(seat.id, selected_date)
        booked_count = len(booked_times)

        # Определяем статус места
        if booked_count == 0:
            emoji = "🟢"
            status = "свободно"
            callback_data = f"seat_{seat.id}"
        elif booked_count < total_slots:
            emoji = "🟡"
            free_count = total_slots - booked_count
            status = f"свободно {free_count}/{total_slots}"
            callback_data = f"seat_{seat.id}"
        else:
            emoji = "🔴"
            status = "занято"
            callback_data = "ignore"

        button = InlineKeyboardButton(
            text=f"{emoji} {seat.name} ({status})",
            callback_data=callback_data
        )
        buttons.append([button])

    # Добавляем кнопки навигации
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад к дате", callback_data="back_to_date"),
        InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_calendar_keyboard(year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """Создает инлайн-клавиатуру с календарем для выбора даты"""
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    # Создаем объект календаря
    cal = calendar.monthcalendar(year, month)

    # Названия месяцев на русском
    months_ru = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    # Дни недели (с понедельника)
    weekdays_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    keyboard = []

    # Заголовок с месяцем и годом
    header_text = f"{months_ru[month - 1]} {year}"
    keyboard.append([InlineKeyboardButton(text=header_text, callback_data="ignore")])

    # Строка с днями недели
    weekday_row = []
    for day in weekdays_ru:
        weekday_row.append(InlineKeyboardButton(text=day, callback_data="ignore"))
    keyboard.append(weekday_row)

    # Дни месяца
    current_date = date.today()
    max_date = current_date + timedelta(days=30)

    for week in cal:
        row = []
        for day in week:
            if day == 0:
                # Пустой день
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                # Проверяем, доступна ли дата
                cell_date = date(year, month, day)

                if cell_date < current_date:
                    # Дата в прошлом
                    text = "❌"
                    callback = "ignore"
                elif cell_date > max_date:
                    # Более чем через 30 дней
                    text = "🔒"
                    callback = "ignore"
                else:
                    # Доступная дата
                    text = str(day)
                    callback = f"calendar_day_{year}_{month}_{day}"

                row.append(InlineKeyboardButton(text=text, callback_data=callback))
        keyboard.append(row)

    # Кнопки навигации по месяцам
    nav_row = []

    # Предыдущий месяц
    prev_month_date = datetime(year, month, 1) - timedelta(days=1)
    nav_row.append(InlineKeyboardButton(
        text="◀️",
        callback_data=f"calendar_nav_{prev_month_date.year}_{prev_month_date.month}"
    ))

    # Кнопка "На главную"
    nav_row.append(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))

    # Следующий месяц
    next_month_date = datetime(year, month, 1) + timedelta(days=32)
    nav_row.append(InlineKeyboardButton(
        text="▶️",
        callback_data=f"calendar_nav_{next_month_date.year}_{next_month_date.month}"
    ))

    keyboard.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_booking_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking"),
            InlineKeyboardButton(text="✏️ Изменить время", callback_data="back_to_times")
        ],
        [
            InlineKeyboardButton(text="🪑 Другое место", callback_data="back_to_seats"),
            InlineKeyboardButton(text="📅 Другая дата", callback_data="back_to_date")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_booking")
        ]
    ])
    return confirmation_keyboard

def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки контакта"""
    contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return contact_keyboard