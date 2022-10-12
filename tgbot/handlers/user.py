from random import randint
from aiogram import Router, Bot, types
from aiogram.types import Message, FSInputFile
from tgbot.config import load_config
from aiogram.dispatcher.fsm.context import FSMContext
from magic_filter import F
from aiogram.dispatcher.fsm.state import State, StatesGroup

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs

from tgbot.misc.states import reg_user,make_req,end_order
from tgbot.misc.functions import auf,mailing_sellers

from tgbot.keyboards.textBtn import choose_cat_button
from tgbot.keyboards.inlineBtn import choose_delivery_button,accept_order_buyer_btn
from tgbot.keyboards.inlineBtn import SellersCallbackFactory


import datetime
import requests
from bs4 import BeautifulSoup
import re
import asyncio


user_router = Router()
config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
bot2 = Bot(token=config.tg_bot.token2, parse_mode='HTML')

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
        await message.reply("Привіт!")
        await bot.send_message(user_id, "Відправ мені своє ім'я")
        await state.set_state(reg_user.name)
    else:
        await message.reply("Привіт!")


@user_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.name)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(name=text)
    await bot.send_message(user_id, "Відправ мені свой номер телефону")
    await state.set_state(reg_user.phone)


@user_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.phone)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(phone=text)
    data = await state.get_data()
    cur.execute("INSERT INTO buyers (id, name, phone,delivery) VALUES (%s, %s, %s, %s)",
                (user_id, data['name'], data['phone'],[]))
    base.commit()
    await bot.send_message(user_id, "Вы зареєстровані")
    await state.clear()


@user_router.message(commands=["buy"])
async def user_start(message: Message, state: FSMContext):
    await message.reply("Привіт!\nВведи назву товару")
    await state.set_state(make_req.name)
    
@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.name)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(name=text)
    
    arr = text.split(' ')
    url = "https://hotline.ua/ua/sr/?q="
    for elem in arr:
        url += elem + "%20"
        
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    try:
        cat = soup.findAll('div', class_='search-sidebar-catalogs__name')
        price = soup.find('div', class_='list-item__value--overlay').find('div', class_='m_b-5').find('div', class_='text-sm')
        categories = []
        price = price.text.strip()
        await state.update_data(min_max=price)

        for i in cat:
            p = re.sub(r'\([^)]*\)', '', i.text).strip()
            categories.append(p)
            
        btn = choose_cat_button(categories)
        await bot.send_message(user_id, "Оберіть потрібну категорію",reply_markup=btn.as_markup(resize_keyboard=True))
        await state.set_state(make_req.cat)
    except:
        await bot.send_message(user_id, "Товару не знайдено, перевірьте вірність написання та введіть його знову",reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(make_req.name)
        
@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.cat)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(cat=text)
    cur.execute("select delivery from buyers where id = %s",(str(user_id),))
    arr = cur.fetchone()
    if arr[0]:
        btn = choose_delivery_button(arr[0])
    else:
        btn = choose_delivery_button([])
        
    await bot.send_message(user_id, "Чудово!",reply_markup=types.ReplyKeyboardRemove())
    await bot.send_message(user_id, "Вкажіть бажаний спосіб доставки",reply_markup=btn.as_markup())
    

