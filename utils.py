from db.session import get_session
from db.models.change_time_log import ChangeTimeLog
from tomato.core.settings import SETTINGS
from sqlalchemy import text
import pandas as pd


async def fix_change_to_db_log(department_id, new_time_minutes, order_type):
    """
    Сохраняет в БД время изменения для отдела с id=department_id на new_time
    :param department_id: ID отдела на котором изменили время ожидания
    :param new_time_minutes: Время на которое изменили время ожидания
    :param order_type: Тип заказа для которого изменили время
    """
    async with get_session() as session:
        change = ChangeTimeLog(department_id=str(department_id), time_minutes=new_time_minutes,
                               type_order=order_type)
        session.add(change)
        await session.commit()


def get_organization_id_per_name(organization_name: str) -> int:
    """
    Возвращает id организации по ее названию
    :param organization_name: Имя организации (В смартомато)
    """
    if organization_id := SETTINGS.NAME_TO_ORGANIZATION_ID.get(organization_name):
        return organization_id
    else:
        raise KeyError(f'Не могу найти id организации по названию {organization_name}')


def pandas_time_log_query(session):
    conn = session.connection()
    raw_sql = """
    SELECT 
        (created_at AT TIME ZONE 'Europe/Moscow')::timestamp AS created_at,
        department_id,
        time_minutes,
        id,
        type_order
    FROM change_time_log
    """

    return pd.read_sql(text(raw_sql), conn, index_col='id')


async def get_change_time_log_df():
    """Получение лога изменения времени на сервере в Pandas DataFrame"""

    async with get_session() as session:
        df = await session.run_sync(pandas_time_log_query)

    return df
