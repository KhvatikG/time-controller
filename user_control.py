from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from db.models.user import User
from db.session import get_session
from tomato.core.settings import SETTINGS

user_control_router = Router()


def parse_user(userdata: str) -> dict:
    """Парсит пользователя из сообщения и возвращает пользователя в виде словаря"""

    userdata = userdata.split(',')
    user = {
        "id": int(userdata[0].strip()),
        "name": userdata[1].strip(),
    }
    if len(userdata) > 2:
        user["role"] = userdata[2].strip()

    return user


@user_control_router.message(F.text.startswith('adduser'))
async def add_user(message: Message):
    """"Перехватчик добавления нового пользователя"""
    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        await message.answer('У вас нет прав на выполнение данной команды')
        return
    try:
        user_dict = parse_user(message.text.lstrip('adduser'))
        async with get_session() as session:
            result = await session.execute(select(User).where(User.id == user_dict["id"]))
            user = result.scalar_one_or_none()
            if user:
                await message.answer(f'Пользователь с данным id уже существует')
                return

            user = User(
                id=user_dict["id"],
                name=user_dict["name"],
                role=user_dict.get("role"),
            )
            session.add(user)
            await session.commit()
            await message.answer(f'Пользователь {user_dict["name"]} добавлен')
    except Exception as e:
        await message.answer(f'Ошибка добавления пользователя: {e}')


@user_control_router.message(F.text == 'getusers')
async def get_users(message: Message):
    """Перехватчик получения списка пользователей"""
    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        await message.answer('У вас нет прав на выполнение данной команды')
        return
    try:
        async with get_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            users_list = [f'{user.id}, {user.name}, {user.role}' for user in users]
            await message.answer('\n-----------------\n'.join(users_list))
    except Exception as e:
        await message.answer(f'Ошибка получения списка пользователей: {e}')


@user_control_router.message(F.text.startswith('deluser'))
async def del_user(message: Message):
    """Перехватчик удаления пользователя"""
    if message.from_user.id != SETTINGS.SUPER_ADMIN_ID:
        await message.answer('У вас нет прав на выполнение данной команды')
        return
    try:
        async with get_session() as session:
            result = await session.execute(select(User).where(User.id == int(message.text.lstrip('deluser'))))
            user = result.scalar_one_or_none()
            if not user:
                await message.answer(f'Пользователь с данным id не найден')
                return
            await session.delete(user)
            await session.commit()
            await message.answer(f'Пользователь {user.name} удален')
    except Exception as e:
        await message.answer(f'Ошибка удаления пользователя: {e}')
