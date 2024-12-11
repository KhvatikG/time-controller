from aiogram import Router, F, types
from loguru import logger

from tomato.core.settings import SETTINGS
broadcast_router = Router()


@broadcast_router.message(F.text.startswith("broadcast"))
async def broadcast(message: types.Message):
    """
    Хэндлер для широковещательной рассылки по всем подключенным каналам
    """
    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        await message.answer('У вас нет прав на выполнение данной команды')
        return

    broadcast_message = message.text.replace("broadcast", "")

    await message.answer("Рассылка начата")
    logger.info("Рассылка начата")

    try:
        for thread_id in SETTINGS.THREAD_ID_LIST:
            await message.bot.send_message(
                chat_id=SETTINGS.MAIN_CHAT_ID,
                message_thread_id=thread_id,
                text=broadcast_message,
            )
    except Exception as e:
        logger.error(e)
        await message.answer(f"Рассылка завершена с ошибкой{e}")
        return

    await message.answer("Рассылка завершена успешно")
    logger.info("Рассылка завершена успешно")
