from aiogram import Router, Bot, types
from aiogram.types import Message, FSInputFile
from tgbot.config import load_config
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs

from tgbot.misc.states import reg_user
from tgbot.misc.functions import auf

user_router = Router()
config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')

base = psycopg2.connect(dbname=config.db.database, user=config.db.user, password=config.db.password,host=config.db.host)
cur = base.cursor()


@user_router.message(commands=["start"])
async def user_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    auf_user = await auf("buyer", user_id)
    print(auf_user)
    if not auf_user:
        await message.reply("Привет!")
        await bot.send_message(user_id, "Отправь мне свое имя")
        await state.set_state(reg_user.name)
    else:
        await message.reply("Привет!")


@user_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.name)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(name=text)
    await bot.send_message(user_id, "Отправь мне свой номер телефона")
    await state.set_state(reg_user.phone)


@user_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.phone)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(phone=text)
    data = await state.get_data()
    cur.execute("INSERT INTO buyers (id, name, phone) VALUES (%s, %s, %s)",
                (user_id, data['name'], data['phone']))
    base.commit()
    await bot.send_message(user_id, "Вы зарегистрированы")


@user_router.message(commands=["buy"])
async def user_start(message: Message, state: FSMContext):
    await message.reply("Привет!")
