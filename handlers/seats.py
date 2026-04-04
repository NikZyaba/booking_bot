from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
import logging

from keyboards.seats import get_seats_keyboard

from database.requests import get_all_seats, get_seat_by_id

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("all_seats"))
async def cmd_show_all_seats(message: types.Message) -> None:
    """Показываем все места по команде /all_seats"""
    seats = await get_all_seats()

    if not seats:
        await message.answer("❌ В заведении пока нет мест")
        return

    # Создаем клавиатуру со списком мест
    keyboard_buttons = []
    for seat in seats:
        button = InlineKeyboardButton(
            text=f"🪑 {seat.name}",
            callback_data=f"info_seat_{seat.id}"
        )
        keyboard_buttons.append([button])

    # Добавляем кнопку главного меню
    keyboard_buttons.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    # Редактируем текущее сообщение, а не отправляем новое
    await message.edit_text(
        "📍 Все места в заведении:\n\n"
        "Выберите место, чтобы увидеть информацию о нем:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("info_seat_"))
async def show_seat_info(callback: types.CallbackQuery) -> None:
    """
    Показывает информацию о выбранном месте
    """
    try:
        # Извлекаем ID места из callback_data
        seat_id = int(callback.data.split("_")[2])

        # Получаем информацию о месте из БД
        seat = await get_seat_by_id(seat_id)

        if not seat:
            await callback.answer("❌ Место не найдено", show_alert=True)
            return

        # Формируем текст с информацией о месте
        info_text = (
            f"🪑 <b>{seat.name}</b>\n\n"
            f"📝 <b>Описание:</b>\n"
            f"{seat.description or 'Описание отсутствует'}\n"
        )

        # Создаем клавиатуру для возврата
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к списку мест", callback_data="back_to_seats_list")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])

        # Если есть фото, отправляем с фото (нужно будет создать новое сообщение)
        if seat.photo and len(seat.photo) > 0:
            photo_file = BufferedInputFile(
                seat.photo,
                filename=f"seat_{seat.id}.jpg"
            )

            # Удаляем текущее сообщение со списком мест
            await callback.message.delete()

            # Отправляем новое сообщение с фото
            await callback.message.answer_photo(
                photo=photo_file,
                caption=info_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Если фото нет, редактируем текущее сообщение
            await callback.message.edit_text(
                text=info_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        await callback.answer()

    except ValueError:
        logger.error(f"Неверный формат callback_data: {callback.data}")
        await callback.answer("❌ Ошибка формата данных", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при показе информации о месте: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_seats_list")
async def back_to_seats_list(callback: types.CallbackQuery) -> None:
    """Возврат к списку всех мест"""
    seats = await get_all_seats()

    if not seats:
        await callback.message.edit_text("❌ В заведении пока нет мест")
        await callback.answer()
        return

    # Создаем клавиатуру со списком мест
    keyboard_buttons = []
    for seat in seats:
        button = InlineKeyboardButton(
            text=f"🪑 {seat.name}",
            callback_data=f"info_seat_{seat.id}"
        )
        keyboard_buttons.append([button])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    # Если текущее сообщение - фото, удаляем его и создаем новое со списком
    # Если текстовое - редактируем
    try:
        await callback.message.edit_text(
            "📍 Все места в заведении:\n\n"
            "Выберите место, чтобы увидеть информацию о нем:",
            reply_markup=keyboard
        )
    except:
        # Если не можем редактировать (например, это фото), удаляем и отправляем новое
        await callback.message.delete()
        await callback.message.answer(
            "📍 Все места в заведении:\n\n"
            "Выберите место, чтобы увидеть информацию о нем:",
            reply_markup=keyboard
        )

    await callback.answer()