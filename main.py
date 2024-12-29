# TODO: Вынести сервисы в модуль services, и обдумать архитектуру
import asyncio

from aiogram import Dispatcher, html, BaseMiddleware
from aiogram.filters import CommandStart, Filter
from aiogram.types import Message, Update
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from close_orders import close_orders
from close_orders_handler import order_closer_router
from self_delivery import self_delivery_router
from broadcast import broadcast_router
from db.models.base import Base
from db.session import engine
from decorators import authorized_only
from reminder import reminder_router, reminder
from set_default_time import set_default_time
from tomato.time_control import set_waiting_time, get_current_waiting_time_string
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS
from bot_init import bot
from tomato.core.logger_settings import logger_setup
from user_control import user_control_router

logger_setup()


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        logger.bind(aiogram_event=True).info(f"---------------------EVENT RECEIVED---------------------\n{event!r}\n---------------------")
        return await handler(event, data)


class NumericFilter(Filter):
    """
    Фильтр для проверки, что сообщение содержит только цифры
    """
    def __init__(self) -> None:
        ...

    async def __call__(self, message: Message) -> bool:
        return message.text.strip().isdigit()


dp = Dispatcher()
dp.update.middleware(LoggingMiddleware())
dp.include_routers(
    reminder_router,
    user_control_router,
    broadcast_router,
    self_delivery_router,
    order_closer_router
)


@dp.message(CommandStart())
@authorized_only
async def command_start_handler(message: Message) -> None:
    """
    Хэндлер команды `/start`
    """
    await message.answer(f'''
    Ну привет, {html.bold(message.from_user.full_name)}...\n
    ''')


@dp.message(NumericFilter())
@authorized_only
async def echo_handler(message: Message) -> None:
    """
    Хэндлер для перехвата времени в минутах из сообщения, ожидает числа, обрезает пробелы по краям.
    Устанавливает время ожидания для всех зон кроме самовывоза.
    Если сообщение не является сообщением в треде чата или тред чата не занесен в конфиг, то ничего не происходит.
    """
    logger.debug(f"Начинаем перехват времени...")
    if message.message_thread_id is None:
        logger.debug(f"Сообщение не является сообщением в чате {message.message_thread_id=}")
        return

    try:
        organization_id = SETTINGS.get_organization_id(message.message_thread_id)
        if organization_id is None:
            logger.debug(f"Организация не найдена в конфиге {organization_id=}, {message.message_thread_id=}")
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
        await message.answer(f"Что-то пошло не так...\n"
                             f"❗{html.bold("ОШИБКА:")}❗\n {e}")


async def main() -> None:
    # Инициализация БД
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        return  # Останавливаем приложение при возникновении ошибки

    # Инициализация скедулера
    scheduler = AsyncIOScheduler(timezone=timezone('Europe/Moscow'))

    # Добавление в скедулер сброса времени на дефолт по расписанию
    default_time_trigger = CronTrigger(hour=23, minute=20, timezone=timezone('Europe/Moscow'))
    scheduler.add_job(set_default_time, trigger=default_time_trigger)
    # Добавление в скедулер закрытие заказов
    close_orders_time_trigger = CronTrigger(hour=23, minute=20, timezone=timezone('Europe/Moscow'))
    scheduler.add_job(close_orders, trigger=close_orders_time_trigger)

    # Добавление в скедулер напоминания о поддержании времени в актуальном состоянии
    reminder_trigger = IntervalTrigger(hours=2)
    scheduler.add_job(reminder, trigger=reminder_trigger)

    # Запускаем скедулер
    scheduler.start()

    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
