# TODO: Декомпозировать код модуля
# TODO: Создать свои исключения, ловить конкретные исключения

from aiogram import html

from loguru import logger

from models.zone import ZonesList, Zone
from tomato.core.api.zones import get_all_zones_of_organization, update_zone
from tomato.core.settings import SETTINGS


def set_waiting_time(organization_id: int, waiting_time: int, token: str, for_self_delivery: bool = False) -> None:
    """
    Устанавливает время ожидания в зонах отдела с id department_id.

    :param for_self_delivery: Если True, то устанавливается время ожидания только для самовывоза
    :param waiting_time: Общее время ожидания в минутах для базовой зоны(Азов)
    :param organization_id: ID отдела
    :param token: Токен авторизации
    """
    try:
        zones: ZonesList = get_all_zones_of_organization(organization_id=organization_id, token=token)
        logger.info(",".join(f"Получены зоны: {zone.name}" for zone in zones))
        # Если нужно установить время для зон кроме самовывоза
        if not for_self_delivery:
            # Получаем список зон кроме самовывоза
            delivery_zones: list[Zone] = zones.get_delivery_zones()

            for delivery_zone in delivery_zones:
                # Получаем разницу времени между базовой зоной и зоной в текущей итерации цикла
                zone_delta: int = SETTINGS.DELTAS.get(delivery_zone.id, 0)

                if waiting_time <= delivery_zone.transportation_time:
                    err: str = (
                        f"Вы указали слишком маленькое общее время, оно должно быть больше времени транспортировки."
                        f"Текущее время транспортировки зоны {delivery_zone.name}: {delivery_zone.transportation_time}\n"
                        f" Вы указали: {waiting_time}"
                    )
                    logger.error(err)
                    raise Exception(err)

                delivery_zone.delivery_time = waiting_time + zone_delta
                delivery_zone.cooking_time = delivery_zone.delivery_time - delivery_zone.transportation_time

                # Отправляем обновление зоны на сервер
                update_zone(zone=delivery_zone, token=token)

        else:  # Если нужно установить время для самовывоза
            self_delivery_zone: Zone = zones.get_self_delivery_zone()

            # Для самовывоза общее время доставки и время готовки равны
            self_delivery_zone.delivery_time = waiting_time
            self_delivery_zone.cooking_time = waiting_time

            # Отправляем обновление зоны на сервер
            update_zone(zone=self_delivery_zone, token=token)

    except Exception as e:
        err = f"Ошибка в set_waiting_time: {e}"
        logger.exception(err)
        raise Exception(err) from e


def get_current_waiting_time_string(
        organization_id: int, token: str, for_self_delivery: bool = False, for_all_zones: bool = False
) -> str:
    """
    Возвращает текущее время ожидания в зонах отдела с id organization_id.

    :param for_all_zones: Если True, то возвращает время ожидания для всех зон организации игнорируя for_self_delivery
    :param for_self_delivery: Если True, то возвращает время ожидания только для самовывоза
    :param organization_id: ID отдела
    :param token: Токен авторизации
    :return: Строку с текущим временем ожидания в минутах для всех зон организации кроме самовывоза,
     если for_self_delivery == True, то только для самовывоза, если for_all_zones == True, то для всех зон организации.
    """
    try:
        zones: ZonesList = get_all_zones_of_organization(organization_id=organization_id, token=token)
    except Exception as e:
        logger.exception(f"Ошибка при получении зон")
        raise Exception(f"Ошибка при получении зон: {e}") from e

    logger.info(",".join(f"Получены зоны: {zone.name}" for zone in zones))
    try:
        if for_all_zones:
            delivery_zones: list[Zone] = zones.get_delivery_zones()
            self_delivery_zone: Zone = zones.get_self_delivery_zone()
            waiting_times_string: str = "\n".join(f"{html.bold(zone.name)}:\n -Готовка: {zone.cooking_time} минут\n"
                                                  f" -Транспортировка: {zone.transportation_time} минут \n"
                                                  f" -Общее: {zone.delivery_time} минут\n\n" for zone in delivery_zones)
            waiting_times_string += f"{html.bold(self_delivery_zone.name)}: {self_delivery_zone.delivery_time} минут\n"

        elif for_self_delivery:  # Если нужно получить время для самовывоза
            self_delivery_zone: Zone = zones.get_self_delivery_zone()
            waiting_times_string: str = f"{html.bold(self_delivery_zone.name)}: {self_delivery_zone.delivery_time} минут\n"

        else:  # Если нужно получить время для всех зон
            delivery_zones: list[Zone] = zones.get_delivery_zones()
            waiting_times_string: str = "\n".join(f"{html.bold(zone.name)}:\n -Готовка: {zone.cooking_time} минут\n"
                                                  f" -Транспортировка: {zone.transportation_time} минут \n"
                                                  f" -Общее: {zone.delivery_time} минут\n" for zone in delivery_zones)

    except Exception as e:
        err = f"Непредвиденная ошибка в get_current_waiting_time {e}"
        logger.exception(err)
        raise Exception(err) from e

    else:
        return waiting_times_string
