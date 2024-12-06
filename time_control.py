# TODO: Вынести api методы в smartomato_api

from aiogram import html
import requests
import json

from loguru import logger

from models.zone import Zone
from tomato.core.settings import SETTINGS


def get_all_zones_of_organization(organization_id: int, token: str) -> list[Zone]:
    """
    Возвращает все зоны организации с id organization_id.

    :param organization_id: id организации, зоны которой необходимо получить.
    :param token: Токен авторизации.
    :return: Возвращает список экземпляров зон.
    """

    url = f'{SETTINGS.BASE_API_URL}/delivery_zones'
    payload = {"token": token, "organization_id": organization_id}
    response = requests.get(url, params=payload)
    code = response.status_code

    logger.info(f"\nПолучение всех зон для {organization_id=}, статус ответа - {code}")

    zones_list: list[Zone] = []

    if code == 200:
        request_data = json.loads(response.text)
        if zones := request_data.get("delivery_zones"):
            logger.info("Зоны получены - delivery_zones в ответе сервера не пуст")
            for zone in zones:
                try:
                    logger.info(f'Получаем инстанс зоны {zone.get("name")}')
                    zone_instance = Zone(**zone)
                    if zone_instance.name != "Пункт самовывоза":
                        zones_list.append(zone_instance)

                except Exception:
                    logger.exception(f"Не удалось создать экземпляр зоны {zone}")
                    raise
        else:
            error = f"Некорректный ответ от сервера смартомато: \n{request_data}"
            logger.exception(error)
            raise Exception(error)

    else:
        error = f"Не удалось получить список зон {response.status_code=}\n{response.text}"
        logger.exception(error)
        raise Exception(error)

    return zones_list


def update_zone(zone: Zone, token):
    """
    :param token: Токен авторизации
    :param zone: Экземпляр зоны с новым временем для отправки
    :return:
    """
    url = f'{SETTINGS.BASE_API_URL}/delivery_zones/{zone.id}?token={token}'
    payload = zone.json()
    headers = {
        'Content-Type': 'application/json'
    }
    logger.info(f"Начинаю изменение зоны {zone.name}")
    response = requests.request("PUT", url, headers=headers, data=payload)

    code = response.status_code
    text = response.text

    if code == 204:
        logger.info(f"Зона {zone.name} изменена")
        return True
    else:
        logger.exception(f"Не удалось изменить зону {zone.name}\n  {code=}\n  {text}")
        raise Exception(f"Ошибка: \n{code=}\n{text}")


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
