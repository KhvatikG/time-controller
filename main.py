# TODO: Добавить к каждой зоне в БД ее дефолтное время, для сброса после смены
# TODO: И ее дельту относительно Азова
from functools import wraps

# TODO: Добавить скедулер который с настраиваемым менеджером промежутком будет уточнять
# TODO: Актуально ли сейчас время ожидания + инфу о времени и присылать клавиатуру(ДА/Нет)
# TODO: Если Да то ок, если нет то - Укажите актуальное время

from aiogram import Dispatcher, html, Bot, types, BaseMiddleware, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, Update
from dotenv import load_dotenv

import asyncio
from loguru import logger
from os import getenv

from time_control import set_waiting_time, get_current_waiting_time_string
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS

logger.add("main.log")


def get_organization_id(message_thread_id):
    """
    Возвращает идентификатор организации по номеру чата.
    :param message_thread_id: id чата
    :return:
    """

    KRUG = 2
    KULT = 3
    GONZO = 4

    CHAT_ID_TO_ORGANIZATION_ID = {
        KRUG: 44166,
        KULT: 45128,
        GONZO: 45622
    }

    if message_thread_id in CHAT_ID_TO_ORGANIZATION_ID:
        return CHAT_ID_TO_ORGANIZATION_ID[message_thread_id]
    else:
        return None


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        logger.info(f"\nReceived {event}\n")
        return await handler(event, data)


def authorized_only(handler):
    @wraps(handler)
    async def wrapped_handler(message: types.Message, *args, **kwargs):
        if message.from_user.id in SETTINGS.AUTHORIZED_USERS:
            return await handler(message, *args, **kwargs)
        else:
            return await message.reply("У вас нет доступа к этой операции.")

    return wrapped_handler


dp = Dispatcher()
dp.update.middleware(LoggingMiddleware())


@dp.message(CommandStart())
@authorized_only
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f'''
    Привет, {html.bold(message.from_user.full_name)}!\n Это прототип, сервис на стадии разработки.\n
    Введи общее время ожидания для зоны Азов, и я вычислю и установлю соответствующие значения во всех зонах.
    ''')


@dp.message()
@authorized_only
async def echo_handler(message: Message) -> None:
    """

    """
    try:
        organization_id = get_organization_id(message.message_thread_id)
        if organization_id is None:
            return
    except Exception as e:
        error_message = f"Что-то пошло не так! Ошибка: \n❗{html.bold("ОШИБКА:")}❗\n {e}"
        await message.answer(error_message)
        logger.error(error_message)
        return

    try:
        time = int(message.text)
        token = get_tomato_auth_token()['token']
        set_waiting_time(organization_id, time, token)
        time_string = get_current_waiting_time_string(organization_id, token)
        await message.answer(time_string)
    except Exception as e:
        logger.error(e)
        # But not all the types is supported to be copied so need to handle it
        await message.answer(f"Что-то пошло не так, пришли время в минутах в числовом виде!\n"
                             f"❗{html.bold("ОШИБКА:")}❗\n {e}")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=SETTINGS.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
