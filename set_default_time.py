import asyncio

from loguru import logger

from bot_init import bot
from tomato.time_control import set_waiting_time, get_current_waiting_time_string
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS


async def set_default_time() -> None:
    """Устанавливает время ожидания по умолчанию для всех организаций."""
    logger.info('Установка дефолтного времени...')
    
    try:
        token = get_tomato_auth_token()
    except Exception as e:
        err = f'Ошибка при получении токена: {e}'
        logger.exception(err)

        await bot.send_message(SETTINGS.MAIN_CHAT_ID, err)
        return

    try:
        # Получаем дефолтное время для доставки в зонах Азов во всех организациях(сейчас оно одинаковое)
        default_delivery_time = SETTINGS.DEFAULT_ZONES_TIMES["AZOV_ALL_ORGANIZATIONS"]
        # Аналогично время самовывоза
        default_self_delivery_time = SETTINGS.DEFAULT_ZONES_TIMES["SELF-DELIVERY_ALL_ORGANIZATIONS"]

        # Перебираем id тредов и id организаций
        for thread_id, organization_id in SETTINGS.CHAT_ID_TO_ORGANIZATION_ID.items():
            # Устанавливаем дефолтное время для зон доставки
            await set_waiting_time(organization_id, default_delivery_time, token)
            # Устанавливаем дефолтное время для самовывоза
            await set_waiting_time(
                organization_id, default_self_delivery_time, token, for_self_delivery=True
            )
            # Поучаем строку с информацией о текущем времени ожидания во всех зонах включая самовывоз
            time_string = get_current_waiting_time_string(organization_id, token, for_all_zones=True)

            await bot.send_message(
                chat_id=SETTINGS.MAIN_CHAT_ID, text=f'Дефолтное время установлено', message_thread_id=thread_id
            )

            await bot.send_message(
                chat_id=SETTINGS.MAIN_CHAT_ID, text=time_string, message_thread_id=thread_id
            )

            logger.info("Дефолтное время установлено\n")

    except Exception as e:
        err = f'Ошибка при установке дефолтного времени: {e}'
        logger.exception(err)
        await bot.send_message(SETTINGS.MAIN_CHAT_ID, err)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_default_time())
