import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs
from tgbot.config import load_config

config = load_config(".env")


async def postgre_start():
    base = psycopg2.connect(
        dbname=config.db.database,
        user=config.db.user,
        password=config.db.password,
        host=config.db.host,
    )
    cur = base.cursor()
    if base:
        print("data base connect Ok!")
    cur.execute(
        """create table if not exists buyers
(
    id       text not null,
    name     text,
    rating   integer[],
    phone    text,
    delivery text[],
    payment  text[]
);

create table if not exists sellers
(
    id           text not null,
    name         text,
    org_form     text,
    category     text[],
    email        text,
    phone        text,
    rating       integer[],
    person_phone text,
    constraint sellers_pk
        primary key (id)
);

create table if not exists orders
(
    id           integer not null,
    buyer_id     text,
    seller_id    text,
    price        text,
    seller_term  text,
    seller_com   text,
    sellers      text[],
    prices       text[],
    seller_terms text[],
    seller_coms  text[],
    name         text,
    category     text,
    min_max      text,
    delivery     text,
    payment      text,
    city         text,
    buyer_com    text,
    status       text    default 'in search'::text,
    st_b         boolean default false,
    st_s         boolean default false,
    valid_time   timestamp,
    msg_b        text,
    msg_s        text,
    chat_b       text,
    chat_s       text,
    chat_from_s  text,
    mes_from_s   text[],
    primary key (id)
);"""
    )

    base.commit()
    cur.close()
    base.close()
