import enum
from datetime import datetime

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy import String, Enum, BigInteger, func

from .base import Base


class ForOrderType(enum.Enum):
    SELF = "Самовывоз"
    DELIVERY = "Доставка"


class ChangeTimeLog(Base):
    __tablename__ = 'change_time_log'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type_order: Mapped[ForOrderType] = mapped_column(Enum(ForOrderType))
    department_id: Mapped[str] = mapped_column(String(16))
    time_minutes: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())

    def __repr__(self):
        if self.type == ForOrderType.SELF:
            return f"Смена времени самовывоза: {self.datetime}"
        else:
            return f"Смена времени доставки: {self.datetime}"

