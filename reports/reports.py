from datetime import datetime, timedelta

from aiogram.enums import ParseMode

from bot_init import bot
from db.models.order_closer_chat import OrderCloserChat
from db.session import get_session
from init_iiko import iiko
from reports.dish_per_time_report import generate_report
from reports.waiting_report import get_daily_time_report
from tomato.core import settings
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS
from tomato.report import get_order_report_by_departments
from loguru import logger

from utils import get_organization_id_per_name


async def send_departments_report(date: str = "now", chats: list[OrderCloserChat] = None) -> None:
    """Отправляет дневной в чат

    :param chats: Чаты для отправки отчета
    :param date: дата в формате YYYY-MM-DD по умолчанию None - будет использована сегодняшняя дата
    """
    if date == "now":
        date = datetime.now().strftime("%Y-%m-%d")
    next_day = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)

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

        department_id = str(get_organization_id_per_name(department))
        async with get_session() as session:
            waiting_report_data = await get_daily_time_report(session, department_id, datetime.fromisoformat(date))

        # Переводим множества в строки для отправки в телеграм
        delivery_periods = waiting_report_data.get("Доставка").get('max_periods')
        if delivery_periods:
            delivery_periods_strings = "\n    ".join(
                [f"{period.get('start').strftime('%H:%M')} - {period.get('end').strftime('%H:%M')}"
                 for period in delivery_periods]
            )
        else:
            delivery_periods_strings = ["нет данных"]

        pickup_periods = waiting_report_data.get("Самовывоз").get('max_periods')
        if pickup_periods:
            pickup_periods_strings = "\n    ".join(
                [f"{period.get('start').strftime('%H:%M')} - {period.get('end').strftime('%H:%M')}"
                 for period in pickup_periods]
            )
        else:
            pickup_periods_strings = ["нет данных"]

        iiko_count_orders_api_data = iiko.olap.get_olap_by_preset_id(
            preset_id=SETTINGS.COUNT_ORDERS_OLAP_UUID,
            date_from=datetime.fromisoformat(date),
            date_to=next_day,
        )
        department_iiko_name = settings.SETTINGS.ORGANIZATION_ID_TO_IIKO_NAME.get(int(department_id))

        iiko_orders_count = 0
        try:
            if orders_data := iiko_count_orders_api_data.get('data'):
                logger.info(f"Получение данных о количестве заказов в Iiko")
                logger.info(f"Данные по количеству заказов в Iiko: {orders_data}")
                for orders_data_item in orders_data:
                    logger.info(f"Данные: {orders_data_item}")
                    if orders_data_item.get('Department') == department_iiko_name:
                        iiko_orders_count = orders_data_item.get('UniqOrderId.OrdersCount')
                        logger.info(f"Количество заказов в Iiko для организации {department_iiko_name}: {iiko_orders_count}")
                    else:
                        logger.warning(f"Нет данных по количеству заказов в Iiko для организации {department_iiko_name}")
            else:
                logger.warning(f"Нет данных по количеству заказов в Iiko")
                logger.warning(f"Отчет по количеству заказов в Iiko: {iiko_count_orders_api_data}")
        except Exception as e:
            logger.exception(f"Ошибка при получении данных о количестве заказов в Iiko")

        message = (
            f"<b>───────────────────</b>\n"
            f"Ресторан: <b>{department}</b>\n"
            f"<b>───────────────────</b>\n"
            f"  Количество заказов через томат: <i>{count_orders} из {iiko_orders_count}</i>\n"
            f"  Это: <i>{round(count_orders/iiko_orders_count*100) if iiko_orders_count else '-'}% от общего количества</i>\n"
            f"  Отменённых: <i>{count_cancelled_orders}</i>\n"
            f"  Средний чек: <i>{round(avg_check, 2)}</i>\n"
            f"  Сумма доставки для клиента: <i>{delivery_sum}</i>\n"
            f"  Сумма по всем заказам: <b>{summ}</b>\n"
            f"<i>------------------------------------------</i>\n"
            f"  <b>Доставка:</b>\n"
            f"  Среднее время ожидания: <i>{waiting_report_data.get("Доставка").get('average_time')}</i>\n"
            f"  Максимальное время ожидания: <i>{waiting_report_data.get("Доставка").get('max_time')}</i>\n"
            f"    В периоды: <i>\n    {delivery_periods_strings}</i>\n\n"
            f"<i>------------------------------------------</i>\n"
            f"  <b>Самовывоз:</b>\n"
            f"  Среднее время ожидания: <i>{waiting_report_data.get("Самовывоз").get('average_time')}</i>\n"
            f"  Максимальное время ожидания: <i>{waiting_report_data.get("Самовывоз").get('max_time')}</i>\n"
            f"    В периоды: <i>\n    {pickup_periods_strings}</i>\n"
            f"<i>------------------------------------------</i>\n"
        )
        logger.info(f"Сообщение построено\n{message}")
        logger.info("Отправка сообщения")

        iiko_api_data = iiko.olap.get_olap_by_preset_id(
            preset_id=SETTINGS.DISH_PER_HOUR_OLAP_UUID,
            date_from=datetime.fromisoformat(date),
            date_to=next_day,
        )
        animation = await generate_report(
            department_name=department,
            api_data=iiko_api_data,
            department_id=int(department_id),
            date_filter=date,
        )

        messages.append({"message": message, "animation": animation})

    if len(df) == 0:
        message = {
            "message": f"За выбранный период данных нет."
        }
        logger.info(f"Сообщение построено\n{message}")
        logger.info("Отправка сообщения")
        messages.append(message)

    # Отправка сообщений
    for chat in chats:  # В каждый зарегистрированный чат
        for message in messages:  # Каждое сообщение
            if animation := message.get("animation"):
                text_message = message.get("message") or "-"
                await bot.send_message(chat_id=chat.id, text=text_message, parse_mode=ParseMode.HTML)
                await bot.send_video(
                    chat_id=chat.id,
                    video=animation,
                    width=1920,
                    height=1080
                )
            else:
                text_message = message.get("message") or "-"
                await bot.send_message(chat_id=chat.id, text=text_message, parse_mode=ParseMode.HTML)
