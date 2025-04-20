from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.change_time_log import ChangeTimeLog


def process_logs(logs: List, start_date: datetime) -> Dict:
    """Обрабатывает логи для одного типа заказа и вычисляет метрики."""
    if not logs:
        return {
            'max_time': None,
            'max_periods': [],
            'average_time': None
        }

    end_of_day = start_date + timedelta(days=1) - timedelta(microseconds=1)
    intervals = []

    # Создаем интервалы между изменениями
    for i in range(len(logs)):
        current = logs[i]
        next_created = logs[i + 1].created_at if i < len(logs) - 1 else end_of_day
        intervals.append({
            'start': current.created_at,
            'end': next_created,
            'time': current.time_minutes
        })

    # Вычисляем максимальное время
    max_time = max(log.time_minutes for log in logs)

    # Находим интервалы с максимальным временем
    max_intervals = [interval for interval in intervals if interval['time'] == max_time]
    max_periods = [{'start': interval['start'], 'end': interval['end']} for interval in max_intervals]

    # Рассчитываем средневзвешенное
    total_weighted = 0.0
    total_duration = 0.0

    for interval in intervals:
        duration = (interval['end'] - interval['start']).total_seconds() / 60  # в минутах
        total_weighted += interval['time'] * duration
        total_duration += duration

    average = round(total_weighted / total_duration, 2) if total_duration else None

    return {
        'max_time': max_time,
        'max_periods': max_periods,
        'average_time': average
    }


async def get_daily_time_report(
        session: AsyncSession,
        department_id: str,
        target_date: datetime
) -> Dict:
    """
    Возвращает отчет по времени доставки и самовывоза за указанный день.

    Args:
        session: Асинхронная сессия SQLAlchemy
        department_id: Идентификатор подразделения
        target_date: Дата для формирования отчета

    Returns:
        Словарь с данными для отчета
        {
            "Доставка": {
                "max_time": 60,
                "max_periods": [
                    {"start": datetime(2025,4,17,19,46,9), "end": datetime(2025,4,17,19,46,13)},
                    ...
                ],
                "average_time": 42.5
            },
            "Самовывоз": {
                "max_time": None,
                "max_periods": [],
                "average_time": None
            }
        }
    """
    start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)

    # Получаем логи за день
    stmt = (
        select(ChangeTimeLog)
        .where(
            and_(
                ChangeTimeLog.department_id == str(department_id),
                ChangeTimeLog.created_at >= start_date,
                ChangeTimeLog.created_at < end_date
            )
        )
        .order_by(ChangeTimeLog.created_at)
    )

    result = await session.execute(stmt)
    logs = result.scalars().all()

    # Разделяем логи по типам заказов
    delivery_logs = [log for log in logs if log.type_order == "Доставка"]
    self_logs = [log for log in logs if log.type_order == "Самовывоз"]

    # Обрабатываем данные
    delivery_data = process_logs(delivery_logs, start_date)
    self_data = process_logs(self_logs, start_date)

    # Формируем итоговую структуру
    return {
        "Доставка": {
            'max_time': delivery_data['max_time'],
            'max_periods': delivery_data['max_periods'],
            'average_time': delivery_data['average_time']
        },
        "Самовывоз": {
            'max_time': self_data['max_time'],
            'max_periods': self_data['max_periods'],
            'average_time': self_data['average_time']
        }
    }
