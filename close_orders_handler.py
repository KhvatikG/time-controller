from aiogram import Router
from aiogram.types import Message
from loguru import logger
from aiogram import F
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.models.order_closer_chat import OrderCloserChat
from db.session import get_session
from tomato.core.settings import SETTINGS
from reports import send_departments_report

order_closer_router = Router()


@order_closer_router.message(F.text.startswith('add_this_chat'))
async def register_chat_for_order_closer(message: Message) -> None:
    """
    Регистрирует новый чат для отчетов по закрытию заказов
    """
    logger.info(f"Добавление чата для отчетов по закрытию заказов...")
    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        logger.warning(f"Пользователь {message.from_user.id} не является супер-админом")
        await message.answer('У вас нет прав на выполнение данной команды')
        return

    logger.info(f"Пользователь инициировавший добавление - {message.from_user.id} является супер-админом")

    try:
        async with get_session() as session:
            logger.info("Получаем чат из БД...")
            result = await session.execute(select(OrderCloserChat).where(OrderCloserChat.id == message.chat.id))
            chat = result.scalar_one_or_none()
            if chat:
                logger.info(f'Чат с таким id уже зарегистрирован')
                await message.answer(f'Чат с таким id уже зарегистрирован')
                return

            logger.info(f'Регистрируем чат в БД')

            chat = OrderCloserChat(id=message.chat.id, create_user_id=message.from_user.id)
            session.add(chat)
            await session.commit()
            await message.answer(f'Чат успешно зарегистрирован')
            logger.info(f'Чат успешно зарегистрирован')

    except SQLAlchemyError as e:
        await message.answer(f'Ошибка SQLAlchemy при регистрации чата: {e}')
        logger.exception("Ошибка SQLAlchemy при регистрации чата")

    except Exception as e:
        await message.answer(f'Ошибка при регистрации чата: {e}')
        logger.exception("Ошибка при регистрации чата")


@order_closer_router.message(F.text.startswith('del_this_chat'))
async def delete_chat(message: Message) -> None:
    """
    Удаляет чат из списка чатов для отчетов по закрытию заказов
    """
    logger.info(f'Удаление чата {message.chat.id}')

    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        logger.warning(f"Пользователь {message.from_user.id} не является супер-админом")
        await message.answer('У вас нет прав на выполнение данной команды')
        return
    logger.info(f'Пользователь инициировавший удаление авторизован: id:'
                f' {message.from_user.id} username: {message.from_user.username}')

    try:
        logger.info(f'Получаем чат из БД')
        async with get_session() as session:
            result = await session.execute(select(OrderCloserChat).where(OrderCloserChat.id == message.chat.id))
            chat = result.scalar_one_or_none()
            if not chat:
                logger.info(f"Чат с таким id не зарегистрирован")
                await message.answer(f'Чат с таким id не зарегистрирован')
                return

            logger.info(f'Удаляем чат из БД')

            session.delete(chat)
            await session.commit()
            await message.answer(f'Чат успешно удален')
            logger.info(f'Чат успешно удален')

    except SQLAlchemyError as e:
        await message.answer(f'Ошибка SQLAlchemy при удалении чата: {e}')
        logger.exception("Ошибка SQLAlchemy при удалении чата")

    except Exception as e:
        await message.answer(f'Ошибка при удалении чата: {e}')
        logger.exception("Ошибка при удалении чата")


@order_closer_router.message(F.text.startswith('get_chats'))
async def get_chats(message: Message) -> None:
    """
    Возвращает список чатов для отчетов по закрытию заказов

    :param message:
    :return:
    """
    logger.info(f'Получение списка чатов')

    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        logger.warning(f"Пользователь {message.from_user.id} не является супер-админом")
        await message.answer('У вас нет прав на выполнение данной команды')
        return

    logger.info(f'Пользователь инициировавший запрос списка чатов авторизован: id:{message.from_user.id}')

    try:
        logger.info(f'Получаем список чатов из БД')
        async with get_session() as session:
            result = await session.execute(select(OrderCloserChat))
            chats = result.scalars().all()
            if not chats:
                logger.info(f"Список чатов пуст")
                await message.answer(f'Список чатов пуст')
                return
            logger.info(f'Список чатов получен')
            for chat in chats:
                logger.info(f'Чат: {chat.id}')
                await message.answer(f'Чат: {chat.id}')
            logger.info(f'Список чатов отправлен')
    except SQLAlchemyError as e:
        await message.answer(f'Ошибка SQLAlchemy при получении списка чатов: {e}')
        logger.exception("Ошибка SQLAlchemy при получении списка чатов")
    except Exception as e:
        await message.answer(f'Ошибка при получении списка чатов: {e}')
        logger.exception("Ошибка при получении списка чатов")


@order_closer_router.message(F.text.startswith('del_chat'))
async def delete_chat_by_id(message: Message) -> None:
    """
    Удаляет чат id которого у казан в комманде
    :param message:
    :return:
    """
    logger.info(f'Удаление чата по id')

    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        logger.warning(f"Пользователь {message.from_user.id} не является супер-админом")
        await message.answer('У вас нет прав на выполнение данной команды')
        return

    logger.info(f'Пользователь инициировавший удаление авторизован: id: {message.from_user.id}')

    logger.info(f'Получаем чат из БД')
    try:
        chat_id = int(message.text.split()[1])
        async with get_session() as session:
            result = await session.execute(select(OrderCloserChat).where(OrderCloserChat.id == chat_id))
            chat = result.scalar_one_or_none()
            if not chat:
                logger.info(f"Чат с таким id не зарегистрирован")
                await message.answer(f'Чат с таким id не зарегистрирован')
                return

            logger.info(f'Получен чат из БД {chat}, id: {chat.id}, create_user_id: {chat.create_user_id}')
            logger.info(f'Удаляем чат из БД')
            await session.delete(chat)
            await session.commit()
            await message.answer(f'Чат успешно удален')
            logger.info(f'Чат успешно удален')
    except SQLAlchemyError as e:
        await message.answer(f'Ошибка SQLAlchemy при удалении чата: {e}')
        logger.exception("Ошибка SQLAlchemy при удалении чата")
    except Exception as e:
        await message.answer(f'Ошибка при удалении чата: {e}')
        logger.exception("Ошибка при удалении чата")


@order_closer_router.message(F.text.startswith('get_report_from'))
async def get_report_from(message: Message) -> None:
    """
    Отправляет отчет по закрытию заказов за указанный период времени
    :param message:
    :return:
    """
    logger.info(f'Получение отчета по закрытию заказов')

    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        logger.warning(f"Пользователь {message.from_user.id} не является супер-админом")
        await message.answer('У вас нет прав на выполнение данной команды')
        return

    logger.info(f'Пользователь инициировавший запрос отчета авторизован: id:{message.from_user.id}')

    date_from = message.text.split()[1]
    chat_id = message.chat.id
    async with get_session() as session:
        logger.info(f'Получаем чат из БД')
        result = await session.execute(select(OrderCloserChat).where(OrderCloserChat.id == chat_id))
        chat = result.scalars().one_or_none()
        if not chat:
            logger.info(f"Чат не найден")
            await message.answer(f'Чат не найден')

        logger.info(f'Получен чат из БД: id: {chat.id}, create_user_id: {chat.create_user_id}')

    logger.info(f'Отправляем отчет по закрытию заказов...')
    await send_departments_report(date_from, [chat])
    logger.info(f'Отчет по закрытию заказов отправлен')
