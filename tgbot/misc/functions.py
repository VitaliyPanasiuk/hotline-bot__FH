from aiogram import Router, Bot, types
from aiogram.types import Message, FSInputFile
from tgbot.config import load_config
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs

from tgbot.misc.states import reg_user

config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')

base = psycopg2.connect(dbname=config.db.database, user=config.db.user, password=config.db.password,host=config.db.host)
cur = base.cursor()


async def auf(type, user_id):
    if type == 'buyer':
        cur.execute("SELECT * FROM buyers WHERE id = %s", (str(user_id),))
        buyer = cur.fetchall()
        print(buyer)
        if len(buyer) > 0:
            return True
        else:
            return False
    if type == 'seller':
        cur.execute("SELECT * FROM sellers WHERE id = %s", (str(user_id),))
        buyer = cur.fetchall()
        if not buyer:
            return False
        else:
            return True
