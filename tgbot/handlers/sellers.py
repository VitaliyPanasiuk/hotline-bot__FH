from aiogram import Router, Bot, types
from aiogram.types import Message, FSInputFile
from magic_filter import F
from tgbot.config import load_config
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup
# from aiogram.exceptions import MessageError
# from aiogram.utils import (MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted,
#                                       MessageToDeleteNotFound)

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs

from tgbot.misc.states import reg_user,make_req,accept_ord,end_order
from tgbot.misc.functions import auf,rating

from tgbot.keyboards.textBtn import choose_cat_button,choose_action
from tgbot.keyboards.inlineBtn import choose_delivery_button,end_button
from tgbot.keyboards.inlineBtn import SellersCallbackFactory

import datetime
import requests
from bs4 import BeautifulSoup
import re
import asyncio
from contextlib import suppress


seller_router = Router()
config = load_config(".env")
bot2 = Bot(token=config.tg_bot.token2, parse_mode='HTML')
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')

base = psycopg2.connect(dbname=config.db.database, user=config.db.user, password=config.db.password,host=config.db.host)
cur = base.cursor()

async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    # with suppress(MessageError):
    await message.delete()


@seller_router.message(commands=["start"])
async def user_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    auf_user = await auf("seller", user_id)
    if not auf_user:
        await bot2.send_message(user_id, "Привіт!")
        await bot2.send_message(user_id, "Відправте своє ім'я або назву компанії")
        await state.set_state(reg_user.name)
    else:
        # btn = homeS_button()
        # await bot2.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())
        cur.execute("SELECT name FROM sellers WHERE id=%s",(str(user_id),))
        name = cur.fetchone()[0]
        await bot2.send_message(user_id, "Привіт, "+ name)


@seller_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.name)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(name=text)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id - 1 )
    await bot2.send_message(user_id, "Відправте свій email")
    await state.set_state(reg_user.email)

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.email)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(email=text)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id - 1 )
    await bot2.send_message(user_id, "Відправте свій номер телефону, що зареєстрований у Телеграм та буде використовуватися для обслуговування клієнтів")
    await state.set_state(reg_user.phone)


@seller_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.phone)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(phone=text)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id - 1 )
    await bot2.send_message(user_id, "Вкажіть організаційно-правову форму (фізична особа, ФОП, юридична особа)")
    await state.set_state(reg_user.org)
    


@seller_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.org)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(org=text)
    data = await state.get_data()
    cur.execute("INSERT INTO sellers (id, name, phone,org_form,email,rating) VALUES (%s,%s,%s, %s, %s, %s)",
                (user_id, data['name'], data['phone'], data['org'], data['email'],[]))
    base.commit()
    await bot2.send_message(user_id, "Ви зареєстровані")
    await bot2.send_message(user_id, "Будь ласка, заповніть анкету та укажіть в ній усі цільові категорії товарів\послуг , що ви продаєте\надаєте!\nВкажіть email, котрий ви вказували при регістрації у боті\nhttps://forms.gle/XEUxayAXtrMK7xEe8")
    # btn = homeS_button()
    # await bot2.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())


@seller_router.callback_query(SellersCallbackFactory.filter(F.action == "accept_order"))
async def user_start(callback_query: types.CallbackQuery, callback_data: SellersCallbackFactory, state: FSMContext):
    user_id = callback_query.from_user.id
    order_id = callback_data.order_id
    await callback_query.message.delete()
    now = datetime.datetime.now()
    cur.execute("SELECT valid_time FROM orders WHERE id = %s",(int(order_id),))
    valid_time = cur.fetchone()
    print(valid_time)
    if now > valid_time[0]:
        msg = await bot2.send_message(user_id,"Час на відповідь вичерпано")
        asyncio.create_task(delete_message(msg, 5))
    else:
        await state.update_data(id=order_id)
        await state.update_data(seller_id=user_id)
        await bot2.send_message(user_id, "Введіть ціну")
        await state.set_state(accept_ord.price)
        
