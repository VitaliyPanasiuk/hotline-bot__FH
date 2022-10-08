import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs
from tgbot.config import load_config

config = load_config(".env")

async def postgre_start():
    base = psycopg2.connect(dbname=config.db.database, user=config.db.user, password=config.db.password,host=config.db.host)
    cur = base.cursor()
    if base:
        print('data base connect Ok!')
    cur.execute('''CREATE table if not exists buyers
(
    id       text not null
        constraint testtable_pk
            primary key,
    name     text,
    rating   integer default 0,
    phone    text,
    delivery text[]
);

create table if not exists sellers
(
    id           text not null
        constraint sellers_pk
            primary key,
    name         text,
    org_form     text,
    category     text,
    phone        text,
    rating       integer default 0,
    person_phone text
);

)''')
    
    
    base.commit()
    cur.close()
    base.close()