from aiogram.enums import ParseMode

from bot_init import bot
from db.models.order_closer_chat import OrderCloserChat
from tomato.core.api.auth import get_tomato_auth_token
from tomato.report import get_order_report_by_departments
from loguru import logger


async def send_departments_report(date: str = None, chats: list[OrderCloserChat] = None) -> None:
    """Отправляет дневной в чат

    :param chats: Чаты для отправки отчета
    :param date: дата в формате YYYY-MM-DD по умолчанию None - будет использована сегодняшняя дата
    """
    logger.info("Отправка дневного отчета по отделам")
    logger.debug("Получение токена")
    token = get_tomato_auth_token()

    logger.debug("Получение дневного отчета")
    df = get_order_report_by_departments(date=date, token=token)
    logger.debug(f"Отчет получен\n{df}")
    logger.info("Начинаю построение сообщений...")

    messages = []
    for i, row in df.iterrows():
        department = row.get('Ресторан')
        count_orders = row.get('Количество заказов')
        count_cancelled_orders = row.get('Количество отменённых')
        avg_check = row.get('Средний чек')
        delivery_sum = row.get('Сумма доставки для клиента')
        summ = str(row.get('Сумма по всем заказам'))
        message = (
            f"Ресторан: <b>{department}</b>\n"
            f"  Количество заказов: <i>{count_orders}</i>\n"
            f"  Отменённых: <i>{count_cancelled_orders}</i>\n"
            f"  Средний чек: <i>{round(avg_check, 2)}</i>\n"
            f"  Сумма доставки для клиента: <i>{delivery_sum}</i>\n"
            f"  Сумма по всем заказам: <b>{summ}</b>\n"
        )
        logger.info(f"Сообщение построено\n{message}")
        logger.info("Отправка сообщения")
        messages.append(message)

    if len(df) == 0:
        message = (
            f"За выбранный период данных нет."
        )
        logger.info(f"Сообщение построено\n{message}")
        logger.info("Отправка сообщения")
        messages.append(message)

    # Отправка сообщений
    for chat in chats:  # В каждый зарегистрированный чат
        for message in messages:  # Каждое сообщение
            await bot.send_message(chat.id, message, parse_mode=ParseMode.HTML)
