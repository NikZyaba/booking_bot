from aiogram.types import CallbackQuery
from datetime import date
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
import qrcode
from io import BytesIO
import logging
from keyboards.main_menu import get_main_menu
from database.requests import create_order, update_seat_booking
from database.models import AsyncSessionFactory, Order
from sqlalchemy import update

logger = logging.getLogger(__name__)


async def generate_qr_code(data: str) -> bytes:
    """
    Генерирует QR-код из данных

    Args:
        data: Данные для кодирования

    Returns:
        bytes: QR-код в формате PNG
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=5,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

    except Exception as e:
        logger.error(f"Ошибка при генерации QR-кода: {e}")
        return None


def format_date_ru(date_obj: date) -> str:
    """Форматирует дату в русский формат"""
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    return f"{date_obj.day} {months[date_obj.month]} {date_obj.year}"


async def create_booking_order(
        callback: CallbackQuery,
        state: FSMContext,
        user,
        seat_id: int,
        seat_name: str,
        selected_date: date,
        selected_time: str
) -> bool:
    """
    Создание заказа с QR-кодом

    Returns:
        bool: True если заказ успешно создан, False в противном случае
    """
    try:
        # Формируем имя клиента
        customer_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if not customer_name:
            customer_name = f"Гость_{user.telegram_id}"

        # Создаем заказ сразу со всеми данными
        order = await create_order(
            user_id=user.id,
            seat_id=seat_id,
            booking_date=selected_date,
            booking_time=selected_time,
            customer_name=customer_name,
            status="confirmed"
        )

        if not order:
            raise Exception("Не удалось создать заказ в базе данных")

        # Обновляем статус места
        await update_seat_booking(seat_id, is_booked=True)

        # Генерируем QR-код с данными заказа
        qr_data = (
            f"Заказ #{order.id}\n"
            f"Место: {seat_name}\n"
            f"Дата: {format_date_ru(selected_date)}\n"
            f"Время: {selected_time}\n"
            f"Гость: {customer_name}"
        )

        qr_bytes = await generate_qr_code(qr_data)

        if not qr_bytes:
            logger.warning(f"QR-код для заказа #{order.id} не сгенерирован, но заказ создан")

        # Сохраняем QR-код в заказе, если он сгенерирован
        if qr_bytes:
            async with AsyncSessionFactory() as session:
                stmt = (
                    update(Order)
                    .where(Order.id == order.id)
                    .values(
                        qr_code=qr_bytes,
                        qr_code_path=f"orders/qr_{order.id}.png"
                    )
                )
                await session.execute(stmt)
                await session.commit()

        logger.info(
            f"✅ Создан заказ #{order.id}: "
            f"пользователь {user.telegram_id}, "
            f"место {seat_name}, "
            f"{selected_date} {selected_time}"
        )

        # Формируем успешное сообщение БЕЗ форматирования Markdown
        success_text = (
            f"✅ Бронирование успешно подтверждено!\n\n"
            f"📋 Детали заказа:\n"
            f"└─ Номер заказа: #{order.id}\n"
            f"└─ Место: {seat_name}\n"
            f"└─ Дата: {selected_date.strftime('%d.%m.%Y')}\n"
            f"└─ Время: {selected_time}\n"
            f"└─ Гость: {customer_name}\n\n"
            f"🎫 Ваш QR-код для входа:\n"
            f"(сохраните его или покажите на входе)\n\n"
            f"⚠️ Важно:\n"
            f"• Приходите за 5-10 минут до брони\n"
            f"• Опоздание более 15 минут может привести к отмене брони\n"
            f"• Для отмены брони используйте команду /my_orders"
        )

        # Отправляем QR-код, если он сгенерирован
        if qr_bytes:
            qr_file = BufferedInputFile(qr_bytes, filename=f"qr_{order.id}.png")

            # Удаляем предыдущее сообщение
            try:
                await callback.message.delete()
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение: {e}")

            # Отправляем фото без parse_mode
            await callback.message.answer_photo(
                photo=qr_file,
                caption=success_text
            )
        else:
            # Если QR-код не сгенерирован, отправляем только текст
            try:
                await callback.message.delete()
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение: {e}")

            await callback.message.answer(success_text)

        # Отправляем кнопку главного меню
        await callback.message.answer(
            "Выберите дальнейшее действие:",
            reply_markup=get_main_menu()
        )

        # Очищаем состояние
        await state.clear()

        return True

    except Exception as e:
        logger.error(f"Ошибка при создании заказа: {e}", exc_info=True)

        # Отправляем сообщение об ошибке пользователю
        error_text = (
            "❌ Произошла ошибка при создании заказа.\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )

        try:
            # Пробуем отредактировать текущее сообщение
            await callback.message.edit_text(error_text)
        except Exception:
            try:
                # Если не можем редактировать, отправляем новое
                await callback.message.answer(error_text)
            except Exception:
                pass

        # Отправляем главное меню
        try:
            await callback.message.answer(
                "🤖 Главное меню\n\nВыберите действие:",
                reply_markup=get_main_menu()
            )
        except Exception:
            pass

        await state.clear()
        return False