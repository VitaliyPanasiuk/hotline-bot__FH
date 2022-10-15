from aiogram import Router, Bot, types
from aiogram.types import Message, FSInputFile
from magic_filter import F
from tgbot.config import load_config
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs

from tgbot.misc.states import reg_user,make_req,accept_ord,end_order
from tgbot.misc.functions import auf

from tgbot.keyboards.textBtn import choose_cat_button,choose_action
from tgbot.keyboards.inlineBtn import choose_delivery_button,homeS_button
from tgbot.keyboards.inlineBtn import SellersCallbackFactory

import datetime
import requests
from bs4 import BeautifulSoup
import re


seller_router = Router()
config = load_config(".env")
bot2 = Bot(token=config.tg_bot.token2, parse_mode='HTML')
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')

base = psycopg2.connect(dbname=config.db.database, user=config.db.user, password=config.db.password,host=config.db.host)
cur = base.cursor()


@seller_router.message(commands=["start"])
async def user_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    auf_user = await auf("seller", user_id)
    if not auf_user:
        await message.reply("Привіт!")
        await bot2.send_message(user_id, "Відправте своє ім'я або назву компанії")
        await state.set_state(reg_user.name)
    else:
        btn = homeS_button()
        await bot.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())


@seller_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.name)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(name=text)
    await bot2.send_message(user_id, "Відправте свій email")
    await state.set_state(reg_user.email)

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.email)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(email=text)
    await bot2.send_message(user_id, "Відправте свій номер телефону(який буде використовуватися для обслуговування клієнтів, що зареєстрований у Телеграм)")
    await state.set_state(reg_user.phone)


@seller_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.phone)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(phone=text)
    await bot2.send_message(user_id, "Вкажіть організаційно-правову форму (фізична особа, ФОП, юридична особа)")
    await state.set_state(reg_user.org)
    


@seller_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.org)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(org=text)
    data = await state.get_data()
    cur.execute("INSERT INTO sellers (id, name, phone,org_form,email) VALUES (%s,%s,%s, %s, %s)",
                (user_id, data['name'], data['phone'], data['org'], data['email']))
    base.commit()
    await bot2.send_message(user_id, "Ви зареєстровані")
    await bot2.send_message(user_id, "Будь ласка, заповніть анкету та укажіть в ній усі цільові категорії товарів\послуг , що ви продаєте\надаєте!\nhttps://forms.gle/BQAgbumLSM34cNv69")
    btn = homeS_button()
    await bot.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())


@seller_router.callback_query(SellersCallbackFactory.filter(F.action == "accept_order"))
async def user_start(callback_query: types.CallbackQuery, callback_data: SellersCallbackFactory, state: FSMContext):
    user_id = callback_query.from_user.id
    order_id = callback_data.order_id
    now = datetime.datetime.now()
    cur.execute("SELECT valid_time FROM orders WHERE id = %s",(int(order_id),))
    valid_time = cur.fetchone()
    print(valid_time)
    if now > valid_time[0]:
        await bot2.send_message(user_id, "Час на відповідь вичерпано")
    else:
        await state.update_data(id=order_id)
        await state.update_data(seller_id=user_id)
        await bot2.send_message(user_id, "Введіть ціну")
        await state.set_state(accept_ord.price)

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=accept_ord.price)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(price=text)
    await bot2.send_message(user_id, "Введіть додаткові умови")
    await state.set_state(accept_ord.terms)

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=accept_ord.terms)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(terms=text)
    await bot2.send_message(user_id, "Введіть коментар")
    await state.set_state(accept_ord.comment)

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=accept_ord.comment)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(comment=text)
    data = await state.get_data()

    cur.execute("UPDATE orders SET sellers = sellers || ARRAY[%s], prices = prices || ARRAY[%s], seller_terms = seller_terms || ARRAY[%s], seller_coms = seller_coms || ARRAY[%s] WHERE id = %s",(str(data['seller_id']),str(data['price']),data['terms'],data['comment'],data['id']))
    base.commit()
    await bot2.send_message(user_id, "Ваша заявка прийнята")
    await state.clear()

@seller_router.callback_query(lambda c: c.data == 'endsellar')
async def user_start(callback_query: types.CallbackQuery, state = FSMContext):
    user_id = callback_query.from_user.id
    await bot.send_message(user_id,f'Введіть id замовлення')
    await state.set_state(end_order.id)
    

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=end_order.id)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    try:
        cur.execute("select * from orders where id = %s",(int(text),))
        order = cur.fetchone()
        if order:
            await state.update_data(id=int(text))
            btn = choose_action()
            await bot.send_message(user_id,f'Оберіть дію',reply_markup=btn.as_markup(resize_keyboard=True))
            await state.set_state(end_order.action)
        else:
            await bot.send_message(user_id,f'Такого замовлення не знайдено')
            btn = homeS_button()
            await bot.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())
    except:
        await bot.send_message(user_id,f'Невірний формат id')
        btn = homeS_button()
        await bot.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=end_order.action)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    if text == 'Підтвердити виконання':
        await bot.send_message(user_id,f'Введіть бал, який буде поставленно покупцю',reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(end_order.action)
    elif text == 'Скарга':
        await bot.send_message(user_id,f'Скаргу було надіслано',reply_markup=types.ReplyKeyboardRemove())
        cur.execute("select buyer_id from orders where id = %s",(data['id'],))
        buyer_id = cur.execute()
        cur.execute("update buyers set rating = rating - 1 where id = %s",(buyer_id[0],))
        base.commit()
    elif text == 'Відмінити замовлення':
        await bot.send_message(user_id,f'Замовлення було відмінено',reply_markup=types.ReplyKeyboardRemove())
        

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=end_order.rate)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(rate=int(text))
    data = await state.get_data()
    cur.execute("select buyer_id from orders where id = %s",(data['id'],))
    buyer_id = cur.execute()
    cur.execute("update buyers set rating = rating + 1  where id = %s",(buyer_id[0],))
    base.commit()
    await bot.send_message(user_id,f'Чудово, замовлення закрито')
    await state.clear()




