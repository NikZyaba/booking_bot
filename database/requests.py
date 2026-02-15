from typing import Optional, List
from datetime import date

from pydantic import with_config
from sqlalchemy import select

from models import User, AsyncSessionFactory, Seat



# ------------------------ Работа с USER ------------------------ #
# Создаем запросы для создания пользователя
async def create_user(
        telegram_id:int,
        first_name:Optional[str],
        last_name:Optional[str],
        telephone_number:Optional[str],
        date_registry:Optional[date]
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
async def get_user_by_telegram_id(telegram_id:int) -> Optional[User]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

async def upate_user_phone(telegram_id:int, phone:str) -> Optional[User]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.telegram_id==telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.telephone_number = phone
            await session.commit()
            await session.refresh(user)
        return user
# -------------------------------------------------------------------#
# ------------------------ Работа с SEAT ------------------------ #
async def get_all_seats() -> List[Seat]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Seat))
        return list(result.scalars().all())
