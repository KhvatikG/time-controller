# TODO: Вынести api методы в smartomato_api

from aiogram import html

from loguru import logger

from tomato.core.api.zones import get_all_zones_of_organization, update_zone
from tomato.core.settings import SETTINGS


def set_waiting_time(organization_id: int, waiting_time: int, token: str) -> None:
    """
    Устанавливает время ожидания в зонах отдела с id department_id.
    :param waiting_time: Общее время ожидания в минутах для базовой зоны(Азов)
    :param organization_id: ID отдела
    :param token: Токен авторизации
    """
    try:
        zones = get_all_zones_of_organization(organization_id=organization_id, token=token)
    except Exception as e:
        raise Exception(f"Ошибка при получении зон: {e}")
    else:
        logger.info(f"Получены зоны: {zones}")
        try:
            for zone in zones:
                zone_delta = SETTINGS.DELTAS.get(zone.id, 0)
                if waiting_time <= zone.transportation_time:
                    err = (f"Вы указали слишком маленькое общее время, оно должно быть больше времени транспортировки.\
                         \nТекущее время транспортировки зоны {zone.name}: {zone.transportation_time}\n"
                           f" Вы указали: {waiting_time}")
                    logger.exception(err)
                    raise Exception(err)

                zone.delivery_time = waiting_time + zone_delta
                zone.cooking_time = zone.delivery_time - zone.transportation_time
                try:
                    update_zone(zone=zone, token=token)
                except Exception as e:
                    logger.exception(f"Ошибка при обновлении зоны {zone.name}: {e}")
                    raise Exception(f"Ошибка при обновлении зоны {zone.name}: {e}")

        except Exception as e:
            err = f"Непредвиденная ошибка в set_waiting_time {e}"
            logger.exception(err)
            raise Exception(err)


def get_current_waiting_time_string(organization_id: int, token: str) -> str:
    """
    Возвращает текущее время ожидания в зонах отдела с id department_id.
    :param organization_id: ID отдела
    :param token: Токен авторизации
    :return: Строку с текущим временем ожидания в минутах для всех зон организации
    """
    try:
        zones = get_all_zones_of_organization(organization_id=organization_id, token=token)
    except Exception as e:
        logger.exception(f"Ошибка при получении зон: {e}")
        raise Exception(f"Ошибка при получении зон: {e}")
    else:
        logger.info(f"Получены зоны: {zones}")
        try:
            waiting_times_string = "\n".join(f"{html.bold(zone.name)}:\n -Готовка: {zone.cooking_time} минут\n"
                                             f" -Транспортировка: {zone.transportation_time} минут \n"
                                             f" -Общее: {zone.delivery_time} минут\n" for zone in zones)

        except Exception as e:
            err = f"Непредвиденная ошибка в get_current_waiting_time {e}"
            logger.exception(err)
            raise Exception(err)

        else:
            return waiting_times_string
