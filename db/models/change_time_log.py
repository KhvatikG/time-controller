from typing import Literal
from datetime import datetime

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy import String, BigInteger, func, DateTime

from .base import Base

ORDER_TYPE = Literal["Самовывоз", "Доставка"]


class ChangeTimeLog(Base):
    __tablename__ = 'change_time_log'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type_order: Mapped[ORDER_TYPE]
    department_id: Mapped[str] = mapped_column(String(16))
    time_minutes: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    def __repr__(self):
        return (f"ChangeTimeLog(id={self.id}, type_order={self.type_order},"
                f" department_id={self.department_id}, time_minutes={self.time_minutes}, created_at={self.created_at})")
