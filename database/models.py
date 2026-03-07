# Для таблиц
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy import String, Date, Integer, LargeBinary, ForeignKey, func, Boolean
from datetime import datetime
# Для работы самой БД
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Для настроек (ТОКЕНЫ, ПАРОЛИ)
import os
from dotenv import load_dotenv

# Для функционала
from datetime import date

# Формат URL: postgresql+asyncpg://user:password@host:port/dbname
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(
    url=DATABASE_URL,
    echo=True  # Для отладки SQL запросов
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    def __str__(self):
        return f"ID = {self.id} created_at = {self.created_at} updated_at = {self.updated_at}"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False)
    first_name: Mapped[str] = mapped_column(String(25), nullable=True)
    last_name: Mapped[str] = mapped_column(String(25), nullable=True)
    telephone_number: Mapped[str] = mapped_column(String(13), unique=True, nullable=True)
    date_registry: Mapped[Date] = mapped_column(Date, nullable=True)

    # Связь между заказами
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class Seat(Base):
    __tablename__ = "seats"

    name: Mapped[str] = mapped_column(String(25), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=True)
    photo: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    photo_mime_type: Mapped[str] = mapped_column(String(50), default="image/jpeg", nullable=True)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Связь между заказами
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="seat", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", back_populates="orders")
    seat: Mapped["Seat"] = relationship("Seat", back_populates="orders")

    booking_date: Mapped[date] = mapped_column(Date, nullable=False)  # Дата бронирования
    booking_time: Mapped[str] = mapped_column(String(5), nullable=False)  # Время (ЧЧ:ММ)
    customer_name: Mapped[str] = mapped_column(String(50), nullable=True)  # Имя клиента
    qr_code: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)  # QR-код
    qr_code_path: Mapped[str] = mapped_column(String(255), nullable=True)  # Путь к QR-коду
