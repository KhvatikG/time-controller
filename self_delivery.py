from aiogram import Router, F, types, html
from loguru import logger

from decorators import authorized_only
from tomato.core.api.auth import get_tomato_auth_token
from tomato.core.settings import SETTINGS
from tomato.time_control import set_waiting_time, get_current_waiting_time_string

self_delivery_router = Router()


@self_delivery_router.message(F.text.lower().startswith('самовывоз'))
@authorized_only
async def self_delivery(message: types.Message):
    """
    Хэндлер для установки времени самовывоза
    """
    logger.info(
        f"Перехвачено сообщение: {message.text},"
        f" от пользователя{message.from_user.username if message.from_user else None}"
    )
    # Если сообщение не является сообщением в треде чата, то выходим
    if message.message_thread_id is None:
        logger.debug(f"Сообщение не является сообщением в чате {message.message_thread_id=}")
        return

    # Получаем ID организации по ID треда(для каждой организации есть свой тред)
    organization_id = SETTINGS.get_organization_id(message.message_thread_id)

    # Если организация не найдена в конфиге, то выходим
    if organization_id is None:
        logger.debug(f"Организация не найдена в конфиге {organization_id=}, {message.message_thread_id=}")
        return

    # Пытаемся получить и подготовить значение времени в минутах
    try:
        time = message.text.split()[1] if len(message.text.split()) > 1 else None
        if not time:
            await message.answer("Не указано время самовывоза")
            return

        time = int(time)

        if time <= 0:
            await message.answer("Время должно быть больше 0")

    except ValueError as e:
        logger.exception(f"Ошибка ввода времени")
        await message.answer("Время должно быть числом, отражающим кол-во минут ожидания,"
                             " указанным через пробел после команды 'самовывоз'\n"
                             "Например:\nсамовывоз 20")
    except Exception as e:
        logger.exception(f"Ошибка ввода времени")
        await message.answer(f"[self_delivery]Неизвестная ошибка{e}")

    # Если со значением времени все ок
    else:
        # Устанавливаем время самовывоза
        try:
            token = get_tomato_auth_token()
            await set_waiting_time(organization_id, time, token, for_self_delivery=True)
            time_string = get_current_waiting_time_string(organization_id, token, for_self_delivery=True)
            await message.answer(time_string)

        except Exception as e:
            logger.exception(e)
            await message.answer(f"Что-то пошло не так...\n"
                                 f"❗{html.bold("ОШИБКА:")}❗\n {e}")
