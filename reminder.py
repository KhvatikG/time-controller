# TODO: Возможно стоит добавить логику оповещения старшего ответственного в случае если нет ответа
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from loguru import logger
from aiogram import Router, html
from sqlalchemy import select

from bot_init import bot
from db.models.user import User
from db.session import get_session
from tomato.time_control import get_current_waiting_time_string
from tomato.core.settings import SETTINGS
from tomato.core.api.auth import get_tomato_auth_token

reminder_router = Router(name=__name__)


def get_keyboard():
    """Возвращает клавиатуру с вариантами ответа"""
    inline_kb_list = [
        [InlineKeyboardButton(text="ДА", callback_data='reminder_yes')],
        [InlineKeyboardButton(text="НЕТ", callback_data='reminder_no')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


async def reminder():
    # Если сейчас заведения закрыты
    if not (SETTINGS.TIME_OPEN <= datetime.now().hour <= SETTINGS.TIME_CLOSE):
        return

    try:
        token = get_tomato_auth_token()
    except Exception as e:
        await bot.send_message(
            SETTINGS.MAIN_CHAT_ID,
            f"[Reminder]Ошибка получения токена: {e}"
        )
        logger.exception(f"Ошибка получения токена: {e}")
        return

    for thread_id in SETTINGS.THREAD_ID_LIST:
        organization_id = SETTINGS.get_organization_id(thread_id)

        if organization_id is None:
            continue

        try:
            time_string = get_current_waiting_time_string(organization_id, token, for_all_zones=True)
        except Exception as e:
            await bot.send_message(
                SETTINGS.MAIN_CHAT_ID,
                f"[Reminder]Ошибка получения времени ожидания: {e}"
            )
            logger.exception(f"Ошибка получения времени ожидания: {e}")
            continue

        await bot.send_message(
            SETTINGS.MAIN_CHAT_ID,
            "Текущее время ожидания:",
            message_thread_id=thread_id
        )
        await bot.send_message(
            SETTINGS.MAIN_CHAT_ID,
            time_string,
            message_thread_id=thread_id
        )

        await bot.send_message(
            SETTINGS.MAIN_CHAT_ID,
            "Верно ли установлено время ожидания?",
            message_thread_id=thread_id,
            reply_markup=get_keyboard()
        )


@reminder_router.callback_query()
async def reminder_callback(call: CallbackQuery):
    if call.data == 'reminder_yes':
        await bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="🔥")
        async with get_session() as session:
            result = await session.execute(select(User).where(User.id == call.from_user.id))
            user = result.scalars().one_or_none()
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Время ожидания установлено верно.\n -{html.italic(user.name)}"
        )
    elif call.data == 'reminder_no':
        await bot.answer_callback_query(
            callback_query_id=call.id,
            show_alert=False,
            text="Пожалуйста введите корректное время ожидания."
        )
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Пожалуйста введите корректное время ожидания."
        )
