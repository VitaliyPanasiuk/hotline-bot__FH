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
            host='ec2-34-247-72-29.eu-west-1.compute.amazonaws.com',
            password='19c1ab0ac0a25af3f00e91eeb3444e14386c258d63a3c5aeab688246acae56d7',
            user='upzuewwgtntlzy',
            database='dcgpjdnnh9jcc1',
            db_uri = ''
        ),
        misc=Miscellaneous()
    )
