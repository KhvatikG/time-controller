from functools import wraps

from aiogram import types
from loguru import logger
from sqlalchemy import select

from db.models.user import User
from db.session import get_session


def authorized_only(handler):
    """
    Декоратор для проверки авторизации пользователя
    """
    @wraps(handler)
    async def wrapped_handler(message: types.Message, *args, **kwargs):
        logger.debug(f"Начинаем проверку авторизации...")
        # Пытаемся получить пользователя из БД
        async with get_session() as session:
            result = await session.execute(select(User).where(User.id == message.from_user.id))
            user = result.scalars().one_or_none()

        if user:
            logger.debug(f"Пользователь авторизован: {user}")
            return await handler(message, *args, **kwargs)

        else:
            return await message.reply("У вас нет доступа к этой операции.")

    return wrapped_handler
