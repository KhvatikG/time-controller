import json
import requests

from tomato.core.settings import SETTINGS


def get_tomato_auth_token() -> dict:
    """Принимает логин и пароль от томата и возвращает токен, в случае
    удачной аутентификации и статус запроса
    который необходимо прикладывать к запросам к апишке томата.

    Для вызова метода API необходимо снабдить запрос HTTP-заголовком вида Authorization: Token token="<TOKEN>",
    где <TOKEN> — привязанный к сессии API-ключ.
    Токен можно также передать посредством query-параметра token: /api/orders?token=<TOKEN>.
    """
    url = SETTINGS.BASE_API_URL + '/session'
    payload = {"login": SETTINGS.TOMATO_LOGIN, "password": SETTINGS.TOMATO_PASSWORD}

    r = requests.post(url, params=payload)

    code = r.status_code
    data = json.loads(r.text)

    if code == 200:
        try:
            token = data['meta']['token']
            return {"code": code, "token": token}

        except Exception as e:
            print(f"ОШИБКА АВТОРИЗАЦИИ: {e}") # TODO: заменить на логирование

    else:
        print("Auth filed") # TODO: заменить на логирование
        return {"code": code, "token": "error"}





