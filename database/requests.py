from typing import Optional, List
from datetime import date

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from database.models import User, AsyncSessionFactory, Seat, Order



# ------------------------ Работа с USER ------------------------ #
# Создаем запросы для создания пользователя
async def create_user(
        telegram_id: int,
        first_name: Optional[str],
        last_name: Optional[str],
        telephone_number: Optional[str],
        date_registry: Optional[date]
) -> User:
    try:
        async with AsyncSessionFactory() as session:
            user = User(telegram_id=telegram_id, first_name=first_name, last_name=last_name,
                        telephone_number=telephone_number, date_registry=date_registry)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    except Exception as e:
        print(f"Ошибка {e}")


# Поиск зарегистрированного пользователя в БД
async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


async def update_user_phone(telegram_id: int, phone: str) -> Optional[User]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.telephone_number = phone
            await session.commit()
            await session.refresh(user)
        return user

async def update_user_info(telegram_id: int, first_name: Optional[str] = None, last_name: Optional[str] = None) -> Optional[User]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))

        user = result.scalar_one_or_none()

        if user:
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name

        await session.commit()
        await session.refresh(user)
        # Пока импортируем внутри функции
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Информация пользователя {telegram_id} обновлена")

# --------------------------------------------------------------- #
# ------------------------ Работа с SEAT ------------------------ #
async def get_all_seats() -> List[Seat]:
    """Получаем все места из БД"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Seat))
        return list(result.scalars().all())


async def get_seat_by_id(seat_id: int) -> Optional[Seat]:
    """Получаем конкретное место из БД по его ID"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Seat).where(Seat.id == seat_id))
        return result.scalar_one_or_none()


async def update_seat_booking(seat_id: int, is_booked: bool) -> Optional[Seat]:
    """Ставим бронь на стол"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Seat).where(Seat.id == seat_id))
        seat = result.scalar_one_or_none()
        if seat:
            seat.is_booked = is_booked
            await session.commit()
            await session.refresh(seat)
        return seat


# ---------------------------------------------------------------- #
# ------------------------ Работа с ORDER ------------------------ #

async def create_order(
    user_id: int,
    seat_id: int,
    booking_date: Optional[date] = None,
    booking_time: Optional[str] = None,
    customer_name: Optional[str] = None,
    status: str = "pending"
) -> Optional[Order]:
    """Создаем заказ с полными данными"""
    try:
        async with AsyncSessionFactory() as session:
            order = Order(
                user_id=user_id,
                seat_id=seat_id,
                booking_date=booking_date,
                booking_time=booking_time,
                customer_name=customer_name,
                status=status
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
            return order
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка при создании заказа: {e}", exc_info=True)
        return None


async def get_user_orders(user_id: int) -> List[Order]:
    """Получаем все заказы пользователя по его ID"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Order).where(Order.user_id == user_id))
        return list(result.scalars().all())


async def get_order_by_id(order_id: int) -> Optional[Order]:
    """Получаем определенный заказ по его уникальному ID"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()


async def update_order_status(order_id: int, status: str) -> Optional[Order]:
    """Обновляем статус заказа"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = status
            await session.commit()
            await session.refresh(order)
        return order


# --------------------------------------------------------------- #
# ----------------- Комбинированные запросы --------------------- #

async def get_seat_with_orders(seat_id: int) -> Optional[Seat]:
    """Получаем заказы на выбранный стол"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Seat).where(Seat.id == seat_id).options(selectinload(Seat.orders)))
        return result.scalar_one_or_none()


async def get_user_with_orders(telegram_id: int) -> Optional[User]:
    """Получаем заказы выбранного пользователя"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id).options(selectinload(User.orders)))
        return result.scalar_one_or_none()

async def get_available_seats() -> List[Seat]:
    """Получаем все свободные места"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Seat).where(Seat.is_booked == False))
        return list(result.scalars().all())


async def get_booked_times_for_seat(seat_id: int, booking_date: date) -> List[str]:
    """
    Получает все забронированные времена для конкретного места на указанную дату

    Args:
        seat_id: ID места
        booking_date: дата бронирования

    Returns:
        List[str]: список забронированных времен в формате "ЧЧ:ММ"
    """
    async with AsyncSessionFactory() as session:
        # Получаем все заказы для этого места на указанную дату
        result = await session.execute(
            select(Order.booking_time)
            .where(Order.seat_id == seat_id)
            .where(Order.booking_date == booking_date)
            .where(Order.status.in_(["pending", "confirmed"]))  # Только активные брони
        )
        # Возвращаем список времен
        return [time for (time,) in result.all()]


async def is_seat_booked(seat_id:int) -> bool:
    """Проверяем, забронировано-ли место"""
    seat = await get_seat_by_id(seat_id)
    return seat.is_booked if seat else False


async def delete_order(order_id: int) -> bool:
    """Удаляет заказ по ID. Если успешно, то возвращает True"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            await session.delete(order)
            await session.commit()
            return True
        return False

async def get_user_active_orders(user_id:int) -> List[Order]:
    """Получает все активные заказы пользователей"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Order).where(Order.user_id == user_id, Order.status.in_(["pending", "confirmed"])))
        return list(result.scalars().all())


