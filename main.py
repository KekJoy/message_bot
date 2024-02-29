import asyncio
import os

from aiogram import Bot, Router, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from sqlalchemy import text

from database import create_db, async_session_maker
from config import settings

bot = Bot(token=settings.BOT_TOKEN)
rt = Router()


async def main():
    dp = Dispatcher()
    dp.include_router(rt)
    await dp.start_polling(bot)


@rt.message(Command('start'))
async def handle_start_chat(message: types.Message):
    if not message.is_topic_message and message.chat.id == settings.CHAT_ID:
        return

    with async_session_maker() as session:
        user = session.execute(text(f'select * from topic where user_id == {message.from_user.id}')).scalars().all()
    if not user:
        chat = await bot.create_forum_topic(chat_id=settings.CHAT_ID,
                                            name=f"Чат {message.from_user.id}: {message.from_user.full_name}")

        session.execute(text(f'insert into topic (user_id, message_thread_id, name, icon_color, icon_custom_emoji_id) '
                             f'values ({message.from_user.id}, {chat.message_thread_id}, "{chat.name}", NULL, NULL);'))
        session.commit()

        await bot.send_message(chat_id=settings.CHAT_ID, message_thread_id=chat.message_thread_id,
                               text="Пользователь создал новую тему. Здесь вы можете обсудить запрос.")

    else:
        await message.answer(text=f'Вы уже создали чат, напишите свой запрос.')


@rt.message(F.forum_topic_created)
async def handle_close_forum_topic(message: types.Message):
    with async_session_maker() as session:
        user_id = session.execute(
            text(f"select user_id from topic where message_thread_id={message.message_thread_id}")).scalars().all()[0]
        name = session.execute(
            text(f"select name from topic where message_thread_id={message.message_thread_id}")).scalars().all()[0]
    await bot.send_message(chat_id=user_id, text=f"Тема \"{name}\" создана. Ожидайте сообщения от администратора.")


@rt.message(F.forum_topic_closed)
async def handle_close_forum_topic(message: types.Message):
    with async_session_maker() as session:
        user_id = session.execute(
            text(f"select user_id from topic where message_thread_id={message.message_thread_id}")).scalars().all()[0]
    await bot.send_message(chat_id=user_id,
                           text=f"Администратор закрыл чат. Чтобы отправить новое сообщение, введите команду /start")

    await bot.send_message(chat_id=settings.CHAT_ID, message_thread_id=message.message_thread_id,
                           text=f"Вы закрыли чат.")

    session.execute(text(
        f"DELETE FROM topic WHERE message_thread_id={message.message_thread_id};"))
    session.commit()


@rt.message()
async def handle_chat_message(message: types.Message):
    if not message.is_topic_message and message.chat.id == settings.CHAT_ID:
        return

    if message.is_topic_message:
        with async_session_maker() as session:
            user_id = session.execute(text(
                f"select user_id from topic where message_thread_id == {message.message_thread_id}")).scalars().all()[0]

        await bot.send_message(chat_id=user_id, text=f"Guskov & Associates: {message.text}")

    else:
        with async_session_maker() as session:
            user_id = session.execute(
                text(f"select * from topic where user_id == {message.from_user.id}")).scalars().all()
        if user_id:
            chat_id = session.execute(
                text(f"select message_thread_id from topic where user_id == {message.from_user.id}")).scalars().all()[0]
            await bot.send_message(chat_id=settings.CHAT_ID, message_thread_id=chat_id,
                                   text=f"{message.from_user.full_name}: {message.text}")
        else:
            await message.answer(text=f'Чтобы создать чат, введите команду /start')


if __name__ == "__main__":
    db_is_created = os.path.exists('database.db')
    if not db_is_created:
        create_db()
    asyncio.run(main())
