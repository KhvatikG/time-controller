import requests

from loguru import logger
from sqlalchemy import select

from bot_init import bot
from db.models.order_closer_chat import OrderCloserChat
from db.session import get_session
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS


async def get_all_chats() -> list[OrderCloserChat]:
    """
    Возвращает список чатов для отчета по закрытию заказов

    :return: список чатов для отчета по закрытию заказов
    """
    try:
        async with get_session() as session:
            result = await session.execute(select(OrderCloserChat))
            chats = result.scalars().all()
            if chats:
                return chats
            return []

    except Exception as e:
        err = f'Ошибка при получении чатов'
        logger.exception(err)
        raise Exception(err) from e


async def close_orders() -> None:
    """Закрывает заказы через сервис OrderCloser"""

    logger.info('Начинаю закрытие заказов...')

    try:
        logger.info('Получаю чаты...')
        # Получение списка чатов для отчета по закрытию заказов
        chats = await get_all_chats()
    except Exception as e:
        err = f'Ошибка при получении чатов: {e}'
        logger.exception(err)
        return

    logger.info('Чаты получены')

    try:
        logger.info('Получаю токен...')
        token = get_tomato_auth_token()
    except Exception as e:
        err = f'Ошибка при получении токена: {e}'
        logger.exception(err)
        return
    logger.info('Токен получен')

    logger.info('Отправляю запрос на закрытие заказов...')
    try:
        url = SETTINGS.ORDERS_CLOSER_API_URL + '/orders/close-confirmed'
        response = requests.post(url, json={'token': token})

        response.raise_for_status()
        logger.info('Заказы закрыты')

        response = response.json()
        for chat in chats:
            chat_id = chat.id
            await bot.send_message(chat_id, 'Заказы закрыты')
            await bot.send_message(chat_id, response.get('message'))

        logger.info('Рассылка отчетов по закрытию заказов завершена')

    except Exception as e:
        err = f'Ошибка при закрытии заказов: {e}'
        logger.exception(err)
