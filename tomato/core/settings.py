from dotenv import load_dotenv

from pydantic_settings import BaseSettings

load_dotenv()  # Загружаем переменные среды из .env


class Settings(BaseSettings):

    MAIN_CHAT_ID: int = -1002351370021

    BOT_TOKEN: str

    TOMATO_LOGIN: str
    TOMATO_PASSWORD: str

    BASE_API_URL: str = "http://smartomato.ru/api"

    AUTHORIZED_USERS: set = {1788982392, 930239035}

    # id зон
    KRUG_AZOV_ID: int = 37894
    KRUG_YASNY_SOLNECHNY_ID: int = 54142
    KRUG_KULESHOVKA_ID: int = 39832
    KRUG_NOVOALEXANDROVKA_ID: int = 39830

    KULT_AZOV_ID: int = 45398
    KULT_YASNY_SOLNECHNY_ID: int = 54164

    GONZO_AZOV_ID: int = 49937
    GONZO_YASNY_SOLNECHNY_ID: int = 54148

    # Дельты
    DELTAS: dict = {
        KRUG_AZOV_ID: 0,
        KRUG_YASNY_SOLNECHNY_ID: 0,
        KRUG_NOVOALEXANDROVKA_ID: 20,
        KRUG_KULESHOVKA_ID: 25,

        KULT_AZOV_ID: 0,
        KULT_YASNY_SOLNECHNY_ID: 0,

        GONZO_AZOV_ID: 0,
        GONZO_YASNY_SOLNECHNY_ID: 0,
    }

    # Дефолтные значения времени
    DEFAULT_ZONES_TIMES: dict = {
        "AZOV_ALL_ORGANIZATIONS": 40
    }

    # thread_id - id треда в группе
    KRUG: int = 2
    KULT: int = 3
    GONZO: int = 4
    # Сопоставление thread_id с id организации в смартомато
    CHAT_ID_TO_ORGANIZATION_ID: dict = {
        KRUG: 44166,
        KULT: 45128,
        GONZO: 45622
    }

    def get_organization_id(self, message_thread_id):
        """
        Возвращает идентификатор организации по номеру чата.
        :param message_thread_id: id чата
        :return:
        """

        if message_thread_id in self.CHAT_ID_TO_ORGANIZATION_ID:
            return self.CHAT_ID_TO_ORGANIZATION_ID[message_thread_id]
        else:
            return None


SETTINGS = Settings()
