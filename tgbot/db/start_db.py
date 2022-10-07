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
    # cur.execute('''CREATE TABLE IF NOT EXISTS (
        
    #     )''')
    
    
    base.commit()
    cur.close()
    base.close()