@user_router.callback_query(lambda c: c.data == 'deliveri_done', state=make_req)
async def user_start(callback_query: types.CallbackQuery, state = FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("SELECT delivery FROM buyers WHERE id = %s",(str(user_id),))
    deliveri = cur.fetchone()
    s = ''.join(deliveri[0])
    await state.update_data(delivers=s)
    await bot.send_message(user_id, "Чудово, вкажіть своє місто",reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(make_req.city)
    
@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.city)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(city=text)
    await bot.send_message(user_id, "Чудово, вкажіть додаткові умові коментарем",reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(make_req.comment)
    
@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.comment)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(comment=text)
    await bot.send_message(user_id, "Чудово, ваше замовлення прийняте",reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    id = randint(1,999999)
    now = datetime.datetime.now()
    valid_time = now + datetime.timedelta(minutes=15)
    cur.execute("INSERT INTO orders (id,buyer_id, name, category,min_max,delivery,city,buyer_com,valid_time) VALUES (%s,%s,%s, %s, %s, %s, %s, %s,%s)",
                (id,str(user_id), data['name'], data['cat'], data['min_max'], data['delivers'],data['city'], data['comment'],valid_time))
    base.commit()
    cur.execute("SELECT rating FROM buyers WHERE id = %s",(str(user_id),))
    rate = cur.fetchone()

    await mailing_sellers(data['name'], data['cat'], data['min_max'],rate,data['comment'],id,data['city'], data['delivers'])
    # TODO: change timer to 900
    await asyncio.sleep(45)
    print('end of await answers from sellers')
    cur.execute('''SELECT sellers,prices,seller_terms,seller_coms
                        FROM orders
                            WHERE id = %s
    ''',(id,))
    order = cur.fetchone()
    if order[0]:
        for i in range(len(order[0])):
            cur.execute("SELECT rating FROM sellers WHERE id = %s",(order[0][i],))
            rate = cur.fetchall()
            btn = accept_order_buyer_btn(str(order[0][i]),str(order[1][i]),str(order[2][i]),str(order[3][i]),id)
            message = f'''
    Рейтинг: {str(rate)}
    Ціна: {str(order[1][i])}
    Додаткові умови: {str(order[2][i])}
    Коментар: {str(order[3][i])}     
            '''
            await bot.send_message(user_id,message,reply_markup=btn.as_markup(resize_keyboard=True))


@user_router.callback_query(SellersCallbackFactory.filter(F.action == "accept_order_buyer"))
async def user_start(callback_query: types.CallbackQuery, callback_data: SellersCallbackFactory, state: FSMContext):
    user_id = callback_query.from_user.id
    seller_id = callback_data.seller_id
    price = callback_data.price
    term = callback_data.term
    com = callback_data.com
    order_id = callback_data.order_id
    print('accept order')
    cur.execute('''SELECT status
                        FROM orders
                            WHERE id = %s
    ''',(order_id,))
    status = cur.fetchone()
    if status[0] == 'in search':
        cur.execute("UPDATE orders SET seller_id = %s, price = %s, seller_term = %s, seller_com = %s,status = 'in progress' WHERE id = %s",(seller_id,price,term,com,order_id))
        base.commit()

        await bot.send_message(user_id,f'Чудово ви обрали продавця\nid замовлення: {order_id}\nДля завершення замовлення введіть команду /end\nОЦІНЮЙТЕ ПРОДАВЦЯ ЛИШЕ ПІСЛЯ ОТРИМАНИХ ПОСЛУГ!')
        cur.execute('''SELECT sellers
                            FROM orders
                                WHERE id = %s
        ''',(order_id,))
        order = cur.fetchone()
        cur.execute('''SELECT phone
                            FROM buyers
                                WHERE id = %s
        ''',(str(user_id),))
        user_phone = cur.fetchone()
        for seller in order[0]:
            if seller != seller_id:
                await bot2.send_message(seller,f'Покупець відхил ваше замовлення\nid замовлення: {order_id}')
            else:
                await bot2.send_message(seller,f'Покупець прийняв ваше\nid замовлення: {order_id}\nНомер телефону покупця: {user_phone[0]}\nДля завершення замовлення введіть команду /end\nОЦІНЮЙТЕ ПОКУПЦЯ ЛИШЕ ПІСЛЯ ОТРИМАНИХ ПОСЛУГ!')
        
@user_router.callback_query(lambda c: c.data == 'nova_pochta')
async def user_start(callback_query: types.CallbackQuery, state = FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s",(str(user_id),))
    arr = cur.fetchone()
    if 'nova_pochta' in arr[0]:
        cur.execute("update buyers set delivery = array_remove(delivery, 'nova_pochta') where id = %s",(str(user_id),))
        base.commit()
    else:
        cur.execute("update buyers set delivery = delivery || ARRAY['nova_pochta'] where id = %s",(str(user_id),))
        base.commit()
    cur.execute("select delivery from buyers where id = %s",(str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text('Вкажіть бажаний спосіб доставки',reply_markup=btn.as_markup(),parse_mode="HTML")

@user_router.callback_query(lambda c: c.data == 'nalp')
async def user_start(callback_query: types.CallbackQuery, state = FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s",(str(user_id),))
    arr = cur.fetchone()
    if 'nalp' in arr[0]:
        cur.execute("update buyers set delivery = array_remove(delivery, 'nalp') where id = %s",(str(user_id),))
        base.commit()
    else:
        cur.execute("update buyers set delivery = delivery || ARRAY['nalp'] where id = %s",(str(user_id),))
        base.commit()
    cur.execute("select delivery from buyers where id = %s",(str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text('Вкажіть бажаний спосіб доставки',reply_markup=btn.as_markup(),parse_mode="HTML")

@user_router.callback_query(lambda c: c.data == 'ukr_pochta')
async def user_start(callback_query: types.CallbackQuery, state = FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s",(str(user_id),))
    arr = cur.fetchone()
    if 'ukr_pochta' in arr[0]:
        cur.execute("update buyers set delivery = array_remove(delivery, 'ukr_pochta') where id = %s",(str(user_id),))
        base.commit()
    else:
        cur.execute("update buyers set delivery = delivery || ARRAY['ukr_pochta'] where id = %s",(str(user_id),))
        base.commit()
    cur.execute("select delivery from buyers where id = %s",(str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text('Вкажіть бажаний спосіб доставки',reply_markup=btn.as_markup(),parse_mode="HTML")

@user_router.message(commands=["end"])
async def user_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await bot.send_message(user_id,f'Введіть id замовлення')
    await state.set_state(end_order.id)
    

@user_router.message_handler(content_types=types.ContentType.TEXT, state=end_order.id)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(id=int(text))
    await bot.send_message(user_id,f'Введіть бал, який буде поставленно продавцю')
    await state.set_state(end_order.rate)


@user_router.message_handler(content_types=types.ContentType.TEXT, state=end_order.rate)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(rate=int(text))
    data = await state.get_data()
    cur.execute("select seller_id from orders where id = %s",(data['id']))
    seller_id = cur.execute()
    cur.execute("update sellers set rating = rating + %s /2 where id = %s",(data['rate'],seller_id[0]))
    base.commit()
    await bot.send_message(user_id,f'Чудово, замовлення закрито')
    await state.clear()