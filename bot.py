import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage

from tgbot.config import load_config
from tgbot.handlers.admin import admin_router
from tgbot.handlers.user import user_router
from tgbot.handlers.sellers import seller_router
from tgbot.middlewares.config import ConfigMiddleware
from tgbot.db import start_db
from tgbot.services import broadcaster
from tgbot.misc.functions import update_category

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, admin_ids: list[int]):
    await broadcaster.broadcast(bot, admin_ids, "Бот був запущений")


def register_global_middlewares(dp: Dispatcher, config):
    dp.message.outer_middleware(ConfigMiddleware(config))
    dp.callback_query.outer_middleware(ConfigMiddleware(config))


async def main():
    await start_db.postgre_start()
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    config = load_config(".env")

    storage = MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    bot2 = Bot(token=config.tg_bot.token2, parse_mode='HTML')
    dp = Dispatcher(storage=storage)
    dp2 = Dispatcher(storage=storage)

    for router in [
        admin_router,
        user_router,
    ]:
        dp.include_router(router)
    for router in [
        seller_router,
    ]:
        dp2.include_router(router)

    register_global_middlewares(dp, config)
    register_global_middlewares(dp2, config)

    # await on_startup(bot, config.tg_bot.admin_ids)
    # ,update_category()
    await asyncio.gather(dp.start_polling(bot), dp2.start_polling(bot2),update_category())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Бот був вимкнений!")
