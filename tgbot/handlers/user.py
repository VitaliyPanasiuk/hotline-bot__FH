from aiogram import Router, Bot, types
from aiogram.types import Message, FSInputFile
from tgbot.config import load_config
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs

from tgbot.misc.states import reg_user,make_req
from tgbot.misc.functions import auf

from tgbot.keyboards.textBtn import choose_cat_button
from tgbot.keyboards.inlineBtn import choose_delivery_button


import requests
from bs4 import BeautifulSoup
import re


user_router = Router()
config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')

base = psycopg2.connect(dbname=config.db.database, user=config.db.user, password=config.db.password,host=config.db.host)
cur = base.cursor()

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 OPR/90.0.4480.117'}


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
    await message.reply("Привет!\nВведи название товара")
    await state.set_state(make_req.name)
    
@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.name)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(name=text)
    
    arr = text.split(' ')
    url = "https://hotline.ua/sr/?q="
    for elem in arr:
        url += elem + "%20"
        
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    try:
        cat = soup.findAll('div', class_='search-sidebar-catalogs__name')
        price = soup.find('div', class_='list-item__value--overlay').find('div', class_='m_b-5').find('div', class_='text-sm')
        categories = []
        price = price.text.strip()
        for i in cat:
            p = re.sub(r'\([^)]*\)', '', i.text).strip()
            categories.append(p)
            
        btn = choose_cat_button(categories)
        await bot.send_message(user_id, "Выберите нужную категорию",reply_markup=btn.as_markup(resize_keyboard=True))
        await state.set_state(make_req.cat)
    except:
        await bot.send_message(user_id, "Такого товара не найдено, проверьте правильность написания названия и введите его заново",reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(make_req.name)
        
@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.cat)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(cat=text)
    arr = []
    btn = choose_delivery_button(arr)
    await bot.send_message(user_id, "Отлично!",reply_markup=types.ReplyKeyboardRemove())
    await bot.send_message(user_id, "Укажите желательный способ доставки",reply_markup=btn.as_markup())
    

@user_router.callback_query(lambda c: c.data == 'deliveri_done', state=make_req)
async def user_start(callback_query: types.CallbackQuery, state = FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("SELECT delivery FROM buyers WHERE id = %s",(str(user_id),))
    deliveri = cur.fetchone()
    await state.update_data(delivers=deliveri[0])
    await bot.send_message(user_id, "Отлично, укажите свой город",reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(make_req.city)
    
@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.city)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(city=text)
    await bot.send_message(user_id, "Отлично, укажите дополнительные требования коментарием к заказу",reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(make_req.comment)
    
@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.city)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(comment=text)
    await bot.send_message(user_id, "Отлично, ваша заявка принята",reply_markup=types.ReplyKeyboardRemove())
    
    
    