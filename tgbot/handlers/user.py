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

from tgbot.misc.states import reg_user, make_req, end_order
from tgbot.misc.functions import auf, mailing_sellers, rating

from tgbot.keyboards.textBtn import choose_cat_button
from tgbot.keyboards.inlineBtn import (
    choose_delivery_button,
    accept_order_buyer_btn,
    homeB_button,
    choose_payment_button,
    end_button,
)
from tgbot.keyboards.inlineBtn import SellersCallbackFactory

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import datetime
import requests
import re
import asyncio


user_router = Router()
config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode="HTML")
bot2 = Bot(token=config.tg_bot.token2, parse_mode="HTML")

base = psycopg2.connect(
    dbname=config.db.database,
    user=config.db.user,
    password=config.db.password,
    host=config.db.host,
)
cur = base.cursor()

headers = {
    "user-agent": "custom/2.22",
    "referer": "https://www.google.com",
    "accept": "text/html",
    "accept-language": "en-US",
    "custom-header-xyz": "hello; charset=utf-8",
}


async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    await message.delete()


@user_router.message(commands=["start"])
async def user_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    auf_user = await auf("buyer", user_id)
    if not auf_user:
        await bot.send_message(user_id, "Привіт!")
        await bot.send_message(user_id, "Відправте своє ім'я")
        await state.set_state(reg_user.name)
    else:
        btn = homeB_button()
        cur.execute("SELECT name FROM buyers WHERE id=%s", (str(user_id),))
        name = cur.fetchone()[0]
        await bot.send_message(user_id, "Привіт, " + name, reply_markup=btn.as_markup())


@user_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.name)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(name=text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await bot.send_message(user_id, "Відправте свій номер телефону")
    await state.set_state(reg_user.phone)


@user_router.message_handler(content_types=types.ContentType.TEXT, state=reg_user.phone)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(phone=text)
    data = await state.get_data()
    cur.execute(
        "INSERT INTO buyers (id, name, phone,delivery,payment,rating) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, data["name"], data["phone"], [], [], []),
    )
    base.commit()
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await bot.send_message(user_id, "Ви зареєстровані")
    btn = homeB_button()
    cur.execute("SELECT name FROM buyers WHERE id=%s", (str(user_id),))
    name = cur.fetchone()[0]
    await bot.send_message(user_id, "Привіт, " + name, reply_markup=btn.as_markup())
    await state.clear()


@user_router.callback_query(lambda c: c.data == "buy")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    await bot.send_message(callback_query.from_user.id, "Введіть назву товару ")
    await state.set_state(make_req.name)


@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.name)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(name=text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)

    arr = text.split(" ")
    url = "https://rozetka.com.ua/search/?text="
    for elem in arr:
        url += elem + "+"

    option = Options()

    option.add_argument("--no-sandbox")
    option.add_argument("--window-size=1420,1080")
    option.add_argument("--headless")
    option.add_argument("--disable-gpu")

    s = Service("/usr/bin/chromedriver")
    # option.binary_location = "C:\Program Files\Google\Chrome\Application\chrome.exe"

    # browser = webdriver.Chrome(service=s, chrome_options=option)
    browser = webdriver.Chrome(
        executable_path="E:\programs\chromedriver_win32\chromedriver.exe",
        chrome_options=option,
    )
    browser.get(url)
    browser.implicitly_wait(1.5)
    try:
        browser.find_element(
            By.CSS_SELECTOR, ".categories-filter__toggle-main>button"
        ).click()
        test = browser.find_elements(By.CSS_SELECTOR, ".categories-filter__toggle")
        for i in test:
            if i.text != "Згорнути":
                i.click()
        categories = []
        products_title = browser.find_elements(
            By.CSS_SELECTOR, ".categories-filter__link-title"
        )
        for i in products_title:
            if i.text != "Всі результати":
                categories.append(i.text)

        btn = choose_cat_button(categories)
        await bot.send_message(
            user_id,
            "Оберіть категорію, що найбільше відповідає запитуваному товару",
            reply_markup=btn.as_markup(resize_keyboard=True),
        )
        await state.set_state(make_req.cat)
    except:
        await bot.send_message(
            user_id,
            "Я не зміг встановити категорію товару, будь ласка, вкажіть бренд товару, а його модель вкажіть в додаткових коментарях",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        await state.set_state(make_req.name)


@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.cat)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(cat=text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)

    await bot.send_message(
        user_id,
        "Чудово, вкажіть додаткові умови коментарем(модель товару, колір, кількість, додаткові побажання тощо)",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(make_req.comment)
    # await bot.send_message(user_id, "Чудово!",reply_markup=types.ReplyKeyboardRemove())
    # await bot.send_message(user_id, "Вкажіть бажаний спосіб доставки (можна обрати декілька)",reply_markup=btn.as_markup())


@user_router.callback_query(lambda c: c.data == "deliveri_done", state=make_req)
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("SELECT delivery FROM buyers WHERE id = %s", (str(user_id),))
    deliveri = cur.fetchone()
    s = ""
    for i in deliveri[0]:
        if i == "nova_pochta":
            s += "Нова Пошта "
        elif i == "nalp":
            s += "САТ "
        elif i == "ukr_pochta":
            s += "Укрпошта "
        elif i == "del":
            s += "Делівері "
        elif i == "mist":
            s += "Міст "
        elif i == "samo":
            s += "Самовивіз "
    await state.update_data(delivers=s)
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id - 1,
    )
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if arr[0]:
        btn = choose_payment_button(arr[0])
    else:
        btn = choose_payment_button([])
    await bot.send_message(
        user_id,
        "Вкажіть бажаний спосіб оплати (можна обрати декілька)",
        reply_markup=btn.as_markup(),
    )