@seller_router.callback_query(SellersCallbackFactory.filter(F.action == "delete_order"))
async def user_start(callback_query: types.CallbackQuery, callback_data: SellersCallbackFactory, state: FSMContext):
    user_id = callback_query.from_user.id
    order_id = callback_data.order_id
    await callback_query.message.delete()

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=accept_ord.price)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(price=text)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id - 1 )
    await bot2.send_message(user_id, "Введіть додаткові умови")
    await state.set_state(accept_ord.terms)

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=accept_ord.terms)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(terms=text)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id - 1 )
    await bot2.send_message(user_id, "Введіть коментар")
    await state.set_state(accept_ord.comment)

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=accept_ord.comment)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(comment=text)
    data = await state.get_data()
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id - 1 )
    
    cur.execute("UPDATE orders SET sellers = sellers || ARRAY[%s], prices = prices || ARRAY[%s], seller_terms = seller_terms || ARRAY[%s], seller_coms = seller_coms || ARRAY[%s] WHERE id = %s",(str(data['seller_id']),str(data['price']),data['terms'],data['comment'],data['id']))
    base.commit()
    # btn = homeS_button()
    # await bot2.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())
    msg = await bot2.send_message(user_id,"Ваша заявка прийнята")
    asyncio.create_task(delete_message(msg, 120))
    await state.clear()


@seller_router.callback_query(SellersCallbackFactory.filter(F.action == "end_order"))
async def user_start(callback_query: types.CallbackQuery, callback_data: SellersCallbackFactory, state: FSMContext):
    user_id = callback_query.from_user.id
    order_id = callback_data.order_id
    # await callback_query.message.delete()
    await state.update_data(id=int(order_id))
    btn = choose_action()
    await bot2.send_message(user_id,f'Оберіть дію',reply_markup=btn.as_markup(resize_keyboard=True))
    await state.set_state(end_order.action)


