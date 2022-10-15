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
            token="5712958832:AAFLsIoReuYVMIvtpBcdXoiXzkslpGg2A-g",
            token2="5622869921:AAGHd7pFRiuP3OilQmWUUfPweoVtyFSomb4",
            admin_ids=(),
            use_redis=False,
        ),
        db=DbConfig(
            host='localhost',
            password='2545',
            user='hotline_user',
            database='hotline',
            db_uri = ''
        ),
        misc=Miscellaneous()
    )
