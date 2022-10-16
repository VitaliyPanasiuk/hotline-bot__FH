from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    db_uri: str


@dataclass
class TgBot:
    token: str
    token2: str
    admin_ids: list[int]
    use_redis: bool


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token="5257942822:AAFqBBqGZs6UJZsF3fJ6fY-f8pCFQelxXRw",
            token2="5411810705:AAFVmiB1l4KbCJ7zI_U-z_hULE9t2fyt9xQ",
            admin_ids=(),
            use_redis=False,
        ),
        db=DbConfig(
            host='localhost',
            password='27052004',
            user='postgres',
            database='hotline',
            db_uri = ''
        ),
        misc=Miscellaneous()
    )
