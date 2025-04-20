from dotenv import load_dotenv

from pydantic_settings import BaseSettings

load_dotenv()  # Загружаем переменные среды из .env


class Settings(BaseSettings):
    MAIN_CHAT_ID: int = -1002351370021

    BOT_TOKEN: str

    TOMATO_LOGIN: str
    TOMATO_PASSWORD: str

    # Iiko
    IIKO_LOGIN: str
    IIKO_HASH_PASSWORD: str
    IIKO_BASE_URL: str

    # Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # UUID преднастроенного отчета в iiko, пример:
    # {'data': [{'Department': '"Круг"', 'DishAmountInt': 20, 'DishType': 'DISH', 'HourOpen': '10'}, {'Department':...]}
    DISH_PER_HOUR_OLAP_UUID: str

    @property
    def DB_URI(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    BASE_API_URL: str = "http://smartomato.ru/api"

    # Режим работы заведений
    TIME_OPEN: int = 10
    TIME_CLOSE: int = 22

    SUPER_ADMIN_ID: int = 1788982392

    AUTHORIZED_USERS: set = {1788982392, 930239035, 836353080}

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
        "AZOV_ALL_ORGANIZATIONS": 40,
        "SELF-DELIVERY_ALL_ORGANIZATIONS": 15,
    }

    # thread_id - id треда в группе
    KRUG: int = 2
    KULT: int = 3
    GONZO: int = 4
    # Список тредов всех заведений
    THREAD_ID_LIST: list = [KRUG, KULT, GONZO]

    # Сопоставление thread_id с id организации в смартомато
    CHAT_ID_TO_ORGANIZATION_ID: dict = {
        KRUG: 44166,
        KULT: 45128,
        GONZO: 45622
    }

    # Сопоставление id организации с названием заведения в смартомато
    NAME_TO_ORGANIZATION_ID: dict = {
        "КРУГ": 44166,
        "КУЛЬТ ЕДЫ": 45128,
        "GONZO": 45622
    }

    # Сопоставление Смартомато id организации с названием заведения в iiko
    ORGANIZATION_ID_TO_IIKO_NAME: dict = {
        44166: '"Круг"',
        45128: 'Культ Еды',
        45622: '«GONZO Азов»'
    }

    ORDERS_CLOSER_API_URL: str

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
