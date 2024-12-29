from datetime import datetime

from sqlalchemy import func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class OrderCloserChat(Base):
    """
    Модель чата для отчетов о закрытии заказов
    """
    __tablename__ = 'order_closer_chats'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    create_user_id: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())

    def __repr__(self):
        return f'<OrderCloserChat {self.id}>'
