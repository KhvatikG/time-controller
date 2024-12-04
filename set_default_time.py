import asyncio

from loguru import logger

from bot_init import bot
from time_control import set_waiting_time, get_current_waiting_time_string
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS


logger.add('log/set_default_time.log', rotation='10 MB', encoding='utf-8')

async def set_default_time() -> None:
    """Устанавливает время ожидания по умолчанию для всех организаций."""

    try:
        token = get_tomato_auth_token()
    except Exception as e:
        err = f'Ошибка при получении токена: {e}'
        logger.exception(err)

        await bot.send_message(SETTINGS.MAIN_CHAT_ID, err)
        return

    try:
        # Получаем дефолтное время для зоны Азов во всех организациях(сейчас оно одинаковое
        default_time = SETTINGS.DEFAULT_ZONES_TIMES["AZOV_ALL_ORGANIZATIONS"]
        # Перебираем id тредов и id организаций
        for thread_id, organization_id in SETTINGS.CHAT_ID_TO_ORGANIZATION_ID.items():
            # Устанавливаем дефолтное время
            set_waiting_time(organization_id, default_time, token)

            await bot.send_message(
                chat_id=SETTINGS.MAIN_CHAT_ID, text=f'Дефолтное время установлено', message_thread_id=thread_id
            )
            time_string = get_current_waiting_time_string(organization_id, token)
            await bot.send_message(
                chat_id=SETTINGS.MAIN_CHAT_ID, text=time_string, message_thread_id=thread_id
            )
    except Exception as e:
        err = f'Ошибка при установке дефолтного времени: {e}'
        logger.exception(err)
        await bot.send_message(SETTINGS.MAIN_CHAT_ID, err)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_default_time())
