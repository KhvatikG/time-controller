from datetime import datetime
import pandas as pd
from urllib.parse import quote
import io

import requests


def get_order_report_by_departments_html(token: str, date: str = "now"):
    """
    Получение отчета о заказах по отделам
    Возвращает HTML таблицу

    :param token: токен для авторизации
    :param date: дата в формате YYYY-MM-DD по умолчанию - сегодняшняя дата
    """

    # URL запроса
    url = "https://app.smartomato.ru/api/reports/perform.html?id=orders"

    if date == "now":
        date = datetime.now().strftime("%Y-%m-%d")

    start_time = "T00:00:00.000Z"
    end_time = "T22:30:00.000Z"

    date_from = f"{date}{start_time}"
    date_to = f"{date}{end_time}"

    payload = {"filter": {"$and": [{"$or": [{"$and": [{"delivery_at": {"$gte": date_from}},
                                                      {"delivery_at": {"$lte": date_to}}]}]}]},
               "group_by": ["restaurant_id"]}
    headers = {
        "Authorization": f"Token token={token}",
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response


def get_order_report_by_departments(token: str, date: str = "now") -> pd.DataFrame:
    """
    Получение дневного отчета о заказах по отделам
    Возвращает DataFrame с данными CSV-отчёта.

    :param token: токен для авторизации
    :param date: дата в формате YYYY-MM-DD по умолчанию - сегодняшняя дата
    """

    # URL запроса
    url = "https://app.smartomato.ru/api/reports/perform.xlsx"

    if date == "now":
        date = datetime.now().strftime("%Y-%m-%d")

    start_time = "T00:00:00.000Z"
    end_time = "T22:30:00.000Z"

    date_from = f"{date}{start_time}"
    date_to = f"{date}{end_time}"

    # Пример фильтра в формате JSON (экранирован для URL)
    # Здесь подставляются даты
    filter_json = (
                      '{"$and":[{"$or":[{"$and":['
                      '{"delivery_at":{"$gte":"%s"}},'
                      '{"delivery_at":{"$lte":"%s"}}'
                      ']}]}]}'
                  ) % (date_from, date_to)

    # Параметры запроса (обратите внимание, что некоторые ключи содержат специальные символы)
    params = {
        "action": "perform",
        "controller": "api/v1/reports",
        "filter": filter_json,
        "format": "html",
        "group_by[]": "restaurant_id",
        "id": "orders",
        # Параметры для report-фильтра. Их можно задать аналогично, если они требуются
        "report[filter][$and][][$or][][$and][][delivery_at][$gte]": date_from,
        "report[filter][$and][][$or][][$and][][delivery_at][$lte]": date_to,
        "report[group_by][]": "restaurant_id",
        "token": token
    }

    # Отправляем GET-запрос
    response = requests.get(url, params=params)
    response.raise_for_status()  # выбросит исключение при ошибке

    # Сохраняем CSV-данные (или сразу читаем в DataFrame)
    text_data = response.content
    print(text_data)

    """# Чтение данных через StringIO с настройками для парсинга
    df = pd.read_csv(
        io.StringIO(text_data),
        sep=';',          # Разделитель — точка с запятой
        quotechar='"',     # Обрамление значений в кавычки
        dtype=str,        # Сохранить все данные как строки
        keep_default_na=False  # Не заменять пустые строки на NaN
    )"""
    df = pd.read_excel(
        io.BytesIO(text_data),
    )

    return df
