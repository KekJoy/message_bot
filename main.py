import asyncio
import os

from aiogram import Bot, Router, Dispatcher, types
from aiogram.enums import ContentType
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
                                            name=f"Чат: {message.from_user.full_name}")
        session.execute(text(f'insert into topic (user_id, message_thread_id, name, icon_color, icon_custom_emoji_id) '
                             f'values ({message.from_user.id}, {chat.message_thread_id}, "{chat.name}", NULL, NULL);'))
        session.commit()

        await bot.send_message(chat_id=settings.CHAT_ID, message_thread_id=chat.message_thread_id,
                               text="Пользователь создал новую тему. Здесь вы можете обсудить запрос.")

    else:
        await message.answer(text=f'Вы уже создали чат, напишите свой запрос.')


@rt.message(F.forum_topic_created)
async def handle_create_forum_topic(message: types.Message):
    await asyncio.sleep(2)
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


async def send_message(chat_id: int, message: types.Message, message_thread_id: int = None, text: str = None):
    match message.content_type:
        case ContentType.TEXT:
            await bot.send_message(chat_id=chat_id,
                                   message_thread_id=message_thread_id,
                                   text=f"{text} {message.text}")
        case ContentType.PHOTO:
            await bot.send_photo(chat_id=chat_id,
                                 message_thread_id=message_thread_id,
                                 photo=message.photo[0].file_id,
                                 caption=f'{text} {"" if message.caption is None else message.caption}')
        case ContentType.VIDEO:
            await bot.send_video(chat_id=chat_id,
                                 message_thread_id=message_thread_id,
                                 video=message.video.file_id,
                                 caption=f'{text} {"" if message.caption is None else message.caption}')
        case ContentType.AUDIO:
            await bot.send_audio(chat_id=chat_id,
                                 message_thread_id=message_thread_id,
                                 audio=message.audio.file_id,
                                 caption=f'{text} {"" if message.caption is None else message.caption}')
        case ContentType.DOCUMENT:
            await bot.send_document(chat_id=chat_id,
                                    message_thread_id=message_thread_id,
                                    document=message.document.file_id,
                                    caption=f'{text} {"" if message.caption is None else message.caption}')
        case ContentType.VOICE:
            await bot.send_voice(chat_id=chat_id,
                                 message_thread_id=message_thread_id,
                                 voice=message.voice.file_id,
                                 caption=f'{text} {"" if message.caption is None else message.caption}')
        case ContentType.CONTACT:
            await bot.send_message(chat_id=chat_id,
                                   message_thread_id=message_thread_id,
                                   text=f"{text}")
            await bot.send_contact(chat_id=chat_id,
                                   message_thread_id=message_thread_id,
                                   first_name=message.contact.first_name,
                                   phone_number=message.contact.phone_number)


@rt.message()
async def handle_chat_message(message: types.Message):
    if not message.is_topic_message and message.chat.id == settings.CHAT_ID:
        return

    if message.is_topic_message:
        with async_session_maker() as session:
            user_id = session.execute(text(
                f"select user_id from topic where message_thread_id == {message.message_thread_id}")).scalars().all()[0]

        await send_message(chat_id=user_id, message=message, text=f'Guskov & Associates:')

    else:
        with async_session_maker() as session:
            user_id = session.execute(
                text(f"select * from topic where user_id == {message.from_user.id}")).scalars().all()
        if user_id:
            chat_id = session.execute(
                text(f"select message_thread_id from topic where user_id == {message.from_user.id}")).scalars().all()[0]

            await send_message(chat_id=settings.CHAT_ID, message=message, message_thread_id=chat_id,
                               text=f"{message.from_user.full_name}:")
        else:
            await message.answer(text=f'Чтобы создать чат, введите команду /start')


if __name__ == "__main__":
    db_is_created = os.path.exists('database.db')
    if not db_is_created:
        create_db()
    asyncio.run(main())