@seller_router.message_handler(content_types=types.ContentType.TEXT, state=end_order.action)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    data = await state.get_data()
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id - 1 )
    # btn = homeS_button()
    if text == 'Підтвердити виконання':
        await bot2.send_message(user_id,f'Введіть бал, що буде поставленно покупцю(від 1 до 10)',reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(end_order.rate)
    # elif text == 'Скарга':
    #     cur.execute("select buyer_id from orders where id = %s",(data['id'],))
    #     buyer_id = cur.fetchone()
    #     cur.execute("update buyers set rating = rating - 1 where id = %s",(buyer_id[0],))
    #     base.commit()
    #     # await bot2.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())
        
    #     msg = await bot2.send_message(user_id,"Скаргу було надіслано")
    #     asyncio.create_task(delete_message(msg, 5))
    elif text == 'Відмінити замовлення':
        # await bot2.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())
        msg = await bot2.send_message(user_id,"Замовлення було відмінено")
        asyncio.create_task(delete_message(msg, 15))
        cur.execute('''SELECT status,name,category,buyer_com,delivery,payment,st_b,st_s
                        FROM orders
                            WHERE id = %s
    ''',(data['id'],))
        status = cur.fetchone()
        cur.execute("SELECT chat_b,msg_b FROM orders WHERE id = %s",(data['id'],))
        msg = cur.fetchone()
        cur.execute('''SELECT phone,name
                                    FROM sellers
                                        WHERE id = %s
                ''',(str(user_id),))
        phom = cur.fetchone()
        btn = end_button(data['id'])
        await bot.edit_message_text(chat_id = msg[0] ,message_id=msg[1],text = f'''Продавець відхилив ваше замовлення, {phom[1]}
id замовлення: `{data['id']}` 🔴🔴
Товар: {status[1]}
Телефон продавця: `{str(phom[0])}`
Категорія: {status[2]}
Доставка: {status[4]}
Спосіб оплати: {status[5]}
Коментар: {status[3]}''',parse_mode='Markdown')
        
        cur.execute(
        """SELECT status,name,category,buyer_com,delivery,payment,st_b,st_s
                        FROM orders
                            WHERE id = %s
    """,
        (data["id"],),
    )
    status = cur.fetchone()
    cur.execute('SELECT buyer_id from orders where id = %s',(data['id'],))
    buyer_id = cur.fetchone()
    print(buyer_id)
    cur.execute("""SELECT phone,name
                            FROM buyers
                                WHERE id = %s """,(str(buyer_id[0]),))
    user_phone = cur.fetchone()
    print(user_phone)
    
    cur.execute("SELECT chat_s,msg_s FROM orders WHERE id = %s", (data["id"],))
    msg = cur.fetchone()
    btn = end_button(data["id"])
    await bot2.edit_message_text(
        chat_id=msg[0],
        message_id=msg[1],
        text=f"""Ви відхилили замовлення
id замовлення: `{data['id']}` 🔴🔴
Номер телефону покупця: `{user_phone[0]}`
Ім'я покупця: {user_phone[1]}
Товар: {status[1]}
Категорія: {status[2]}
Коментар: {status[3]}
    """,
            parse_mode="Markdown",
        )
        
    await state.clear()
        

@seller_router.message_handler(content_types=types.ContentType.TEXT, state=end_order.rate)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    # btn = homeS_button()
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id)
    await bot2.delete_message(chat_id = message.chat.id ,message_id = message.message_id - 1 )
    await state.update_data(rate=int(text))
    data = await state.get_data()
    cur.execute("select buyer_id from orders where id = %s",(data['id'],))
    buyer_id = cur.fetchone()[0]
    cur.execute("UPDATE orders SET st_s = True WHERE id = %s",(data['id'],))
    base.commit()
    await rating('update','buyer',buyer_id,data['rate'])
    
    # await bot.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())
    msg = await bot2.send_message(user_id,f'Чудово, замовлення закрито')
    asyncio.create_task(delete_message(msg, 5))
    cur.execute("UPDATE orders SET st_s = True WHERE id = %s",(data['id'],))
    base.commit()
    cur.execute('''SELECT status,name,category,buyer_com,delivery,payment,st_b,st_s
                        FROM orders
                            WHERE id = %s
    ''',(data['id'],))
    status = cur.fetchone()
    cur.execute("SELECT chat_b,msg_b FROM orders WHERE id = %s",(data['id'],))
    msg = cur.fetchone()
    cur.execute('''SELECT phone,name
                                FROM sellers
                                    WHERE id = %s
            ''',(str(user_id),))
    phom = cur.fetchone()
    cur.execute('''SELECT st_b from orders where id = %s''',(data['id'],))
    st_b = cur.fetchone()
    btn = end_button(data['id'])
    print('st_b',st_b[0])
    if st_b[0] == True:
        await bot.edit_message_text(
            chat_id = msg[0] ,
            message_id=msg[1],
            text = f'''Чудово ви обрали продавця, {phom[1]}
id замовлення: `{data['id']}` 🟢🟢
Товар: {status[1]}
Телефон продавця: `{str(phom[0])}`
Категорія: {status[2]}
Доставка: {status[4]}
Спосіб оплати: {status[5]}
Коментар: {status[3]}''',
            parse_mode='Markdown')
    else:
        await bot.edit_message_text(
        chat_id = msg[0] ,
        message_id=msg[1],
        text = f'''Чудово ви обрали продавця, {phom[1]}
id замовлення: `{data['id']}` 🟢🟢
Товар: {status[1]}
Телефон продавця: `{str(phom[0])}`
Категорія: {status[2]}
Доставка: {status[4]}
Спосіб оплати: {status[5]}
Коментар: {status[3]}''',
        reply_markup=btn.as_markup(),
        parse_mode='Markdown')
    
    cur.execute(
        """SELECT status,name,category,buyer_com,delivery,payment,st_b,st_s
                        FROM orders
                            WHERE id = %s
    """,
        (data["id"],),
    )
    status = cur.fetchone()
    cur.execute('SELECT buyer_id from orders where id = %s',(data['id'],))
    buyer_id = cur.fetchone()
    print(buyer_id)
    cur.execute("""SELECT phone,name
                            FROM buyers
                                WHERE id = %s """,(str(buyer_id[0]),))
    user_phone = cur.fetchone()
    print(user_phone)
    
    cur.execute("SELECT chat_s,msg_s FROM orders WHERE id = %s", (data["id"],))
    msg = cur.fetchone()
    btn = end_button(data["id"])
    if st_b[0] == True:
        await bot2.edit_message_text(
            chat_id=msg[0],
            message_id=msg[1],
            text=f"""Покупець прийняв ваше замовлення
id замовлення: `{data['id']}` 🟢🟢
Номер телефону покупця: `{user_phone[0]}`
Ім'я покупця: {user_phone[1]}
Товар: {status[1]}
Категорія: {status[2]}
Коментар: {status[3]}
    """,
            parse_mode="Markdown",
        )
    else:
        await bot2.edit_message_text(
            chat_id=msg[0],
            message_id=msg[1],
            text=f"""Покупець прийняв ваше замовлення
id замовлення: `{data['id']}` 🟢🔴
Номер телефону покупця: `{user_phone[0]}`
Ім'я покупця: {user_phone[1]}
Товар: {status[1]}
Категорія: {status[2]}
Коментар: {status[3]}
    """,
            parse_mode="Markdown",
        )
    await state.clear()
    





