# TODO: Добавить скедулер который с настраиваемым менеджером промежутком будет уточнять
# TODO: Актуально ли сейчас время ожидания + инфу о времени и присылать клавиатуру(ДА/Нет)
# TODO: Если Да то ок, если нет то - Укажите актуальное время

from functools import wraps
import asyncio

from aiogram import Dispatcher, html, types, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.types import Message, Update
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from reminder import reminder_router, reminder
from set_default_time import set_default_time
from time_control import set_waiting_time, get_current_waiting_time_string
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS
from bot_init import bot
from tomato.core.logger_settings import logger_setup


logger_setup()


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        logger.info(f"\nReceived {event!r}\n")
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
dp.include_router(reminder_router)

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
        organization_id = SETTINGS.get_organization_id(message.message_thread_id)
        if organization_id is None:
            return
    except Exception as e:
        error_message = f"Что-то пошло не так! Ошибка: \n❗{html.bold("ОШИБКА:")}❗\n {e}"
        await message.answer(error_message)
        logger.exception(error_message)
        return

    try:
        time = int(message.text)
        token = get_tomato_auth_token()
        set_waiting_time(organization_id, time, token)
        time_string = get_current_waiting_time_string(organization_id, token)
        await message.answer(time_string)
    except Exception as e:
        logger.exception(e)
        # But not all the types is supported to be copied so need to handle it
        await message.answer(f"Что-то пошло не так, пришли время в минутах в числовом виде!\n"
                             f"❗{html.bold("ОШИБКА:")}❗\n {e}")


async def main() -> None:
    # Инициализация скедулера
    scheduler = AsyncIOScheduler()
    # Добавление в скедулер сброса времени на дефолт по расписанию
    default_time_trigger = CronTrigger(hour=22, minute=30)
    scheduler.add_job(set_default_time, trigger=default_time_trigger)

    # Добавление в скедулер напоминания о поддержании времени в актуальном состоянии
    reminder_trigger = IntervalTrigger(hours=1)
    scheduler.add_job(reminder, trigger=reminder_trigger)

    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
