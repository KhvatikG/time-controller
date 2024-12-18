import asyncio
import requests

from loguru import logger

from bot_init import bot
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS


async def close_orders() -> None:
    """Закрывает заказы через сервис OrderCloser"""
    logger.info('Установка дефолтного времени...')

    try:
        token = get_tomato_auth_token()
    except Exception as e:
        err = f'Ошибка при получении токена: {e}'
        logger.exception(err)

        await bot.send_message(SETTINGS.MAIN_CHAT_ID, err)
        return
    logger.info('Токен получен')
    logger.info('Закрытие заказов...')
    try:
        url = SETTINGS.ORDER_CLOSER_API_URL
        response = requests.post(url, json={'token': token})

        response.raise_for_status()
        logger.info('Заказы закрыты')

        response = response.json()
        await bot.send_message(SETTINGS.ORDER_CLOSER_CHAT_ID, 'Заказы закрыты')
        await bot.send_message(SETTINGS.ORDER_CLOSER_CHAT_ID, response.get('message'))

    except Exception as e:
        err = f'Ошибка при закрытии заказов: {e}'
        logger.exception(err)
        await bot.send_message(SETTINGS.ORDER_CLOSER_CHAT_ID, err)