@user_router.callback_query(lambda c: c.data == "nak")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "nak" in arr[0]:
        cur.execute(
            "update buyers set payment = array_remove(payment, 'nak') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set payment = payment || ARRAY['nak'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_payment_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб оплати (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "pred")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "pred" in arr[0]:
        cur.execute(
            "update buyers set payment = array_remove(payment, 'pred') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set payment = payment || ARRAY['pred'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_payment_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб оплати (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "card")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "card" in arr[0]:
        cur.execute(
            "update buyers set payment = array_remove(payment, 'card') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set payment = payment || ARRAY['card'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_payment_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб оплати (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "card_pdv")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "card_pdv" in arr[0]:
        cur.execute(
            "update buyers set payment = array_remove(payment, 'card_pdv') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set payment = payment || ARRAY['card_pdv'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select payment from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_payment_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб оплати (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "payment_done", state=make_req)
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("SELECT payment FROM buyers WHERE id = %s", (str(user_id),))
    payment = cur.fetchone()
    s = ""
    for i in payment[0]:
        if i == "nak":
            s += "Накладений платіж "
        elif i == "pred":
            s += "Передплата на картку "
        elif i == "card":
            s += "Безготівкова без ПДВ "
        elif i == "card_pdv":
            s += "Безготівкова з ПДВ "
    await state.update_data(payment=s)
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
    )
    await bot.send_message(
        user_id, "Чудово, вкажіть своє місто", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(make_req.city)


@user_router.message_handler(content_types=types.ContentType.TEXT, state=make_req.city)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(city=text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    # await bot.send_message(user_id, "Чудово, вкажіть додаткови умові коментарем",reply_markup=types.ReplyKeyboardRemove())
    # await state.set_state(make_req.comment)

    msg = await bot.send_message(
        user_id,
        "Чудово, ваше замовлення прийнято, у кожного із продавців є 10 хвилин для надання цінової та бонусної пропозиції. Зачекайте, будь ласка!",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    asyncio.create_task(delete_message(msg, 120))
    data = await state.get_data()
    id = randint(1, 999999)
    now = datetime.datetime.now()
    valid_time = now + datetime.timedelta(minutes=10)
    cur.execute(
        "INSERT INTO orders (id,buyer_id, name, category,delivery,city,buyer_com,valid_time,payment) VALUES (%s,%s, %s, %s, %s, %s, %s,%s,%s)",
        (
            id,
            str(user_id),
            data["name"],
            data["cat"],
            data["delivers"],
            data["city"],
            data["comment"],
            valid_time,
            data["payment"],
        ),
    )
    base.commit()
    # cur.execute("SELECT rating FROM buyers WHERE id = %s",(str(user_id),))
    # rate = cur.fetchone()[0]
    message = f"""
Товар: {data["name"]}🔴🔴
Коментар: {data["comment"]}
Категорія: {data["cat"]}
Місто: {data["city"]}
Доставка: {data["delivers"]}
Спосіб оплати: {data["payment"]}
        """
    btn = homeB_button()
    mesg = await bot.send_message(user_id, message, reply_markup=btn.as_markup())
    cur.execute("Update orders SET msg_b = %s WHERE id=%s", (str(mesg.message_id), id))
    cur.execute("Update orders SET chat_b = %s WHERE id=%s", (str(mesg.chat.id), id))
    base.commit()
    # asyncio.create_task(delete_message(mesg, 15))
    buyer_rating = await rating("get", "buyer", user_id, 0)

    await mailing_sellers(
        data["name"],
        data["cat"],
        buyer_rating,
        data["comment"],
        id,
        data["city"],
        data["delivers"],
    )
    # TODO: change timer to 600
    await asyncio.sleep(600)
    print("end of await answers from sellers")
    # await bot.delete_message(chat_id = message.chat.id ,message_id = message.message_id + 1)
    cur.execute(
        """SELECT sellers,prices,seller_terms,seller_coms,category,buyer_com,name
                        FROM orders
                            WHERE id = %s
    """,
        (id,),
    )
    order = cur.fetchone()
    # print(order)
    if order and order[0]:
        for i in range(len(order[0])):
            cur.execute("SELECT name FROM sellers WHERE id = %s", (str(order[0][i]),))
            name = cur.fetchone()[0]
            seller_rating = await rating("get", "seller", str(order[0][i]), 0)
            # seller_id,order_price,order_term,order_com,order_id
            btn = accept_order_buyer_btn(
                str(order[0][i]),
                # str(order[1][i]),
                # str(order[2][i]),
                # str(order[3][i]),
                id,
            )
            message = f"""
Продавець: {name} 
Товар: {str(order[6])}
Коментар: {str(order[5])}
Категорія: {str(order[4])}
Рейтинг: {str(seller_rating)}
Ціна: {str(order[1][i])}
Додаткові умови: {str(order[2][i])}
Коментар: {str(order[3][i])}     
            """
            await bot.send_message(
                user_id, message, reply_markup=btn.as_markup(resize_keyboard=True)
            )
    else:
        mesg = await bot.send_message(
            user_id,
            "На жаль, жоден із продавців не надав цінової пропозиціїї на ваш запит. Спробуйте пізніше , або змініть критерії пошуку.",
        )
        asyncio.create_task(delete_message(mesg, 120))


@user_router.message_handler(
    content_types=types.ContentType.TEXT, state=make_req.comment
)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    await state.update_data(comment=text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if arr[0]:
        btn = choose_delivery_button(arr[0])
    else:
        btn = choose_delivery_button([])
    await bot.send_message(user_id, "Чудово!", reply_markup=types.ReplyKeyboardRemove())
    await bot.send_message(
        user_id,
        "Вкажіть бажаний спосіб доставки (можна обрати декілька)",
        reply_markup=btn.as_markup(),
    )


@user_router.callback_query(
    SellersCallbackFactory.filter(F.action == "accept_order_buyer")
)
async def user_start(
    callback_query: types.CallbackQuery,
    callback_data: SellersCallbackFactory,
    state: FSMContext,
):
    user_id = callback_query.from_user.id
    seller_id = callback_data.seller_id
    # price = callback_data.price
    # term = callback_data.term
    # com = callback_data.com
    order_id = callback_data.order_id
    await callback_query.message.delete()
    print("accept order")
    cur.execute(
        """SELECT sellers,prices,seller_terms,seller_coms
                        FROM orders
                            WHERE id = %s
    """,
        (order_id,),
    )
    order = cur.fetchone()
    # if order[0]:
    #     for i in range(len(order[0])):
    #         await bot.delete_message(chat_id = callback_query.message.chat.id ,message_id = callback_query.message.message_id - i)

    cur.execute(
        """SELECT status,name,category,buyer_com,delivery,payment,st_b,st_s
                        FROM orders
                            WHERE id = %s
    """,
        (order_id,),
    )
    status = cur.fetchone()
    if status[0] == "in search":
        cur.execute(
            "SELECT sellers,prices,seller_terms,seller_coms FROM orders WHERE id = %s",
            (order_id,),
        )
        n = cur.fetchone()

        cur.execute(
            "UPDATE orders SET seller_id = %s, price = %s, seller_term = %s, seller_com = %s,status = 'in progress' WHERE id = %s",
            (
                seller_id,
                n[1][n[0].index(seller_id)],
                n[2][n[0].index(seller_id)],
                n[3][n[0].index(seller_id)],
                order_id,
            ),
        )
        base.commit()
        cur.execute(
            """SELECT phone,name
                                FROM sellers
                                    WHERE id = %s
            """,
            (seller_id,),
        )
        phom = cur.fetchone()
        cur.execute(
            """SELECT chat_b,msg_b
                                FROM orders
                                    WHERE id = %s
            """,
            (order_id,),
        )
        last_mess = cur.fetchone()

        await bot.delete_message(chat_id=last_mess[0], message_id=last_mess[1])
        btn = end_button(order_id)
        test = await bot.send_message(
            user_id,
            f"""Чудово ви обрали продавця, {phom[1]}
id замовлення: `{order_id}`{"🟢🟢" if status[7] else "🟢🔴"}
Товар: {status[1]}
Телефон продавця: `{str(phom[0])}`
Категорія: {status[2]}
Доставка: {status[4]}
Спосіб оплати: {status[5]}
Коментар: {status[3]}
""",
            reply_markup=btn.as_markup(),
            parse_mode="Markdown",
        )
        cur.execute(
            "Update orders SET msg_b = %s WHERE id=%s", (str(test.message_id), order_id)
        )
        cur.execute(
            "Update orders SET chat_b = %s WHERE id=%s", (str(test.chat.id), order_id)
        )
        base.commit()
        # btn = homeB_button()
        # await bot.send_message(user_id, "Привіт, "+ callback_query.from_user.first_name,reply_markup=btn.as_markup())
        cur.execute(
            """SELECT sellers
                            FROM orders
                                WHERE id = %s
        """,
            (order_id,),
        )
        order = cur.fetchone()
        cur.execute(
            """SELECT phone,name
                            FROM buyers
                                WHERE id = %s
        """,
            (str(user_id),),
        )
        user_phone = cur.fetchone()
        for seller in order[0]:
            if seller != seller_id:
                await bot2.send_message(
                    seller,
                    f"""Покупець відхилив ваше замовлення 
id замовлення: `{order_id}` 🔴🔴
Номер телефону покупця: `{user_phone[0]}`
Ім'я покупця: {user_phone[1]}
Товар: {status[1]}
Категорія: {status[2]}
Коментар: {status[3]}
""",
                    reply_markup=btn.as_markup(),
                    parse_mode="Markdown",
                )
            else:
                btn = end_button(order_id)
                test = await bot2.send_message(
                    seller,
                    f"""Покупець прийняв ваше замовлення
id замовлення: `{order_id}` {"🟢🟢" if status[6] else "🟢🔴"}
Номер телефону покупця: `{user_phone[0]}`
Ім'я покупця: {user_phone[1]}
Товар: {status[1]}
Категорія: {status[2]}
Коментар: {status[3]}
""",
                    reply_markup=btn.as_markup(),
                    parse_mode="Markdown",
                )
                cur.execute(
                    "Update orders SET msg_s = %s WHERE id=%s",
                    (str(test.message_id), order_id),
                )
                cur.execute(
                    "Update orders SET chat_s = %s WHERE id=%s",
                    (str(test.chat.id), order_id),
                )
                base.commit()


@user_router.callback_query(lambda c: c.data == "nova_pochta")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "nova_pochta" in arr[0]:
        cur.execute(
            "update buyers set delivery = array_remove(delivery, 'nova_pochta') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set delivery = delivery || ARRAY['nova_pochta'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб доставки (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "nalp")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "nalp" in arr[0]:
        cur.execute(
            "update buyers set delivery = array_remove(delivery, 'nalp') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set delivery = delivery || ARRAY['nalp'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб доставки (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "ukr_pochta")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "ukr_pochta" in arr[0]:
        cur.execute(
            "update buyers set delivery = array_remove(delivery, 'ukr_pochta') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set delivery = delivery || ARRAY['ukr_pochta'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб доставки (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "del")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "del" in arr[0]:
        cur.execute(
            "update buyers set delivery = array_remove(delivery, 'del') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set delivery = delivery || ARRAY['del'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб доставки (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "mist")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "mist" in arr[0]:
        cur.execute(
            "update buyers set delivery = array_remove(delivery, 'mist') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set delivery = delivery || ARRAY['mist'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб доставки (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(lambda c: c.data == "samo")
async def user_start(callback_query: types.CallbackQuery, state=FSMContext):
    user_id = callback_query.from_user.id
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    if "samo" in arr[0]:
        cur.execute(
            "update buyers set delivery = array_remove(delivery, 'samo') where id = %s",
            (str(user_id),),
        )
        base.commit()
    else:
        cur.execute(
            "update buyers set delivery = delivery || ARRAY['samo'] where id = %s",
            (str(user_id),),
        )
        base.commit()
    cur.execute("select delivery from buyers where id = %s", (str(user_id),))
    arr = cur.fetchone()
    btn = choose_delivery_button(arr[0])
    await callback_query.message.edit_text(
        "Вкажіть бажаний спосіб доставки (можна обрати декілька)",
        reply_markup=btn.as_markup(),
        parse_mode="HTML",
    )


@user_router.callback_query(SellersCallbackFactory.filter(F.action == "end_order"))
async def user_start(
    callback_query: types.CallbackQuery,
    callback_data: SellersCallbackFactory,
    state: FSMContext,
):
    user_id = callback_query.from_user.id
    order_id = callback_data.order_id
    # await callback_query.message.delete()
    await state.update_data(id=int(order_id))
    await bot.send_message(
        user_id, f"Введіть бал, що буде поставленно продавцю(від 1 до 10)"
    )
    await state.set_state(end_order.rate)


@user_router.message_handler(content_types=types.ContentType.TEXT, state=end_order.rate)
async def test_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    
    await state.update_data(rate=int(text))
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    data = await state.get_data()
    cur.execute("select seller_id from orders where id = %s", (data["id"],))
    seller_id = cur.fetchone()[0]
    # cur.execute("update sellers set rating = rating + %s /2 where id = %s",(data['rate'],seller_id[0]))
    # base.commit()
    await rating("update", "seller", seller_id, data["rate"])
    btn = homeB_button()
    # await bot.send_message(user_id, "Привіт, "+ message.from_user.first_name,reply_markup=btn.as_markup())
    msg = await bot.send_message(user_id, f"Чудово, замовлення закрито")
    asyncio.create_task(delete_message(msg, 5))
    cur.execute("UPDATE orders SET st_b = True WHERE id = %s", (data["id"],))
    base.commit()
    cur.execute(
        """SELECT status,name,category,buyer_com,delivery,payment,st_b,st_s
                        FROM orders
                            WHERE id = %s
    """,
        (data["id"],),
    )
    status = cur.fetchone()
    cur.execute(
        """SELECT phone,name
                            FROM buyers
                                WHERE id = %s
        """,
        (str(user_id),),
    )
    user_phone = cur.fetchone()
    cur.execute("SELECT chat_s,msg_s FROM orders WHERE id = %s", (data["id"],))
    msg = cur.fetchone()
    cur.execute('''SELECT st_s from orders where id = %s''',(data['id'],))
    st_s = cur.fetchone()
    btn = end_button(data["id"])
    print('st_s',st_s[0])
    if st_s[0] == True:
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
id замовлення: `{data['id']}` 🟢🟢
Номер телефону покупця: `{user_phone[0]}`
Ім'я покупця: {user_phone[1]}
Товар: {status[1]}
Категорія: {status[2]}
Коментар: {status[3]}
    """,
            reply_markup=btn.as_markup(),
            parse_mode="Markdown",
        )
        
    # radact buyer message
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
    print(st_s)
    if st_s[0] == True:
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
id замовлення: `{data['id']}` 🟢🔴
Товар: {status[1]}
Телефон продавця: `{str(phom[0])}`
Категорія: {status[2]}
Доставка: {status[4]}
Спосіб оплати: {status[5]}
Коментар: {status[3]}''',
            parse_mode='Markdown')
    await state.clear()
