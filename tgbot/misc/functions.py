from aiogram import Router, Bot, types
from aiogram.types import Message, FSInputFile
from tgbot.config import load_config
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup

from tgbot.keyboards.inlineBtn import accept_order_btn
from tgbot.keyboards.inlineBtn import SellersCallbackFactory
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs

from tgbot.misc.states import reg_user
import gspread

import datetime
import asyncio
import json

class GoogleSheets:
    def __init__(self, filename, google_sheet_name):
        service_account = gspread.service_account(filename)
        self.sheet = service_account.open(google_sheet_name)

config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
bot2 = Bot(token=config.tg_bot.token2, parse_mode='HTML')

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

async def mailing_sellers(name,category,min_max,rate,comment,id,city,delivery):
    cur.execute("SELECT * FROM sellers")
    sellers = cur.fetchall()
    print('start send messages to sellers')
    for seller in sellers:
        print(seller)
        if seller[3] and category in seller[3]:
            message = f'''
Товар: {name}
Категорія: {category}
Місто: {city}
Доставка: {delivery}
мін-макс ціна: {min_max}
Коментар: {comment}
Рейтинг покупця: {rate[0]}
            '''
            btn = accept_order_btn(id)
            await bot2.send_message(seller[0],message,reply_markup=btn.as_markup())
            
async def update_category():
    while True:
        print('start change category')
        service=GoogleSheets(filename='cred.json', google_sheet_name='Анкета продавця для сервісу Цінокрад (Ответы)')
        all_sheets = service.sheet.worksheets()
        sh = all_sheets[0]
        ranges = 'A2:ES1000'
        worksheet = service.sheet.worksheet(sh.title)
        result = worksheet.get(ranges)
        if result:
            for k in range(len(result)):
                cat = []
                email = result[k][1]
                for i in range(len(result[k])):
                    if i not in [0,1,2,3,4,5] and result[k][i]:
                        arr = result[k][i].split(',')
                        for r in arr:
                            cat.append(r)
                cur.execute("UPDATE sellers SET category = %s WHERE email = %s",(cat,email))
                base.commit()
        # TODO: change timer to 300
        await asyncio.sleep(300)




