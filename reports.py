from aiogram.enums import ParseMode
from aiogram.utils.markdown import bold, italic

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
    for i, row in df.iterrows():
        department = row.get('Ресторан')
        count_orders = row.get('Количество заказов')
        count_cancelled_orders = row.get('Количество отменённых')
        avg_check = row.get('Средний чек')
        delivery_sum = row.get('Сумма доставки для клиента')
        summ = row.get('Сумма по всем заказам')
        message = (
            f"Ресторан: {bold(department)}\n"
            f"  Количество заказов: {italic(count_orders)}\n"
            f"  Отменённых: {italic(count_cancelled_orders)}\n"
            f"  Средний чек: {round(avg_check, 2)}\n"
            f"  Сумма доставки для клиента: {italic(delivery_sum)}\n"
            f"  Сумма по всем заказам: {bold(summ)}\n"
        )
        logger.info(f"Сообщение построено\n{message}")
        logger.info("Отправка сообщения")
        for chat in chats:
            await bot.send_message(chat.id, message, parse_mode=ParseMode.MARKDOWN)
