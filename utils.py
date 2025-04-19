from db.session import get_session
from db.models.change_time_log import ChangeTimeLog, ForOrderType
from tomato.core.settings import SETTINGS


async def fix_change_to_db_log(department_id, new_time_minutes, for_type_order):
    """
    Сохраняет в БД время изменения для отдела с id=department_id на new_time
    :param department_id: ID отдела на котором изменили время ожидания
    :param new_time_minutes: Время на которое изменили время ожидания
    :param for_type_order: Время для доставки или самовывоза
    """
    async with get_session() as session:
        change = ChangeTimeLog(department_id=str(department_id), time_minutes=new_time_minutes,
                               type_order=for_type_order)
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
