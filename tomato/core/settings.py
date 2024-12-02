from dotenv import load_dotenv

from pydantic_settings import BaseSettings

load_dotenv()  # Загружаем переменные среды из .env


class Settings(BaseSettings):

    TOMATO_LOGIN: str
    TOMATO_PASSWORD: str

    BASE_API_URL: str = "http://smartomato.ru/api"

    AUTHORIZED_USERS: set = {1788982392, 930239035}

    # id телеграм чатов
    #KRUG_CHAT_ID: int
    #KULT_CHAT_ID: int
    #GONZO_CHAT_ID: int

    # id отделов
    KULT_ORGANIZATION_ID: int = 0
    KRUG_ORGANIZATION_ID: int = 44166
    GONZO_ORGANIZATION_ID: int = 0

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

    def get_department_id_by_chat_id(self, chat_id: int):
        if chat_id == self.KRUG_CHAT_ID:
            return self.KRUG_ORGANIZATION_ID

        elif chat_id == self.KULT_CHAT_ID:
            return self.KULT_ORGANIZATION_ID

        elif chat_id == self.GONZO_CHAT_ID:
            return self.GONZO_ORGANIZATION_ID

        else:
            return None


SETTINGS = Settings()
