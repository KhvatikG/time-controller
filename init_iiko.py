from iiko_api import IikoApi
from tomato.core.settings import SETTINGS

iiko = IikoApi(
    base_url=SETTINGS.IIKO_BASE_URL,
    login=SETTINGS.IIKO_LOGIN,
    hash_password=SETTINGS.IIKO_HASH_PASSWORD
)
